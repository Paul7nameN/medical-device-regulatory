from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.regulatory.log_parser import parse_raw_logs
from app.models.logs import LogEntry
from app.database import get_async_db
from app.services.persistence import PersistenceService, _map_log_type_to_db_enum
from app.models.orm import LogEntry as LogEntryORM
from app.models.enums import AuditAction

router = APIRouter()


class IngestRequest(BaseModel):
    raw_logs: List[str]
    device_id: Optional[str] = None


class IngestResponse(BaseModel):
    ingested: int
    normalized: int
    warnings: List[str]
    sample_entries: List[dict]
    saved_to_db: bool = False


class LogEntryListItem(BaseModel):
    id: str
    device_name: Optional[str]
    timestamp: str
    log_type: str
    raw_log_type: Optional[str]
    source: Optional[str]
    raw_value: Optional[str]


class LogListResponse(BaseModel):
    items: List[LogEntryListItem]
    total: int
    limit: int
    offset: int


def _orm_log_to_list_item(log_entry: LogEntryORM) -> dict:
    payload = log_entry.payload or {}
    device_name = log_entry.device.name if log_entry.device else None
    return {
        "id": str(log_entry.id),
        "device_name": device_name,
        "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
        "log_type": log_entry.log_type.value if hasattr(log_entry.log_type, 'value') else str(log_entry.log_type),
        "raw_log_type": payload.get("raw_log_type"),
        "source": log_entry.source,
        "raw_value": payload.get("raw_value"),
    }


async def _save_entries_to_db(
    db: AsyncSession,
    entries: List[LogEntry],
    device_id: Optional[str],
):
    persistence = PersistenceService(db)
    device = await persistence.get_or_create_device(device_id or "unknown")
    
    log_entries: List[LogEntryORM] = []
    for log_model in entries:
        raw_log_type = log_model.log_type.value
        db_log_type = _map_log_type_to_db_enum(raw_log_type)
        
        log_orm = LogEntryORM(
            device_id=device.id,
            timestamp=log_model.timestamp,
            log_type=db_log_type,
            source=log_model.sensor_id or "log_parser",
            payload={
                "raw_log_type": raw_log_type,
                "raw_value": log_model.raw_value,
                "parsed_value": log_model.parsed_value,
                "metadata": log_model.metadata,
            },
        )
        log_entries.append(log_orm)
    
    db.add_all(log_entries)
    await db.commit()
    
    await persistence.log_audit(
        action=AuditAction.CREATE,
        actor="system",
        resource_type="log_entry",
        resource_id=None,
        description=f"Ingested {len(entries)} log entries for device {device_id or 'unknown'}",
        new_value={
            "device_id": device_id,
            "count": len(entries),
        },
    )
    
    return len(log_entries)


@router.post("/logs/ingest", response_model=IngestResponse)
async def ingest_logs(
    request: IngestRequest,
    db: AsyncSession = Depends(get_async_db),
):
    entries, warnings = parse_raw_logs(request.raw_logs)

    sample_entries = []
    for entry in entries[:5]:
        sample_entries.append({
            "timestamp": entry.timestamp.isoformat(),
            "log_type": entry.log_type.value,
            "raw_value": entry.raw_value,
            "parsed_value": entry.parsed_value,
            "sensor_id": entry.sensor_id
        })

    saved_to_db = False
    if entries:
        try:
            await _save_entries_to_db(db, entries, request.device_id)
            saved_to_db = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to save log entries to DB: {e}")

    return IngestResponse(
        ingested=len(request.raw_logs),
        normalized=len(entries),
        warnings=warnings,
        sample_entries=sample_entries,
        saved_to_db=saved_to_db,
    )


@router.post("/logs/ingest/file", response_model=IngestResponse)
async def ingest_logs_from_file(
    file: UploadFile = File(...),
    device_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        content = await file.read()
        lines = content.decode('utf-8').splitlines()

        entries, warnings = parse_raw_logs(lines)

        sample_entries = []
        for entry in entries[:5]:
            sample_entries.append({
                "timestamp": entry.timestamp.isoformat(),
                "log_type": entry.log_type.value,
                "raw_value": entry.raw_value,
                "parsed_value": entry.parsed_value,
                "sensor_id": entry.sensor_id
            })

        saved_to_db = False
        if entries:
            try:
                await _save_entries_to_db(db, entries, device_id)
                saved_to_db = True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to save log entries to DB: {e}")

        return IngestResponse(
            ingested=len(lines),
            normalized=len(entries),
            warnings=warnings,
            sample_entries=sample_entries,
            saved_to_db=saved_to_db,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/logs", response_model=LogListResponse)
async def list_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    device_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    persistence = PersistenceService(db)
    
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    logs, total = await persistence.get_logs(
        device_id=device_id,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset,
    )
    
    items = [_orm_log_to_list_item(log) for log in logs]
    
    return LogListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )

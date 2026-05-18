from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.regulatory.rules.base import RuleRegistry
from app.config import settings
from app.database import get_async_db

router = APIRouter()


@router.get("/health")
async def health_check():
    rules = RuleRegistry.get_all()
    categories = RuleRegistry.get_categories()

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "rules_loaded": len(rules),
        "categories": categories,
        "debug": settings.debug
    }


@router.get("/health/db")
async def db_health_check(
    db: AsyncSession = Depends(get_async_db),
):
    try:
        result = await db.execute(text("SELECT 1 as ping"))
        ping = result.scalar_one_or_none()
        
        from app.models.orm import Device, AnalysisSession, ComplianceReport
        from sqlalchemy import select, func
        
        device_count_result = await db.execute(select(func.count()).select_from(Device))
        device_count = device_count_result.scalar()
        
        session_count_result = await db.execute(select(func.count()).select_from(AnalysisSession))
        session_count = session_count_result.scalar()
        
        report_count_result = await db.execute(select(func.count()).select_from(ComplianceReport))
        report_count = report_count_result.scalar()
        
        return {
            "status": "connected",
            "ping": ping,
            "stats": {
                "devices": device_count,
                "analysis_sessions": session_count,
                "compliance_reports": report_count,
            }
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e),
        }


@router.get("/health/rules")
async def list_rules():
    rules = RuleRegistry.get_all()

    return {
        "total": len(rules),
        "rules": [
            {
                "rule_id": r.rule_id,
                "description": r.description,
                "category": r.category,
                "default_severity": r.default_severity.value,
                "data_source": r.data_source.value,
                "confidence": r.confidence,
                "inspection_hint": r.inspection_hint
            }
            for r in rules
        ]
    }


@router.get("/health/categories")
async def list_categories():
    categories = RuleRegistry.get_categories()
    result = {}

    for category in categories:
        rules = RuleRegistry.get_by_category(category)
        result[category] = {
            "count": len(rules),
            "rules": [r.rule_id for r in rules]
        }

    return result

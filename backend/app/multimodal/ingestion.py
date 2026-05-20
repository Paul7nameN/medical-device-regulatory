from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import logging

from app.models.logs import LogEntry
from app.models.multimodal import (
    SourceFile,
    SourceFileType,
    ChartAlignment,
)
from app.regulatory.log_parser.log_parser import LogParser, ParseResult

logger = logging.getLogger(__name__)


class IngestionResult:
    def __init__(
        self,
        merged_entries: List[LogEntry],
        sources: List[SourceFile],
        dedup_stats: Dict[str, Any],
        warnings: List[str],
        errors: List[str],
    ):
        self.merged_entries = merged_entries
        self.sources = sources
        self.dedup_stats = dedup_stats
        self.warnings = warnings
        self.errors = errors
        self.success = len(errors) == 0


class MultiModalIngestionService:
    def __init__(self):
        self.log_parser = LogParser()
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def ingest_log_files(
        self,
        file_contents: Dict[str, List[str]],
        file_names: Optional[Dict[str, str]] = None,
    ) -> IngestionResult:
        """
        Ingest multiple log files, merge them, sort by timestamp, and deduplicate.
        
        Args:
            file_contents: Dict mapping file_id to list of log lines
            file_names: Optional dict mapping file_id to original filename
        
        Returns:
            IngestionResult with merged entries, sources, and stats
        """
        self.warnings = []
        self.errors = []
        all_entries: List[Tuple[LogEntry, str]] = []
        sources: List[SourceFile] = []
        file_names = file_names or {}

        total_entries_before = 0

        for file_id, lines in file_contents.items():
            filename = file_names.get(file_id, file_id)
            
            result = self.log_parser.parse_lines(lines)
            
            for entry in result.entries:
                all_entries.append((entry, file_id))
            
            total_entries_before += len(result.entries)
            
            time_range_start, time_range_end = self._get_time_range(result.entries)
            
            sources.append(SourceFile(
                id=file_id,
                name=filename,
                type=SourceFileType.LOG_FILE,
                entry_count=len(result.entries),
                time_range_start=time_range_start,
                time_range_end=time_range_end,
            ))
            
            self.warnings.extend([f"[{filename}] {w}" for w in result.warnings])
            self.errors.extend([f"[{filename}] {e}" for e in result.errors])

        sorted_entries = sorted(all_entries, key=lambda x: x[0].timestamp)
        
        deduped_entries, dedup_count = self.dedupe_log_entries(
            [e[0] for e in sorted_entries]
        )

        dedup_stats = {
            "total_entries_before_merge": total_entries_before,
            "total_entries_after_merge": len(sorted_entries),
            "total_entries_after_dedup": len(deduped_entries),
            "duplicates_removed": dedup_count,
        }

        self.warnings.append(
            f"Merged {len(file_contents)} files: {total_entries_before} entries → {len(deduped_entries)} after dedup"
        )

        return IngestionResult(
            merged_entries=deduped_entries,
            sources=sources,
            dedup_stats=dedup_stats,
            warnings=list(self.warnings),
            errors=list(self.errors),
        )

    def dedupe_log_entries(
        self, entries: List[LogEntry]
    ) -> Tuple[List[LogEntry], int]:
        """
        Deduplicate log entries using (timestamp, log_type, raw_value) tuple.
        
        Args:
            entries: List of log entries (already sorted)
        
        Returns:
            Tuple of (deduplicated entries, count of duplicates removed)
        """
        seen: Dict[Tuple[datetime, str, str], bool] = defaultdict(bool)
        deduped: List[LogEntry] = []
        dup_count = 0

        for entry in entries:
            key = (entry.timestamp, entry.log_type.value, entry.raw_value)
            
            if seen[key]:
                dup_count += 1
            else:
                seen[key] = True
                deduped.append(entry)

        return deduped, dup_count

    def build_sources_array(
        self,
        log_sources: List[SourceFile],
        chart_sources: Optional[List[SourceFile]] = None,
        constraints_sources: Optional[List[SourceFile]] = None,
    ) -> List[SourceFile]:
        """
        Build combined sources array from all file types.
        
        Args:
            log_sources: Sources from log files
            chart_sources: Optional sources from chart images
            constraints_sources: Optional sources from constraints docs
        
        Returns:
            Combined list of all SourceFile entries
        """
        all_sources = list(log_sources)
        
        if chart_sources:
            all_sources.extend(chart_sources)
        
        if constraints_sources:
            all_sources.extend(constraints_sources)
        
        return all_sources

    def create_source_file(
        self,
        file_id: str,
        filename: str,
        file_type: SourceFileType,
        entry_count: int = 0,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        alignment: Optional[ChartAlignment] = None,
    ) -> SourceFile:
        """
        Create a SourceFile entry for tracking.
        
        Args:
            file_id: Unique identifier for the file
            filename: Original filename
            file_type: Type of file (log, chart, constraints)
            entry_count: Number of entries/items in the file
            time_range_start: Start time if applicable
            time_range_end: End time if applicable
            alignment: Optional chart alignment info
        
        Returns:
            SourceFile instance
        """
        return SourceFile(
            id=file_id,
            name=filename,
            type=file_type,
            entry_count=entry_count,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            alignment=alignment,
        )

    def _get_time_range(
        self, entries: List[LogEntry]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract min and max timestamps from log entries."""
        if not entries:
            return None, None
        
        timestamps = [e.timestamp for e in entries]
        return min(timestamps), max(timestamps)

    def ingest_logs_from_upload(
        self,
        uploaded_files: List[Tuple[str, bytes, str]],
    ) -> IngestionResult:
        """
        Ingest log files directly from uploaded bytes.
        
        Args:
            uploaded_files: List of (file_id, file_bytes, filename) tuples
        
        Returns:
            IngestionResult
        """
        file_contents: Dict[str, List[str]] = {}
        file_names: Dict[str, str] = {}

        for file_id, file_bytes, filename in uploaded_files:
            try:
                text_content = file_bytes.decode('utf-8')
                lines = text_content.splitlines()
                file_contents[file_id] = lines
                file_names[file_id] = filename
            except UnicodeDecodeError:
                try:
                    text_content = file_bytes.decode('latin-1')
                    lines = text_content.splitlines()
                    file_contents[file_id] = lines
                    file_names[file_id] = filename
                except Exception as e:
                    self.errors.append(f"Cannot decode file {filename}: {str(e)}")

        return self.ingest_log_files(file_contents, file_names)

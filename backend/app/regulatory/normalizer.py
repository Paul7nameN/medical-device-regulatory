from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.models.logs import LogEntry, LogType


class LogNormalizer:
    def __init__(self):
        pass

    def sort_by_timestamp(self, logs: List[LogEntry]) -> List[LogEntry]:
        return sorted(logs, key=lambda x: x.timestamp)

    def build_context(self, logs: List[LogEntry]) -> Dict[str, Any]:
        if not logs:
            return {
                "time_range_start": None,
                "time_range_end": None,
                "duration_seconds": 0,
                "door_events_per_hour": {},
                "door_open_count": 0,
                "door_close_count": 0,
                "sensor_availability": {
                    "primary": True,
                    "secondary": True
                },
                "sensor_timeouts": [],
                "temp_reading_count": 0,
                "alarm_count": 0,
                "sync_failures": 0
            }

        sorted_logs = self.sort_by_timestamp(logs)

        time_start = sorted_logs[0].timestamp
        time_end = sorted_logs[-1].timestamp
        duration = time_end - time_start

        door_open_events = [log for log in logs if log.log_type == LogType.DOOR_OPEN]
        door_close_events = [log for log in logs if log.log_type == LogType.DOOR_CLOSE]

        hourly_doors: Dict[datetime, int] = defaultdict(int)
        for event in door_open_events:
            hour_key = event.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_doors[hour_key] += 1

        sensor_timeouts = [log for log in logs if log.log_type == LogType.SENSOR_TIMEOUT]
        primary_timeout = any(
            "PRIMARY" in log.raw_value.upper() or (log.sensor_id and "PRIMARY" in log.sensor_id)
            for log in sensor_timeouts
        )
        secondary_timeout = any(
            "SECONDARY" in log.raw_value.upper() or (log.sensor_id and "SECONDARY" in log.sensor_id)
            for log in sensor_timeouts
        )

        temp_readings = [log for log in logs if log.log_type == LogType.TEMP_READING]
        alarms = [log for log in logs if log.log_type == LogType.ALARM_TRIGGERED]
        sync_failures = [log for log in logs if log.log_type == LogType.TELEMETRY_SYNC_FAILED]

        context: Dict[str, Any] = {
            "time_range_start": time_start,
            "time_range_end": time_end,
            "duration_seconds": duration.total_seconds(),
            "duration_hours": duration.total_seconds() / 3600,
            "door_events_per_hour": dict(hourly_doors),
            "door_open_count": len(door_open_events),
            "door_close_count": len(door_close_events),
            "sensor_availability": {
                "primary": not primary_timeout,
                "secondary": not secondary_timeout
            },
            "sensor_timeouts": [
                {
                    "timestamp": s.timestamp,
                    "sensor_id": s.sensor_id,
                    "raw_value": s.raw_value
                }
                for s in sensor_timeouts
            ],
            "temp_reading_count": len(temp_readings),
            "alarm_count": len(alarms),
            "sync_failures": len(sync_failures),
            "logs_sorted": sorted_logs
        }

        return context

    def identify_gaps(self, logs: List[LogEntry], max_gap_seconds: float = 90.0) -> List[Dict[str, Any]]:
        if len(logs) < 2:
            return []

        sorted_logs = self.sort_by_timestamp(logs)
        gaps: List[Dict[str, Any]] = []

        for i in range(1, len(sorted_logs)):
            gap_seconds = (sorted_logs[i].timestamp - sorted_logs[i-1].timestamp).total_seconds()
            if gap_seconds > max_gap_seconds:
                gaps.append({
                    "index": i,
                    "from_timestamp": sorted_logs[i-1].timestamp,
                    "to_timestamp": sorted_logs[i].timestamp,
                    "gap_seconds": gap_seconds,
                    "from_log_type": sorted_logs[i-1].log_type,
                    "to_log_type": sorted_logs[i].log_type
                })

        return gaps

    def normalize(self, logs: List[LogEntry]) -> Dict[str, Any]:
        sorted_logs = self.sort_by_timestamp(logs)
        context = self.build_context(sorted_logs)
        gaps = self.identify_gaps(sorted_logs)

        return {
            "sorted_logs": sorted_logs,
            "context": context,
            "gaps": gaps,
            "total_entries": len(sorted_logs)
        }

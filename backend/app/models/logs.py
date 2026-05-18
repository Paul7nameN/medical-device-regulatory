from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, field_serializer


class LogType(str, Enum):
    TEMP_READING = "TEMP_READING"
    FAN_SPEED = "FAN_SPEED"
    VOLTAGE = "VOLTAGE"
    HUMIDITY = "HUMIDITY"
    BATTERY_LEVEL = "BATTERY_LEVEL"
    DOOR_OPEN = "DOOR_OPEN"
    DOOR_CLOSE = "DOOR_CLOSE"
    DEVICE_START = "DEVICE_START"
    ALARM_TRIGGERED = "ALARM_TRIGGERED"
    TEMP_WARNING = "TEMP_WARNING"
    SENSOR_TIMEOUT = "SENSOR_TIMEOUT"
    TELEMETRY_SYNC_FAILED = "TELEMETRY_SYNC_FAILED"
    COOLING_RECOVERY_START = "COOLING_RECOVERY_START"


class LogEntry(BaseModel):
    timestamp: datetime
    log_type: LogType
    raw_value: str
    parsed_value: Optional[Any] = None
    sensor_id: Optional[str] = None
    metadata: dict = {}

    @field_serializer("timestamp")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "log_type": self.log_type.value if hasattr(self.log_type, 'value') else str(self.log_type),
            "raw_value": self.raw_value,
            "parsed_value": self.parsed_value,
            "sensor_id": self.sensor_id,
            "metadata": self.metadata
        }

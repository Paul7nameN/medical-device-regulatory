#!/usr/bin/env python3
"""Generate MED-THERM demo log files (~1000 lines each)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path


def fmt_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def line(dt: datetime, event: str) -> str:
    return f"{fmt_ts(dt)} {event}\n"


def generate_session(
    start: datetime,
    line_count: int,
    interval_seconds: int,
    temp_fn,
    weights: dict[str, float],
    seed: int,
) -> list[str]:
    rng = random.Random(seed)
    events = list(weights.keys())
    probs = [weights[e] for e in events]
    lines: list[str] = []
    dt = start

    for i in range(line_count):
        t = temp_fn(i, line_count)
        # Force telemetry every ~6th line for graphs
        if i % 6 == 1:
            kind = "TEMP_READING"
        elif i % 6 == 2:
            kind = "FAN_SPEED"
        elif i % 6 == 3:
            kind = "HUMIDITY"
        elif i % 6 == 4:
            kind = "VOLTAGE"
        elif i % 6 == 5:
            kind = "BATTERY_LEVEL"
        else:
            kind = rng.choices(events, weights=probs, k=1)[0]

        if kind == "TEMP_READING":
            lines.append(line(dt, f"TEMP_READING {t:.1f}C"))
        elif kind == "FAN_SPEED":
            rpm = int(1400 + (t - 4) * 180 + rng.randint(-120, 120))
            rpm = max(900, min(3200, rpm))
            lines.append(line(dt, f"FAN_SPEED {rpm}RPM"))
        elif kind == "HUMIDITY":
            h = int(35 + rng.randint(0, 45))
            lines.append(line(dt, f"HUMIDITY {h}%"))
        elif kind == "VOLTAGE":
            v = 12.4 - (i / line_count) * 0.6 + rng.uniform(-0.08, 0.08)
            lines.append(line(dt, f"VOLTAGE {v:.2f}V"))
        elif kind == "BATTERY_LEVEL":
            batt = 99.5 - (i / line_count) * 18 + rng.uniform(-0.3, 0.3)
            lines.append(line(dt, f"BATTERY_LEVEL {batt:.1f}%"))
        elif kind == "SENSOR_TIMEOUT":
            lines.append(line(dt, "SENSOR_TIMEOUT SECONDARY_SENSOR"))
        else:
            lines.append(line(dt, kind))

        dt += timedelta(seconds=interval_seconds)

    return lines


# Scenario B: mostly compliant cold chain (~2.5h window)
def temp_stable(i: int, n: int) -> float:
    base = 4.2 + (i / n) * 2.8  # 4.2 -> 7.0
    wobble = random.Random(i).uniform(-0.4, 0.4)
    return max(2.5, min(7.8, base + wobble))


weights_stable = {
    "DOOR_OPEN": 0.08,
    "DOOR_CLOSE": 0.08,
    "ALARM_TRIGGERED": 0.04,
    "TEMP_WARNING": 0.03,
    "COOLING_RECOVERY_START": 0.05,
    "DEVICE_START": 0.04,
    "TELEMETRY_SYNC_FAILED": 0.03,
    "SENSOR_TIMEOUT": 0.02,
    "TEMP_READING": 0.25,
    "FAN_SPEED": 0.12,
    "HUMIDITY": 0.10,
    "VOLTAGE": 0.08,
    "BATTERY_LEVEL": 0.08,
}


# Scenario C: excursion + redundancy loss (~2.5h window)
def temp_excursion(i: int, n: int) -> float:
    third = n // 3
    if i < third:
        return 4.5 + random.Random(i).uniform(0, 1.5)
    if i < 2 * third:
        return 7.5 + random.Random(i).uniform(0, 2.5)
    return 9.5 + random.Random(i).uniform(0, 2.5)  # up to ~12C


weights_critical = {
    "DOOR_OPEN": 0.12,
    "DOOR_CLOSE": 0.10,
    "ALARM_TRIGGERED": 0.09,
    "TEMP_WARNING": 0.10,
    "COOLING_RECOVERY_START": 0.08,
    "DEVICE_START": 0.04,
    "TELEMETRY_SYNC_FAILED": 0.06,
    "SENSOR_TIMEOUT": 0.08,
    "TEMP_READING": 0.15,
    "FAN_SPEED": 0.08,
    "HUMIDITY": 0.06,
    "VOLTAGE": 0.07,
    "BATTERY_LEVEL": 0.07,
}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_dirs = [
        repo_root / "docs" / "user-guide" / "examples",
        Path(r"C:\Users\Daniel-NicolaeVisa\Downloads\OneDrive_1_5-18-2026"),
    ]

    sessions = [
        (
            "medical_device_logs_1000_setB_stable.txt",
            datetime(2026, 5, 20, 8, 0, 0),
            1000,
            9,
            temp_stable,
            weights_stable,
            42,
        ),
        (
            "medical_device_logs_1000_setC_excursion.txt",
            datetime(2026, 5, 22, 10, 0, 0),
            1000,
            9,
            temp_excursion,
            weights_critical,
            77,
        ),
    ]

    for filename, start, count, interval, temp_fn, weights, seed in sessions:
        content = "".join(
            generate_session(start, count, interval, temp_fn, weights, seed)
        )
        for out_dir in out_dirs:
            if not out_dir.exists():
                continue
            path = out_dir / filename
            path.write_text(content, encoding="utf-8")
            print(f"Wrote {path} ({count} lines)")


if __name__ == "__main__":
    main()

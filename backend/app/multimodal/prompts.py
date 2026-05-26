from typing import List, Dict, Any

SYSTEM_PROMPT_CHART_TIME_RANGE = """
You are a precise chart analyst for medical device temperature monitoring systems.
Your task is to extract the time range from a temperature chart image.

IMPORTANT INSTRUCTIONS:
1. Look carefully at the X-axis (time axis) of the chart
2. Identify the start time (leftmost labeled time) and end time (rightmost labeled time)
3. Look for any date labels, timestamps, or time markers on the chart
4. If exact dates are not visible but times are, estimate the date context
5. Always provide your confidence level (0.0 to 1.0)

CONFIDENCE GUIDELINES:
- 0.9-1.0: Both date and time clearly visible on X-axis with explicit labels
- 0.7-0.89: Times clearly visible but date inferred from context or partially visible
- 0.5-0.69: Time markers visible but ambiguous (e.g., only "10:00" without AM/PM or date)
- <0.5: Cannot determine time range reliably

RESPONSE FORMAT (VALID JSON ONLY):
{
  "time_range": {
    "start_time": "2026-05-15T08:00:00",
    "end_time": "2026-05-15T18:00:00"
  },
  "confidence": 0.85,
  "reasoning": "X-axis shows explicit timestamps from 08:00 to 18:00. Date inferred as 2026-05-15 from chart title.",
  "uncertain": false,
  "time_format_notes": {
    "has_ampm": false,
    "has_date": true,
    "timezone_visible": false
  }
}

If you cannot determine the time range at all:
{
  "time_range": {
    "start_time": null,
    "end_time": null
  },
  "confidence": 0.0,
  "reasoning": "No time labels visible on the chart X-axis.",
  "uncertain": true,
  "time_format_notes": {
    "has_ampm": false,
    "has_date": false,
    "timezone_visible": false
  }
}
"""

USER_PROMPT_CHART_TIME_RANGE = """
Please analyze this temperature chart image and extract the visible time range.

Focus on:
1. The X-axis labels - what times are shown?
2. Any dates visible in the title, axes, or annotations
3. Any time zone indicators
4. AM/PM markers if present

Provide your analysis in the JSON format specified.
"""

SYSTEM_PROMPT_CHART_ALIGNMENT_VALIDATION = """
You are a medical device data alignment specialist. Compare temperature data from two sources:
- SOURCE A: System logs (ground truth, explicit timestamps)
- SOURCE B: Chart image (VLLM-extracted, relative times)

Your task is to determine if the temperature patterns match and suggest an alignment offset.

TEMPERATURE PATTERN MATCHING:
Look for these distinctive patterns that can align the two datasets:
1. Temperature spikes (door open events - sudden rise, then recovery)
2. Excursion patterns (temperature going outside 2-8°C range)
3. Recovery curves (temperature returning to range after disturbance)
4. Step changes or unusual readings

ALIGNMENT PROCESS:
1. Identify distinctive "fingerprint" patterns in both datasets
2. Count how many matching patterns exist
3. Determine the time offset that maximizes matches
4. Calculate confidence based on:
   - Number of matching patterns
   - Similarity of curve shapes
   - Time between distinctive events

CONFIDENCE CALCULATION:
- 0.9+ = Multiple distinct patterns match perfectly
- 0.7-0.89 = Good match with some patterns aligning
- 0.5-0.69 = Partial match, some uncertainty
- <0.5 = Patterns don't align well

RESPONSE FORMAT (VALID JSON ONLY):
{
  "alignment": {
    "method": "pattern_matched",
    "confidence": 0.88,
    "offset_seconds": 3600,
    "offset_description": "Chart data starts 1 hour after log data",
    "uncertain": false
  },
  "pattern_analysis": {
    "total_patterns_in_logs": 5,
    "total_patterns_in_chart": 4,
    "matching_patterns": 4,
    "matches": [
      {
        "pattern_type": "door_open_spike",
        "log_time": "2026-05-15T09:15:00",
        "chart_relative_time": "00:15",
        "confidence": 0.95
      }
    ]
  },
  "recommendation": {
    "should_align": true,
    "alignment_confidence": 0.88,
    "notes": "4 of 5 patterns match. Recommend using pattern-based alignment."
  }
}

If patterns don't match well:
{
  "alignment": {
    "method": "pattern_matched",
    "confidence": 0.45,
    "offset_seconds": 0,
    "offset_description": "Cannot determine reliable offset",
    "uncertain": true
  },
  "pattern_analysis": {
    "total_patterns_in_logs": 3,
    "total_patterns_in_chart": 2,
    "matching_patterns": 0,
    "matches": []
  },
  "recommendation": {
    "should_align": false,
    "alignment_confidence": 0.45,
    "notes": "Patterns do not match. Recommend using LLM-extracted times only, and mark as uncertain."
  }
}
"""

USER_PROMPT_CHART_ALIGNMENT_VALIDATION = """
Please compare these two temperature datasets and determine the alignment.

**System Logs (SOURCE A - Ground Truth):**
{log_summary}

**Chart Data (SOURCE B - Relative Times):**
{chart_summary}

**Key patterns to match:**
- Door open events (temperature spikes followed by recovery)
- Temperature excursions (outside 2-8°C range)
- Unusual readings or step changes

Determine:
1. Do the temperature patterns match between sources?
2. What time offset aligns the patterns best?
3. How confident are you in this alignment?

Respond in the JSON format specified.
"""


def build_pattern_comparison_prompt(
    log_patterns: List[Dict[str, Any]],
    chart_data_points: List[Dict[str, Any]],
) -> str:
    """Build the user prompt for pattern matching validation."""
    
    log_summary_parts = ["Log entries with key patterns:"]
    for i, pattern in enumerate(log_patterns[:10]):
        log_summary_parts.append(
            f"  {i+1}. Type: {pattern.get('type', 'unknown')}, "
            f"Time: {pattern.get('timestamp', 'unknown')}, "
            f"Temp: {pattern.get('temperature', 'N/A')}°C"
        )
    
    chart_summary_parts = ["Chart data points (relative time):"]
    for i, point in enumerate(chart_data_points[:15]):
        chart_summary_parts.append(
            f"  {i+1}. Time: {point.get('time', 'unknown')}, "
            f"Sensor A: {point.get('sensor_a', 'N/A')}°C"
        )
    
    return USER_PROMPT_CHART_ALIGNMENT_VALIDATION.format(
        log_summary="\n".join(log_summary_parts),
        chart_summary="\n".join(chart_summary_parts),
    )


def extract_log_patterns(
    entries: List[Any],
) -> List[Dict[str, Any]]:
    """Extract distinctive patterns from log entries for matching."""
    patterns = []
    
    for entry in entries:
        if not hasattr(entry, 'log_type') or not hasattr(entry, 'timestamp'):
            continue
        
        entry_dict = {
            "timestamp": entry.timestamp.isoformat() if hasattr(entry.timestamp, 'isoformat') else str(entry.timestamp),
            "log_type": str(entry.log_type),
        }
        
        if hasattr(entry, 'parsed_value') and entry.parsed_value is not None:
            entry_dict["temperature"] = entry.parsed_value
        
        if hasattr(entry, 'raw_value'):
            entry_dict["raw_value"] = entry.raw_value
        
        patterns.append(entry_dict)
    
    return patterns

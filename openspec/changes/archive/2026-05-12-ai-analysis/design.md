# Design: AI Analysis Module

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI APPLICATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐               │
│  │ /api/ai/...      │  │ /api/validate    │  │ /api/logs/...    │               │
│  │ (AI Analysis)    │  │ (Engine)         │  │ (Ingestion)      │               │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘               │
│           │                      │                      │                          │
│           └──────────────────────┼──────────────────────┘                          │
│                                  ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐      │
│  │                         AI ANALYSIS MODULE CORE                          │      │
│  │                                                                           │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │      │
│  │  │ ModelArk     │  │ Image        │  │ Text         │                  │      │
│  │  │ Client       │  │ Analysis     │  │ Analysis     │                  │      │
│  │  │ (OpenAI SDK) │  │ (Charts)     │  │ (Logs/Reports)│                  │      │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │      │
│  │         │                  │                  │                          │      │
│  │         └──────────────────┼──────────────────┘                          │      │
│  │                            ▼                                               │      │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │      │
│  │  │                    Regulatory Engine Integration                    │  │      │
│  │  │                                                                     │  │      │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │      │
│  │  │  │ Log      │  │ Chart    │  │ Cross    │  │ Enhanced │         │  │      │
│  │  │  │ Findings │  │ Findings │  │ Validation │ │ Reports  │         │  │      │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │  │      │
│  │  └────────────────────────────────────────────────────────────────────┘  │      │
│  └───────────────────────────────────────────────────────────────────────────┘      │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         MODELARK API (OpenAI-compatible)                            │
│                                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐               │
│  │ Dola-Seed-2.0-pro           │  │ GLM-4.7                      │               │
│  │ ep-20260406181344-7fmp8     │  │ ep-20260406181003-74jsw    │               │
│  │                              │  │                              │               │
│  │ • Visual chart analysis     │  │ • Log analysis               │               │
│  │ • Violation detection       │  │ • Report generation          │               │
│  │ • Image-to-text extraction  │  │ • Compliance summaries       │               │
│  └──────────────────────────────┘  └──────────────────────────────┘               │
│                                                                                      │
│  Base URL: https://ark.ap-southeast.bytepluses.com/api/v3                          │
│  Auth: Bearer Token via Authorization header                                        │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
backend/
├── app/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py           # ModelArk API client (OpenAI SDK wrapper)
│   │   ├── config.py           # AI module configuration
│   │   │
│   │   ├── image/
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py     # Chart image analysis (Dola-Seed-2.0-pro)
│   │   │   ├── prompts.py      # System prompts for image analysis
│   │   │   └── models.py       # Chart analysis data models
│   │   │
│   │   ├── text/
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py     # Log/text analysis (GLM-4.7)
│   │   │   ├── prompts.py      # System prompts for text analysis
│   │   │   ├── report.py       # Compliance report generation
│   │   │   └── models.py       # Text analysis data models
│   │   │
│   │   └── integration/
│   │       ├── __init__.py
│   │       └── engine.py       # Integration with RegulatoryEngine
│   │
│   ├── api/
│   │   └── ai.py               # FastAPI endpoints for AI analysis
│   │
│   └── config.py               # Updated with ModelArk settings
│
├── tests/
│   ├── test_ai_client.py       # API client tests
│   ├── test_image_analyzer.py  # Chart analysis tests
│   ├── test_text_analyzer.py   # Text analysis tests
│   └── test_ai_integration.py  # Integration tests
│
└── requirements.txt            # Updated with openai, httpx
```

---

## Core Data Models

### AI Analysis Request/Response Models

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class AIModelType(str, Enum):
    CHART_ANALYSIS = "chart_analysis"      # Dola-Seed-2.0-pro
    TEXT_ANALYSIS = "text_analysis"        # GLM-4.7


class ImageFormat(str, Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


class ChartViolationType(str, Enum):
    EXCURSION = "excursion"              # Temperature outside range
    GAP = "gap"                          # Missing data gap
    SLOW_RECOVERY = "slow_recovery"      # Recovery > 3min
    FREQUENT_ACCESS = "frequent_access"   # >10 door events/hour


class ChartViolation(BaseModel):
    violation_type: ChartViolationType
    timestamp_start: Optional[datetime]
    timestamp_end: Optional[datetime]
    description: str
    confidence: float  # 0.0 to 1.0
    extracted_value: Optional[float]


class ChartAnalysisResult(BaseModel):
    model_used: str
    analyzed_at: datetime
    duration_seconds: float
    
    chart_type: Optional[str]  # "temperature_profile", "timeline", etc.
    time_range_start: Optional[datetime]
    time_range_end: Optional[datetime]
    temp_range_min: Optional[float]
    temp_range_max: Optional[float]
    
    violations: List[ChartViolation]
    summary: str
    
    raw_response: Optional[Dict[str, Any]]
    confidence: float


class LogAnalysisResult(BaseModel):
    model_used: str
    analyzed_at: datetime
    duration_seconds: float
    
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    
    risk_assessment: str  # "low", "medium", "high", "critical"
    
    raw_response: Optional[Dict[str, Any]]


class ComplianceReportSection(BaseModel):
    title: str
    content: str
    bullet_points: Optional[List[str]]


class GeneratedReport(BaseModel):
    model_used: str
    generated_at: datetime
    duration_seconds: float
    
    report_type: str  # "compliance_summary", "audit_report", "incident_report"
    device_id: str
    title: str
    
    sections: List[ComplianceReportSection]
    executive_summary: str
    recommendations: str
    conclusion: str
    
    raw_response: Optional[Dict[str, Any]]


class CrossValidationResult(BaseModel):
    log_findings_count: int
    chart_findings_count: int
    matching_violations: int
    conflicting_findings: int
    
    confidence_score: float  # Agreement between sources
    
    summary: str


class AIError(BaseModel):
    error_type: str  # "api_error", "timeout", "rate_limit", "validation_error"
    message: str
    retry_available: bool
    retry_after_seconds: Optional[int]
```

---

## ModelArk API Client Design

### Client Architecture

```python
from openai import AsyncOpenAI
from typing import Optional, Dict, Any, List
from httpx import Timeout
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class ModelArkClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=Timeout(timeout=timeout)
        )
        self.max_retries = max_retries
        self.model_chart = "ep-20260406181344-7fmp8"
        self.model_text = "ep-20260406181003-74jsw"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            Exception,  # API errors, network errors
        ))
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send chat completion request to ModelArk API."""
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        
        response = await self.client.chat.completions.create(**kwargs)
        return response.model_dump()
    
    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        image_format: ImageFormat = ImageFormat.PNG
    ) -> Dict[str, Any]:
        """Analyze an image using Dola-Seed-2.0-pro."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        return await self.chat_completion(
            messages=messages,
            model=self.model_chart,
            response_format={"type": "json_object"}
        )
    
    async def analyze_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze text using GLM-4.7."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat_completion(
            messages=messages,
            model=self.model_text,
            response_format={"type": "json_object"}
        )
```

---

## Image Analysis Module (Chart Processing)

### Prompt Design for Dola-Seed-2.0-pro

**System Prompt for Chart Analysis:**

```python
SYSTEM_PROMPT_CHART_ANALYSIS = """
You are a medical device compliance analyst specializing in temperature profile charts.
Analyze the provided temperature chart image for MED-THERM-2026 compliance violations.

REGULATORY REQUIREMENTS:
- REG-TEMP-1: Temperature must stay within 2°C to 8°C
- REG-TEMP-2: Single excursion > 5min or cumulative > 10min/24h is critical
- REG-TEMP-3: Recovery after disturbance must be ≤ 3 minutes
- REG-TEMP-4: Sampling intervals must be ≤ 30 seconds
- REG-OPS-1: Door events must not cause prolonged excursions

ANALYSIS TASKS:
1. Identify the chart type (temperature profile, timeline, etc.)
2. Extract time range (start and end timestamps if visible)
3. Extract temperature range (min and max visible values)
4. Detect violations:
   - Excursions: temperatures outside 2-8°C range
   - Gaps: missing data or time jumps
   - Slow recovery: temperature not returning to range within 3min
   - Frequent access: multiple door disturbance patterns

5. For each violation, provide:
   - violation_type: excursion, gap, slow_recovery, frequent_access
   - timestamp_start: when violation started (estimate if axis visible)
   - timestamp_end: when violation ended (estimate)
   - description: detailed explanation
   - confidence: 0.0 to 1.0
   - extracted_value: relevant numeric value

RESPONSE FORMAT (JSON):
{
  "chart_type": "temperature_profile",
  "time_range": {
    "start": "2026-05-14T14:00:00",
    "end": "2026-05-14T18:00:00"
  },
  "temperature_range": {
    "min": 0.0,
    "max": 12.0
  },
  "violations": [
    {
      "violation_type": "excursion",
      "timestamp_start": "2026-05-14T14:30:00",
      "timestamp_end": "2026-05-14T14:45:00",
      "description": "Temperature exceeded 8°C for 15 minutes",
      "confidence": 0.95,
      "extracted_value": 10.5
    }
  ],
  "summary": "Overall compliance status with brief explanation",
  "confidence_score": 0.90
}
"""
```

### Image Analyzer Implementation

```python
class ChartAnalyzer:
    def __init__(self, client: ModelArkClient):
        self.client = client
    
    async def analyze(
        self,
        image_bytes: bytes,
        image_format: ImageFormat = ImageFormat.PNG
    ) -> ChartAnalysisResult:
        """Analyze a temperature chart image."""
        import base64
        
        start_time = datetime.now()
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        response = await self.client.analyze_image(
            image_base64=image_base64,
            prompt=SYSTEM_PROMPT_CHART_ANALYSIS,
            image_format=image_format
        )
        
        content = response['choices'][0]['message']['content']
        parsed = self._parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return self._build_result(parsed, response, duration)
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse and validate JSON response from model."""
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._extract_json_from_text(content)
    
    def _build_result(
        self,
        parsed: Dict,
        raw_response: Dict,
        duration: float
    ) -> ChartAnalysisResult:
        """Build structured result from parsed JSON."""
        violations = []
        for v in parsed.get("violations", []):
            try:
                violations.append(ChartViolation(
                    violation_type=ChartViolationType(v.get("violation_type")),
                    timestamp_start=self._parse_datetime(v.get("timestamp_start")),
                    timestamp_end=self._parse_datetime(v.get("timestamp_end")),
                    description=v.get("description", ""),
                    confidence=float(v.get("confidence", 0.5)),
                    extracted_value=v.get("extracted_value")
                ))
            except (ValueError, TypeError):
                continue
        
        return ChartAnalysisResult(
            model_used=self.client.model_chart,
            analyzed_at=datetime.now(),
            duration_seconds=duration,
            chart_type=parsed.get("chart_type"),
            time_range_start=self._parse_datetime(
                parsed.get("time_range", {}).get("start")
            ),
            time_range_end=self._parse_datetime(
                parsed.get("time_range", {}).get("end")
            ),
            temp_range_min=parsed.get("temperature_range", {}).get("min"),
            temp_range_max=parsed.get("temperature_range", {}).get("max"),
            violations=violations,
            summary=parsed.get("summary", ""),
            raw_response=raw_response,
            confidence=float(parsed.get("confidence_score", 0.5))
        )
```

---

## Text Analysis Module

### Prompt Design for GLM-4.7

**System Prompt for Log Analysis:**

```python
SYSTEM_PROMPT_LOG_ANALYSIS = """
You are a MED-THERM-2026 compliance analyst. Analyze the provided device log data
and generate a comprehensive analysis for regulatory compliance.

LOG FORMAT:
Each log entry has: timestamp, log_type, raw_value, parsed_value, sensor_id

SUPPORTED LOG TYPES:
- TEMP_READING: Temperature measurements (target: 2-8°C)
- FAN_SPEED: Cooling fan RPM
- VOLTAGE: Power voltage
- HUMIDITY: Ambient humidity
- BATTERY_LEVEL: Battery percentage
- DOOR_OPEN/DOOR_CLOSE: Access events
- ALARM_TRIGGERED: Alarm activation
- TEMP_WARNING: Temperature warning
- SENSOR_TIMEOUT: Sensor failure (PRIMARY or SECONDARY)
- TELEMETRY_SYNC_FAILED: Sync failure

ANALYSIS OUTPUT (JSON):
{
  "summary": "2-3 sentence overall summary",
  "key_findings": [
    "Finding 1",
    "Finding 2",
    "Finding 3"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ],
  "risk_assessment": "low|medium|high|critical"
}
"""
```

**System Prompt for Report Generation:**

```python
SYSTEM_PROMPT_REPORT_GENERATION = """
You are a regulatory compliance report generator. Create comprehensive, audit-ready
compliance reports for MED-THERM-2026 based on provided findings.

REPORT STRUCTURE:
1. Executive Summary - High-level overview
2. Device Information - Device ID, time range
3. Compliance Summary - Pass/fail by category
4. Detailed Findings - For each violation
5. Recommendations - Action items
6. Conclusion - Overall status

RESPONSE FORMAT (JSON):
{
  "title": "MED-THERM-2026 Compliance Report",
  "executive_summary": "Detailed executive summary paragraph",
  "sections": [
    {
      "title": "Section Title",
      "content": "Section content paragraph",
      "bullet_points": ["Point 1", "Point 2"]
    }
  ],
  "recommendations": "Detailed recommendations paragraph",
  "conclusion": "Conclusion paragraph"
}
"""
```

### Text Analyzer Implementation

```python
class TextAnalyzer:
    def __init__(self, client: ModelArkClient):
        self.client = client
    
    async def analyze_logs(
        self,
        logs: List[LogEntry],
        findings: List[Finding]
    ) -> LogAnalysisResult:
        """Analyze logs and findings for AI-powered insights."""
        start_time = datetime.now()
        
        prompt = self._build_log_analysis_prompt(logs, findings)
        
        response = await self.client.analyze_text(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_LOG_ANALYSIS
        )
        
        content = response['choices'][0]['message']['content']
        parsed = self._parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return LogAnalysisResult(
            model_used=self.client.model_text,
            analyzed_at=datetime.now(),
            duration_seconds=duration,
            summary=parsed.get("summary", ""),
            key_findings=parsed.get("key_findings", []),
            recommendations=parsed.get("recommendations", []),
            risk_assessment=parsed.get("risk_assessment", "low"),
            raw_response=response
        )
    
    async def generate_report(
        self,
        compliance_report: ComplianceReport,
        report_type: str = "compliance_summary"
    ) -> GeneratedReport:
        """Generate a comprehensive compliance report."""
        start_time = datetime.now()
        
        prompt = self._build_report_prompt(compliance_report, report_type)
        
        response = await self.client.analyze_text(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_REPORT_GENERATION
        )
        
        content = response['choices'][0]['message']['content']
        parsed = self._parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        sections = []
        for s in parsed.get("sections", []):
            sections.append(ComplianceReportSection(
                title=s.get("title", ""),
                content=s.get("content", ""),
                bullet_points=s.get("bullet_points")
            ))
        
        return GeneratedReport(
            model_used=self.client.model_text,
            generated_at=datetime.now(),
            duration_seconds=duration,
            report_type=report_type,
            device_id=compliance_report.device_id,
            title=parsed.get("title", "Compliance Report"),
            sections=sections,
            executive_summary=parsed.get("executive_summary", ""),
            recommendations=parsed.get("recommendations", ""),
            conclusion=parsed.get("conclusion", ""),
            raw_response=response
        )
    
    def _build_log_analysis_prompt(
        self,
        logs: List[LogEntry],
        findings: List[Finding]
    ) -> str:
        """Build prompt from log entries and findings."""
        log_summary = self._summarize_logs(logs)
        findings_summary = self._summarize_findings(findings)
        
        return f"""
DEVICE LOG ANALYSIS REQUEST:

LOG SUMMARY:
{log_summary}

REGULATORY FINDINGS:
{findings_summary}

Please analyze this data and provide your insights in JSON format.
"""
```

---

## API Endpoints Design

### POST /api/ai/analyze-chart

Analyze a temperature profile chart image.

**Request:**
```
Content-Type: multipart/form-data

Parameters:
- file: Image file (PNG/JPG)
- device_id: Optional device identifier
```

**Response:**
```json
{
  "result": {
    "model_used": "ep-20260406181344-7fmp8",
    "analyzed_at": "2026-05-12T15:30:00",
    "duration_seconds": 8.5,
    "chart_type": "temperature_profile",
    "violations": [
      {
        "violation_type": "excursion",
        "description": "Temperature exceeded 8°C for 15 minutes",
        "confidence": 0.95
      }
    ],
    "summary": "Chart shows one temperature excursion violation...",
    "confidence": 0.90
  }
}
```

### POST /api/ai/analyze-logs

Analyze logs with AI for insights and summaries.

**Request:**
```json
{
  "logs": [
    {"timestamp": "2026-05-14T14:00:10", "log_type": "TEMP_READING", "raw_value": "4.3C"}
  ],
  "device_id": "CRYOSAFE-001"
}
```

**Response:**
```json
{
  "result": {
    "model_used": "ep-20260406181003-74jsw",
    "summary": "Device operating within normal parameters...",
    "key_findings": ["Temperature readings are stable..."],
    "recommendations": ["No immediate action required"],
    "risk_assessment": "low"
  }
}
```

### POST /api/ai/generate-report

Generate an AI-powered compliance report.

**Request:**
```json
{
  "report": { /* ComplianceReport from validation */ },
  "report_type": "compliance_summary",
  "device_id": "CRYOSAFE-001"
}
```

**Response:**
```json
{
  "report": {
    "title": "MED-THERM-2026 Compliance Report",
    "executive_summary": "Device CRYOSAFE-001 shows...",
    "sections": [
      {"title": "Executive Summary", "content": "..."},
      {"title": "Compliance Status", "content": "..."}
    ],
    "recommendations": "...",
    "conclusion": "..."
  }
}
```

### GET /api/ai/models

List available models and status.

**Response:**
```json
{
  "models": [
    {
      "id": "ep-20260406181344-7fmp8",
      "name": "Dola-Seed-2.0-pro",
      "purpose": "chart_analysis",
      "status": "available"
    },
    {
      "id": "ep-20260406181003-74jsw",
      "name": "GLM-4.7",
      "purpose": "text_analysis",
      "status": "available"
    }
  ],
  "api_status": "connected",
  "config": {
    "base_url": "https://ark.ap-southeast.bytepluses.com/api/v3",
    "timeout": 60,
    "max_retries": 3
  }
}
```

---

## Integration with Regulatory Engine

### Enhanced Validation Flow

```python
class AIAugmentedRegulatoryEngine:
    def __init__(
        self,
        base_engine: RegulatoryEngine,
        ai_client: ModelArkClient
    ):
        self.base_engine = base_engine
        self.chart_analyzer = ChartAnalyzer(ai_client)
        self.text_analyzer = TextAnalyzer(ai_client)
    
    async def validate_with_ai(
        self,
        logs: List[LogEntry],
        chart_image: Optional[bytes] = None,
        chart_format: ImageFormat = ImageFormat.PNG,
        filter_rules: Optional[List[str]] = None,
        device_id: str = "unknown"
    ) -> Dict[str, Any]:
        """Run validation with optional AI chart analysis."""
        # 1. Run base validation
        report = self.base_engine.validate(
            logs=logs,
            filter_rules=filter_rules,
            device_id=device_id
        )
        
        result = {
            "base_report": report,
            "ai_analysis": {}
        }
        
        # 2. Analyze chart if provided
        if chart_image:
            chart_result = await self.chart_analyzer.analyze(
                chart_image, chart_format
            )
            result["ai_analysis"]["chart"] = chart_result
            
            # 3. Cross-validate with log findings
            cross_validation = self._cross_validate(
                report.findings,
                chart_result.violations
            )
            result["cross_validation"] = cross_validation
        
        # 4. Generate AI log analysis
        log_analysis = await self.text_analyzer.analyze_logs(
            logs, report.findings
        )
        result["ai_analysis"]["logs"] = log_analysis
        
        # 5. Generate enhanced report
        enhanced_report = await self.text_analyzer.generate_report(
            report, "compliance_summary"
        )
        result["ai_analysis"]["report"] = enhanced_report
        
        return result
    
    def _cross_validate(
        self,
        log_findings: List[Finding],
        chart_violations: List[ChartViolation]
    ) -> CrossValidationResult:
        """Cross-validate findings from logs and chart analysis."""
        matching = 0
        conflicting = 0
        
        for chart_violation in chart_violations:
            # Check if matching finding exists in log-based findings
            for log_finding in log_findings:
                if self._violations_match(chart_violation, log_finding):
                    matching += 1
                    break
            else:
                conflicting += 1
        
        total_log = len(log_findings)
        total_chart = len(chart_violations)
        
        confidence = (
            matching / max(total_log, total_chart)
            if max(total_log, total_chart) > 0
            else 1.0
        )
        
        return CrossValidationResult(
            log_findings_count=total_log,
            chart_findings_count=total_chart,
            matching_violations=matching,
            conflicting_findings=conflicting,
            confidence_score=confidence,
            summary=f"Log findings: {total_log}, Chart findings: {total_chart}, "
                   f"Matching: {matching}, Confidence: {confidence:.1%}"
        )
```

---

## Error Handling & Retry Logic

### Error Types

```python
class AIError(Exception):
    """Base exception for AI analysis errors."""
    pass


class AIAPIError(AIError):
    """API call failed."""
    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message)


class AITimeoutError(AIError):
    """API call timed out."""
    pass


class AIRateLimitError(AIError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message)


class AIValidationError(AIError):
    """Input validation failed."""
    pass


class AIImageError(AIError):
    """Image processing failed."""
    pass
```

### Retry Strategy

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

# Retry configuration
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=2, max=10),
    "retry": retry_if_exception_type((
        AIAPIError,
        AITimeoutError,
        ConnectionError,
        TimeoutError
    ))
}

@retry(**RETRY_CONFIG)
async def with_retry(func, *args, **kwargs):
    """Execute function with retry logic."""
    try:
        return await func(*args, **kwargs)
    except RetryError as e:
        raise AIAPIError(
            f"All retries failed: {e.last_attempt.exception()}"
        )
```

### Fallback Strategy

```python
async def analyze_chart_with_fallback(
    image_bytes: bytes,
    analyzer: ChartAnalyzer
) -> Tuple[Optional[ChartAnalysisResult], Optional[AIError]]:
    """Try AI analysis, fall back to None with error info."""
    try:
        result = await analyzer.analyze(image_bytes)
        return result, None
    except AIAPIError as e:
        logger.warning(f"AI chart analysis failed: {e}")
        return None, e
    except AIRateLimitError as e:
        logger.warning(f"Rate limited: {e}, retry after {e.retry_after}s")
        return None, e
    except Exception as e:
        logger.error(f"Unexpected error in chart analysis: {e}")
        return None, AIError(str(e))
```

---

## Configuration Updates

### Updated Settings

```python
# app/config.py

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Existing settings
    app_name: str = "MED-THERM Compliance Engine"
    app_version: str = "0.1.0"
    debug: bool = True
    cors_origins: list = ["*"]
    
    # VLLM settings (existing)
    vllm_provider: Optional[str] = None
    vllm_api_key: Optional[str] = None
    vllm_model: Optional[str] = None
    
    # NEW: ModelArk AI Settings
    modelark_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    modelark_api_key: Optional[str] = None
    
    model_chart_analysis: str = "ep-20260406181344-7fmp8"  # Dola-Seed-2.0-pro
    model_text_analysis: str = "ep-20260406181003-74jsw"  # GLM-4.7
    
    modelark_timeout: int = 60
    modelark_max_retries: int = 3
    modelark_retry_delay: float = 1.0
    
    ai_enabled: bool = False  # Enable only when API key is configured
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Auto-enable AI if API key is provided
if settings.modelark_api_key and not settings.ai_enabled:
    settings.ai_enabled = True
```

### Environment Variables (.env)

```env
# ModelArk AI Configuration
MODELARK_API_KEY=your-api-key-here
MODELARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
MODELARK_TIMEOUT=60
MODELARK_MAX_RETRIES=3
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_ai_client.py
class TestModelArkClient:
    def test_chat_completion(self, mock_openai_client):
        pass
    
    def test_retry_on_api_error(self, mock_openai_client):
        pass
    
    def test_image_analysis_prompt_building(self):
        pass
    
    def test_text_analysis_prompt_building(self):
        pass


# tests/test_image_analyzer.py
class TestChartAnalyzer:
    def test_parse_json_response(self):
        pass
    
    def test_parse_json_from_text_fallback(self):
        pass
    
    def test_build_result(self):
        pass
    
    def test_violation_type_parsing(self):
        pass


# tests/test_text_analyzer.py
class TestTextAnalyzer:
    def test_log_summary_generation(self):
        pass
    
    def test_findings_summary_generation(self):
        pass
    
    def test_report_section_parsing(self):
        pass
```

### Integration Tests

```python
# tests/test_ai_integration.py
class TestAIIntegration:
    @pytest.mark.asyncio
    async def test_validate_with_ai(self):
        pass
    
    @pytest.mark.asyncio
    async def test_cross_validation_matching(self):
        pass
    
    @pytest.mark.asyncio
    async def test_cross_validation_conflicting(self):
        pass
    
    @pytest.mark.asyncio
    async def test_fallback_on_api_error(self):
        pass
```

### Mock Setup

```python
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_openai_client():
    with patch('openai.AsyncOpenAI') as mock:
        mock_response = AsyncMock()
        mock_response.choices[0].message.content = '{"test": "response"}'
        mock.return_value.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        yield mock


@pytest.fixture
def sample_chart_response():
    return {
        "choices": [
            {
                "message": {
                    "content": '''
                    {
                        "chart_type": "temperature_profile",
                        "violations": [],
                        "summary": "Test chart analysis",
                        "confidence_score": 0.9
                    }
                    '''
                }
            }
        ]
    }
```

---

## Technology Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| **OpenAI SDK** | ModelArk is OpenAI-compatible, SDK provides reliable client | Direct httpx calls |
| **tenacity** | Robust retry logic with exponential backoff | Manual retry loops |
| **Pydantic v2** | Type-safe request/response models, consistent with existing code | Dataclasses |
| **Async implementation** | Non-blocking API calls, better for concurrent requests | Sync implementation |
| **JSON response format** | Structured, easy to parse and validate | Free-form text |

---

## Performance Considerations

| Operation | Target | Notes |
|-----------|--------|-------|
| Chart analysis | < 30s | Includes image upload + model inference |
| Text analysis | < 15s | Log summary generation |
| Report generation | < 20s | Comprehensive report generation |
| Memory per request | < 50MB | Image + response handling |

### Optimization Strategies

1. **Connection pooling** - Reuse HTTP connections via OpenAI SDK
2. **Request batching** - Batch multiple log entries in single prompt
3. **Response caching** - Cache identical chart images and log batches
4. **Async processing** - Use async/await for concurrent API calls
5. **Timeout configuration** - Per-operation timeouts with graceful degradation

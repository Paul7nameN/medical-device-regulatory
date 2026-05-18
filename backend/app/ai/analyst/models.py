from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendIndicator(str, Enum):
    STABLE = "stable"
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"


class InsightCategory(str, Enum):
    SENSOR = "sensor"
    POWER = "power"
    COOLING = "cooling"
    OPERATIONAL = "operational"
    ENVIRONMENTAL = "environmental"
    THERMAL = "thermal"
    DATA = "data"
    ALARM = "alarm"


class InsightRiskFactor(BaseModel):
    factor: str
    severity: str


class RiskOverview(BaseModel):
    overall_risk_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Overall risk score from 0.0 to 1.0"
    )
    risk_level: RiskLevel = Field(
        ..., 
        description="Risk level: low, medium, high, critical"
    )
    primary_risk_category: str = Field(
        ..., 
        description="Primary category driving the risk"
    )
    imminent_concerns_count: int = Field(
        default=0, 
        description="Number of immediate concerns identified"
    )
    trend_indicator: TrendIndicator = Field(
        default=TrendIndicator.STABLE, 
        description="Trend direction: stable, improving, deteriorating"
    )


class Insight(BaseModel):
    id: str = Field(..., description="Unique identifier for this insight")
    priority: RiskLevel = Field(
        ..., 
        description="Priority/severity of this insight"
    )
    category: str = Field(
        ..., 
        description="Category: sensor, power, cooling, operational, environmental, thermal, data, alarm"
    )
    title: str = Field(
        ..., 
        description="Short title for this insight"
    )
    evidence: List[str] = Field(
        default_factory=list, 
        description="Evidence supporting this insight"
    )
    why_matters: str = Field(
        default="", 
        description="Why this is important from a regulatory/risk perspective"
    )
    risk_score_contribution: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="How much this contributes to overall risk score"
    )
    risk_factors: List[InsightRiskFactor] = Field(
        default_factory=list, 
        description="Specific risk factors identified"
    )


class Prediction(BaseModel):
    id: str = Field(..., description="Unique identifier for this prediction")
    scenario: str = Field(
        ..., 
        description="What scenario is predicted"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence in this prediction (0.0-1.0)"
    )
    timeframe: str = Field(
        default="", 
        description="Timeframe for this prediction (e.g., 'next 2-4 hours')"
    )
    estimated_probability: str = Field(
        default="", 
        description="Human-readable probability (e.g., '75%')"
    )
    risk_factors_driving_this: List[str] = Field(
        default_factory=list, 
        description="Factors supporting this prediction"
    )
    mitigation_potential: Optional[str] = Field(
        default=None, 
        description="How risk could be mitigated"
    )
    why_concerning: Optional[str] = Field(
        default=None, 
        description="Why this prediction matters"
    )


class ActionItem(BaseModel):
    action: str = Field(..., description="What action to take")
    priority: RiskLevel = Field(
        ..., 
        description="Priority of this action"
    )
    steps: Optional[List[str]] = Field(
        default=None, 
        description="Step-by-step instructions if applicable"
    )
    why_needed: Optional[str] = Field(
        default=None, 
        description="Why this action is needed"
    )
    rationale: Optional[str] = Field(
        default=None, 
        description="Additional rationale/context"
    )


class ActionPlan(BaseModel):
    summary: str = Field(
        default="", 
        description="High-level summary of the action plan"
    )
    immediate_actions_0_1h: List[ActionItem] = Field(
        default_factory=list, 
        description="Actions to take within the next hour"
    )
    short_term_24h: List[ActionItem] = Field(
        default_factory=list, 
        description="Actions to take within 24 hours"
    )
    long_term_maintenance: List[ActionItem] = Field(
        default_factory=list, 
        description="Long-term maintenance and process improvements"
    )


class AIAnalysisResult(BaseModel):
    session_risk_overview: RiskOverview
    insights: List[Insight] = Field(default_factory=list)
    predictions: List[Prediction] = Field(default_factory=list)
    action_plan: ActionPlan
    natural_language_summary: str = Field(
        ..., 
        description="Human-readable summary in natural language"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        description="When this analysis was generated"
    )
    model_used: Optional[str] = Field(
        default=None, 
        description="Model used for this analysis"
    )


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    analysis_session_id: Optional[str] = Field(
        default=None, 
        description="Optional session ID for context"
    )
    message: str = Field(..., description="User's message")
    chat_history: List[ChatMessage] = Field(
        default_factory=list, 
        description="Conversation history for context"
    )


class ChatResponse(BaseModel):
    message: str = Field(..., description="AI's response")
    sources: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Referenced insights/sources if applicable"
    )
    suggested_actions: List[str] = Field(
        default_factory=list, 
        description="Suggested follow-up actions"
    )


class Thresholds(BaseModel):
    safe_temp_range: List[float] = Field(
        default=[2.0, 8.0], 
        description="Safe temperature range [min, max] in Celsius"
    )
    max_single_excursion_min: int = Field(
        default=5, 
        description="Maximum single excursion duration in minutes"
    )
    max_cumulative_excursion_24h: int = Field(
        default=10, 
        description="Maximum cumulative excursion in 24 hours (minutes)"
    )
    max_recovery_min: int = Field(
        default=3, 
        description="Maximum recovery time after disturbance in minutes"
    )
    sensor_disagreement_max_celsius: float = Field(
        default=0.5, 
        description="Maximum allowed disagreement between dual sensors"
    )
    max_door_events_per_hour: int = Field(
        default=10, 
        description="Maximum door events per hour before concern"
    )
    battery_backup_required_hours: int = Field(
        default=4, 
        description="Required battery backup runtime"
    )
    max_sampling_interval_sec: int = Field(
        default=30, 
        description="Maximum temperature sampling interval in seconds"
    )
    max_telemetry_gap_sec: int = Field(
        default=90, 
        description="Maximum telemetry gap in seconds"
    )


DEFAULT_THRESHOLDS = Thresholds()

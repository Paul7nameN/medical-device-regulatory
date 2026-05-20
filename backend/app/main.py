from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api import health, logs, validate, ai, reports, multimodal

from app.regulatory.rules import (
    RegTemp1, RegTemp2, RegTemp3, RegTemp4,
    RegSens1, RegSens2, RegSens3,
    RegAlarm1, RegAlarm2, RegAlarm3,
    RegData1, RegData2, RegData3,
    RegPower1, RegPower2,
    RegCool1, RegCool2,
    RegIns1, RegIns2,
    RegOps1, RegOps2,
)
from app.regulatory.rules.base import RuleRegistry


def register_all_rules():
    RuleRegistry.clear()

    RuleRegistry.register(RegTemp1)
    RuleRegistry.register(RegTemp2)
    RuleRegistry.register(RegTemp3)
    RuleRegistry.register(RegTemp4)

    RuleRegistry.register(RegSens1)
    RuleRegistry.register(RegSens2)
    RuleRegistry.register(RegSens3)

    RuleRegistry.register(RegAlarm1)
    RuleRegistry.register(RegAlarm2)
    RuleRegistry.register(RegAlarm3)

    RuleRegistry.register(RegData1)
    RuleRegistry.register(RegData2)
    RuleRegistry.register(RegData3)

    RuleRegistry.register(RegPower1)
    RuleRegistry.register(RegPower2)

    RuleRegistry.register(RegCool1)
    RuleRegistry.register(RegCool2)

    RuleRegistry.register(RegIns1)
    RuleRegistry.register(RegIns2)

    RuleRegistry.register(RegOps1)
    RuleRegistry.register(RegOps2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_all_rules()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="MED-THERM-2026 Regulatory Compliance Engine for medical device temperature-controlled transport units",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(logs.router, prefix="/api", tags=["Logs"])
app.include_router(validate.router, prefix="/api", tags=["Validation"])
app.include_router(ai.router, prefix="/api", tags=["AI Analysis"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(multimodal.router, prefix="/api", tags=["Multi-Modal Analysis"])


@app.get("/")
async def root():
    endpoints = {
        "health": "/api/health",
        "health_db": "/api/health/db",
        "rules": "/api/health/rules",
        "ingest": "/api/logs/ingest",
        "list_logs": "/api/logs",
        "validate": "/api/validate",
        "list_analysis": "/api/analysis",
        "quick_test": "/api/validate/quick-test",
        "generate_report": "/api/reports/generate",
        "list_reports": "/api/reports",
    }
    
    if settings.ai_enabled:
        endpoints["ai_models"] = "/api/ai/models"
        endpoints["ai_analyze_chart"] = "/api/ai/analyze-chart"
        endpoints["ai_analyze_logs"] = "/api/ai/analyze-logs"
        endpoints["ai_generate_report"] = "/api/ai/generate-report"
        endpoints["multimodal_analyze"] = "/api/multimodal/analyze"
        endpoints["multimodal_status"] = "/api/multimodal/status/{id}"
        endpoints["multimodal_results"] = "/api/multimodal/results/{id}"
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "ai_enabled": settings.ai_enabled,
        "docs": "/docs",
        "endpoints": endpoints
    }

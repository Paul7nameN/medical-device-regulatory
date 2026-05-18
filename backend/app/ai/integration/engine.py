from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import logging

from app.config import settings
from app.models.logs import LogEntry
from app.models.findings import Finding, ComplianceReport, Severity
from app.regulatory.engine import RegulatoryEngine

from app.ai.client import (
    ModelArkClient,
    AIError,
    AIValidationError,
)
from app.ai.image.models import (
    ChartAnalysisResult,
    ChartViolation,
    CrossValidationResult,
)
from app.ai.text.models import (
    LogAnalysisResult,
    GeneratedReport,
)
from app.ai.image.analyzer import ChartAnalyzer
from app.ai.text.analyzer import TextAnalyzer

logger = logging.getLogger(__name__)


class AIAugmentedRegulatoryEngine:
    def __init__(
        self,
        base_engine: Optional[RegulatoryEngine] = None,
        client: Optional[ModelArkClient] = None
    ):
        self.base_engine = base_engine or RegulatoryEngine()
        self.client = client or ModelArkClient()
        self.chart_analyzer = ChartAnalyzer(self.client)
        self.text_analyzer = TextAnalyzer(self.client)

    async def validate_with_ai(
        self,
        logs: List[LogEntry],
        chart_image_bytes: Optional[bytes] = None,
        chart_format: str = "png",
        filter_rules: Optional[List[str]] = None,
        device_id: str = "unknown",
        ai_required: bool = False,
        generate_ai_report: bool = False
    ) -> Dict[str, Any]:
        if not logs:
            return {
                "report": self._create_empty_result(device_id),
                "ai_analysis": None,
                "cross_validation": None,
                "ai_enabled": settings.ai_enabled,
                "warnings": []
            }

        warnings = []
        ai_analysis = None
        cross_validation = None

        base_report = self.base_engine.validate(
            logs=logs,
            filter_rules=filter_rules,
            device_id=device_id
        )

        result = {
            "report": base_report,
            "ai_enabled": settings.ai_enabled,
            "warnings": warnings,
        }

        if not settings.ai_enabled:
            if ai_required:
                raise AIValidationError(
                    "AI analysis is required but not enabled. Set MODELARK_API_KEY."
                )
            warnings.append("AI analysis not enabled. Set MODELARK_API_KEY to enable.")
            result["warnings"] = warnings
            return result

        try:
            ai_analysis = {}

            if chart_image_bytes:
                from app.ai.client import ImageFormat
                format_enum = ImageFormat(chart_format.lower())
                chart_result = await self.chart_analyzer.analyze(
                    chart_image_bytes,
                    format_enum
                )
                ai_analysis["chart"] = chart_result

                if hasattr(base_report, 'findings') and base_report.findings:
                    cross_validation = self._cross_validate(
                        log_findings=base_report.findings,
                        chart_result=chart_result
                    )
                    result["cross_validation"] = cross_validation

            log_analysis_result = await self.text_analyzer.analyze_logs(
                logs,
                base_report.findings if hasattr(base_report, 'findings') else []
            )
            ai_analysis["logs"] = log_analysis_result

            if generate_ai_report:
                ai_report = await self.text_analyzer.generate_report(
                    base_report,
                    "compliance_summary"
                )
                ai_analysis["report"] = ai_report

            result["ai_analysis"] = ai_analysis

        except AIError as e:
            error_msg = f"AI analysis failed: {str(e)}"
            logger.warning(error_msg)

            if ai_required:
                raise
            warnings.append(error_msg)
            result["warnings"] = warnings

        except Exception as e:
            error_msg = f"Unexpected error in AI analysis: {str(e)}"
            logger.error(error_msg)

            if ai_required:
                raise AIValidationError(error_msg)
            warnings.append(error_msg)
            result["warnings"] = warnings

        return result

    def _cross_validate(
        self,
        log_findings: List[Finding],
        chart_result: ChartAnalysisResult
    ) -> CrossValidationResult:
        log_violation_count = sum(
            1 for f in log_findings
            if not f.passed and f.severity in [
                Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM
            ]
        )

        chart_violation_count = len(chart_result.violations) if chart_result.violations else 0

        matching_count = 0
        conflicting_count = 0

        log_temp_violations = [
            f for f in log_findings
            if not f.passed and f.rule_id in [
                "REG-TEMP-1", "REG-TEMP-2", "REG-TEMP-3", "REG-TEMP-4"
            ]
        ]

        chart_temp_violations = [
            v for v in (chart_result.violations or [])
            if v.violation_type.value in ["excursion", "slow_recovery", "gap"]
        ]

        if log_temp_violations and chart_temp_violations:
            matching_count = min(len(log_temp_violations), len(chart_temp_violations))
        elif log_temp_violations or chart_temp_violations:
            conflicting_count = abs(len(log_temp_violations) - len(chart_temp_violations))

        total = log_violation_count + chart_violation_count
        confidence = 1.0

        if total > 0:
            if matching_count > 0:
                max_possible = max(len(log_temp_violations), len(chart_temp_violations))
                if max_possible > 0:
                    confidence = matching_count / max_possible
            elif conflicting_count > 0:
                confidence = 0.3

        summary_parts = []
        if matching_count > 0:
            summary_parts.append(f"{matching_count} matching violations detected")
        if conflicting_count > 0:
            summary_parts.append(f"{conflicting_count} potential conflicts")

        if not summary_parts:
            summary = "No significant violations detected in either source"
        else:
            summary = "; ".join(summary_parts)

        if not settings.ai_enabled:
            summary += " (AI analysis not enabled)"

        return CrossValidationResult(
            log_findings_count=log_violation_count,
            chart_findings_count=chart_violation_count,
            matching_violations=matching_count,
            conflicting_findings=conflicting_count,
            confidence_score=confidence,
            summary=summary
        )

    def _create_empty_result(self, device_id: str) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "analyzed_at": datetime.now().isoformat(),
            "total_entries": 0,
            "summary": {},
            "findings": [],
            "passed_count": 0,
            "failed_count": 0,
            "critical_count": 0,
        }


async def validate_with_ai(
    logs: List[LogEntry],
    chart_image_bytes: Optional[bytes] = None,
    chart_format: str = "png",
    filter_rules: Optional[List[str]] = None,
    device_id: str = "unknown",
    ai_required: bool = False,
    generate_ai_report: bool = False
) -> Dict[str, Any]:
    engine = AIAugmentedRegulatoryEngine()
    return await engine.validate_with_ai(
        logs=logs,
        chart_image_bytes=chart_image_bytes,
        chart_format=chart_format,
        filter_rules=filter_rules,
        device_id=device_id,
        ai_required=ai_required,
        generate_ai_report=generate_ai_report
    )

from datetime import datetime
from typing import List, Optional, Dict, Any
from collections import defaultdict

from app.ai.client import ModelArkClient, AIError, AIValidationError
from app.ai.text.models import (
    LogAnalysisResult,
    ComplianceReportSection,
    GeneratedReport
)
from app.ai.text.prompts import (
    SYSTEM_PROMPT_LOG_ANALYSIS,
    SYSTEM_PROMPT_REPORT_GENERATION,
    SYSTEM_PROMPT_RULE_EXTRACTION,
    LOG_ANALYSIS_USER_PROMPT_TEMPLATE,
    REPORT_GENERATION_USER_PROMPT_TEMPLATE,
    USER_PROMPT_RULE_EXTRACTION_TEMPLATE,
)
from app.config import settings

try:
    from app.models.logs import LogEntry, LogType
    from app.models.findings import Finding, ComplianceReport, Severity
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


class TextAnalyzer:
    def __init__(self, client: Optional[ModelArkClient] = None):
        self.client = client or ModelArkClient()
    
    async def analyze_logs(
        self,
        logs: List[Any],
        findings: List[Any]
    ) -> LogAnalysisResult:
        if not settings.ai_enabled:
            raise AIValidationError(
                "AI analysis is not enabled. Set MODELARK_API_KEY environment variable."
            )
        
        start_time = datetime.now()
        
        log_summary = self._summarize_logs(logs)
        findings_summary = self._summarize_findings(findings)
        
        user_prompt = LOG_ANALYSIS_USER_PROMPT_TEMPLATE.format(
            log_summary=log_summary,
            findings_summary=findings_summary
        )
        
        response = await self.client.analyze_text(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_LOG_ANALYSIS
        )
        
        content = self._extract_response_content(response)
        parsed = ModelArkClient.parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return LogAnalysisResult(
            model_used=settings.model_text_analysis,
            analyzed_at=datetime.now(),
            duration_seconds=duration,
            summary=str(parsed.get("summary", "")),
            key_findings=[str(f) for f in parsed.get("key_findings", [])],
            recommendations=[str(r) for r in parsed.get("recommendations", [])],
            risk_assessment=str(parsed.get("risk_assessment", "low")),
            raw_response=response
        )
    
    async def generate_report(
        self,
        compliance_report: Any,
        report_type: str = "compliance_summary"
    ) -> GeneratedReport:
        if not settings.ai_enabled:
            raise AIValidationError(
                "AI analysis is not enabled. Set MODELARK_API_KEY environment variable."
            )
        
        start_time = datetime.now()
        
        report_data = self._extract_report_data(compliance_report)
        
        category_breakdown = self._format_category_breakdown(
            compliance_report.summary if hasattr(compliance_report, 'summary') else {}
        )
        
        key_findings = self._format_key_findings(
            compliance_report.findings if hasattr(compliance_report, 'findings') else []
        )
        
        user_prompt = REPORT_GENERATION_USER_PROMPT_TEMPLATE.format(
            device_id=report_data.get("device_id", "unknown"),
            total_entries=report_data.get("total_entries", 0),
            time_range_start=report_data.get("time_range_start", "N/A"),
            time_range_end=report_data.get("time_range_end", "N/A"),
            passed_count=report_data.get("passed_count", 0),
            failed_count=report_data.get("failed_count", 0),
            critical_count=report_data.get("critical_count", 0),
            category_breakdown=category_breakdown,
            key_findings=key_findings
        )
        
        response = await self.client.analyze_text(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_REPORT_GENERATION
        )
        
        content = self._extract_response_content(response)
        parsed = ModelArkClient.parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        sections = []
        section_dicts = parsed.get("sections", [])
        if isinstance(section_dicts, list):
            for s in section_dicts:
                if isinstance(s, dict):
                    sections.append(ComplianceReportSection(
                        title=str(s.get("title", "")),
                        content=str(s.get("content", "")),
                        bullet_points=[str(bp) for bp in s.get("bullet_points", [])] if s.get("bullet_points") else None
                    ))
        
        return GeneratedReport(
            model_used=settings.model_text_analysis,
            generated_at=datetime.now(),
            duration_seconds=duration,
            report_type=report_type,
            device_id=report_data.get("device_id", "unknown"),
            title=str(parsed.get("title", "MED-THERM-2026 Compliance Report")),
            sections=sections,
            executive_summary=str(parsed.get("executive_summary", "")),
            recommendations=str(parsed.get("recommendations", "")),
            conclusion=str(parsed.get("conclusion", "")),
            raw_response=response
        )
    
    async def extract_rules(
        self,
        document_text: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        if not settings.ai_enabled:
            raise AIValidationError(
                "AI analysis is not enabled. Set MODELARK_API_KEY environment variable."
            )
        
        start_time = datetime.now()
        
        user_prompt = USER_PROMPT_RULE_EXTRACTION_TEMPLATE.format(
            document_text=document_text,
            filename=filename or "unknown-document"
        )
        
        response = await self.client.analyze_text(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_RULE_EXTRACTION
        )
        
        content = self._extract_response_content(response)
        rules_data = ModelArkClient.parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        rules_list = []
        if isinstance(rules_data, list):
            rules_list = rules_data
        elif isinstance(rules_data, dict):
            possible_keys = ["rules", "extracted_rules", "result", "data"]
            for key in possible_keys:
                if key in rules_data and isinstance(rules_data[key], list):
                    rules_list = rules_data[key]
                    break
        
        if rules_list:
            avg_confidence = sum(
                r.get("confidence", 0.5) for r in rules_list if isinstance(r, dict)
            ) / len(rules_list)
        else:
            avg_confidence = 0.0
        
        return {
            "success": True,
            "rules": rules_list,
            "meta": {
                "extracted_at": datetime.now(),
                "model_used": settings.model_text_analysis,
                "average_confidence": round(avg_confidence, 2),
                "rule_count": len(rules_list),
                "filename": filename,
                "ruleset_name": filename or "Custom Rules",
                "source": "extracted",
            },
            "raw_response": response,
            "duration_seconds": duration
        }
    
    def _extract_response_content(self, response: Dict[str, Any]) -> str:
        try:
            choices = response.get('choices', [])
            if not choices:
                return '{}'
            
            message = choices[0].get('message', {})
            content = message.get('content', '{}')
            
            return content
        except (KeyError, IndexError, TypeError):
            return '{}'
    
    def _summarize_logs(self, logs: List[Any]) -> str:
        if not logs:
            return "No log entries provided."
        
        type_counts = defaultdict(int)
        timestamps = []
        
        for log in logs:
            if hasattr(log, 'log_type'):
                type_counts[str(log.log_type)] += 1
            elif isinstance(log, dict):
                log_type = log.get('log_type', log.get('log_type'))
                if log_type:
                    type_counts[str(log_type)] += 1
            
            ts = None
            if hasattr(log, 'timestamp'):
                ts = log.timestamp
            elif isinstance(log, dict):
                ts = log.get('timestamp')
            if ts:
                timestamps.append(ts)
        
        summary_parts = []
        summary_parts.append(f"Total log entries: {len(logs)}")
        
        if timestamps:
            try:
                min_ts = min(timestamps)
                max_ts = max(timestamps)
                summary_parts.append(f"Time range: {min_ts} to {max_ts}")
            except (TypeError, ValueError):
                pass
        
        if type_counts:
            summary_parts.append("Log types present:")
            for log_type, count in sorted(type_counts.items()):
                summary_parts.append(f"  - {log_type}: {count} entries")
        
        return "\n".join(summary_parts)
    
    def _summarize_findings(self, findings: List[Any]) -> str:
        if not findings:
            return "No regulatory findings provided."
        
        passed_count = 0
        failed_count = 0
        critical_count = 0
        high_count = 0
        
        finding_details = []
        
        for finding in findings:
            passed = None
            severity = None
            rule_id = None
            message = None
            
            if hasattr(finding, 'passed'):
                passed = finding.passed
            elif isinstance(finding, dict):
                passed = finding.get('passed')
            
            if passed:
                passed_count += 1
            else:
                failed_count += 1
            
            if hasattr(finding, 'severity'):
                severity = str(finding.severity)
            elif isinstance(finding, dict):
                severity = finding.get('severity', '')
            
            severity_str = str(severity).lower() if severity else ''
            if severity_str == 'critical':
                critical_count += 1
            elif severity_str == 'high':
                high_count += 1
            
            if hasattr(finding, 'rule_id'):
                rule_id = finding.rule_id
            elif isinstance(finding, dict):
                rule_id = finding.get('rule_id')
            
            if hasattr(finding, 'message'):
                message = finding.message
            elif isinstance(finding, dict):
                message = finding.get('message')
            
            if rule_id and not passed:
                finding_details.append(f"  - {rule_id}: {message[:100] if message else ''}...")
        
        summary_parts = []
        summary_parts.append(f"Total findings: {len(findings)}")
        summary_parts.append(f"Passed: {passed_count}")
        summary_parts.append(f"Failed: {failed_count}")
        summary_parts.append(f"Critical severity: {critical_count}")
        summary_parts.append(f"High severity: {high_count}")
        
        if finding_details and len(finding_details) <= 10:
            summary_parts.append("\nFailed rules:")
            summary_parts.extend(finding_details[:10])
        
        return "\n".join(summary_parts)
    
    def _extract_report_data(self, compliance_report: Any) -> Dict[str, Any]:
        data = {
            "device_id": "unknown",
            "total_entries": 0,
            "time_range_start": "N/A",
            "time_range_end": "N/A",
            "passed_count": 0,
            "failed_count": 0,
            "critical_count": 0
        }
        
        if hasattr(compliance_report, 'device_id'):
            data["device_id"] = str(compliance_report.device_id)
        elif isinstance(compliance_report, dict):
            data["device_id"] = str(compliance_report.get("device_id", "unknown"))
        
        if hasattr(compliance_report, 'total_entries'):
            data["total_entries"] = compliance_report.total_entries
        elif isinstance(compliance_report, dict):
            data["total_entries"] = compliance_report.get("total_entries", 0)
        
        if hasattr(compliance_report, 'time_range_start') and compliance_report.time_range_start:
            data["time_range_start"] = str(compliance_report.time_range_start)
        elif isinstance(compliance_report, dict) and compliance_report.get("time_range_start"):
            data["time_range_start"] = str(compliance_report.get("time_range_start"))
        
        if hasattr(compliance_report, 'time_range_end') and compliance_report.time_range_end:
            data["time_range_end"] = str(compliance_report.time_range_end)
        elif isinstance(compliance_report, dict) and compliance_report.get("time_range_end"):
            data["time_range_end"] = str(compliance_report.get("time_range_end"))
        
        if hasattr(compliance_report, 'passed_count'):
            data["passed_count"] = compliance_report.passed_count
        elif isinstance(compliance_report, dict):
            data["passed_count"] = compliance_report.get("passed_count", 0)
        
        if hasattr(compliance_report, 'failed_count'):
            data["failed_count"] = compliance_report.failed_count
        elif isinstance(compliance_report, dict):
            data["failed_count"] = compliance_report.get("failed_count", 0)
        
        if hasattr(compliance_report, 'critical_count'):
            data["critical_count"] = compliance_report.critical_count
        elif isinstance(compliance_report, dict):
            data["critical_count"] = compliance_report.get("critical_count", 0)
        
        return data
    
    def _format_category_breakdown(self, summary: Dict[str, Any]) -> str:
        if not summary:
            return "No category breakdown available."
        
        lines = []
        for category, cat_summary in summary.items():
            if isinstance(cat_summary, dict):
                passed = cat_summary.get('passed', 0)
                failed = cat_summary.get('failed', 0)
                total = cat_summary.get('total', passed + failed)
                lines.append(f"  - {category}: {passed} passed, {failed} failed of {total}")
        
        return "\n".join(lines) if lines else "No category breakdown available."
    
    def _format_key_findings(self, findings: List[Any]) -> str:
        if not findings:
            return "No key findings."
        
        lines = []
        critical_count = 0
        
        for finding in findings:
            severity = None
            rule_id = None
            message = None
            passed = None
            
            if hasattr(finding, 'severity'):
                severity = str(finding.severity).lower()
            elif isinstance(finding, dict):
                severity = str(finding.get('severity', '')).lower()
            
            if severity == 'critical':
                critical_count += 1
                
                if hasattr(finding, 'rule_id'):
                    rule_id = finding.rule_id
                elif isinstance(finding, dict):
                    rule_id = finding.get('rule_id')
                
                if hasattr(finding, 'message'):
                    message = finding.message
                elif isinstance(finding, dict):
                    message = finding.get('message')
                
                if rule_id and message:
                    lines.append(f"  - CRITICAL [{rule_id}]: {message[:150]}...")
        
        if lines:
            return "\n".join(lines[:5])
        return "No critical findings."

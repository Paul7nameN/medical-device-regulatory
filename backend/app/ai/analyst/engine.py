from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import logging

from app.config import settings
from app.ai.client import ModelArkClient, AIError, AIValidationError, AIAPIError
from app.ai.analyst.models import (
    RiskOverview,
    Insight,
    InsightRiskFactor,
    Prediction,
    ActionItem,
    ActionPlan,
    AIAnalysisResult,
    Thresholds,
    DEFAULT_THRESHOLDS,
)
from app.ai.analyst.context_builder import (
    build_analysis_context,
    build_context_from_logs,
    build_context_from_chart,
)
from app.ai.analyst.prompts import (
    SYSTEM_PROMPT_AI_ANALYSIS,
    SYSTEM_PROMPT_CHAT,
    build_ai_analysis_prompt,
)
from app.models.logs import LogEntry
from app.models.findings import ComplianceReport
from app.ai.image.models import ChartAnalysisResult

logger = logging.getLogger(__name__)


class AIAnalystEngine:
    def __init__(
        self,
        client: Optional[ModelArkClient] = None,
        thresholds: Thresholds = DEFAULT_THRESHOLDS,
    ):
        self.client = client or ModelArkClient()
        self.thresholds = thresholds
        self._enabled = settings.ai_enabled
    
    async def analyze_logs(
        self,
        logs: List[LogEntry],
        report: Optional[ComplianceReport] = None,
    ) -> Optional[AIAnalysisResult]:
        if not self._enabled:
            logger.warning("AI analysis skipped: AI not enabled")
            return None
        
        try:
            context = build_context_from_logs(logs, report, self.thresholds)
            return await self._analyze_with_context(context)
        except Exception as e:
            logger.error(f"AI log analysis failed: {e}", exc_info=True)
            return None
    
    async def analyze_chart(
        self,
        chart_result: ChartAnalysisResult,
        report: Optional[ComplianceReport] = None,
    ) -> Optional[AIAnalysisResult]:
        if not self._enabled:
            logger.warning("AI analysis skipped: AI not enabled")
            return None
        
        try:
            context = build_context_from_chart(chart_result, report, self.thresholds)
            return await self._analyze_with_context(context)
        except Exception as e:
            logger.error(f"AI chart analysis failed: {e}", exc_info=True)
            return None
    
    async def chat(
        self,
        message: str,
        ai_analysis: Optional[Any] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        if not self._enabled:
            return "AI analysis is not enabled. Please configure MODELARK_API_KEY."
        
        messages = []
        
        messages.append({"role": "system", "content": SYSTEM_PROMPT_CHAT})
        
        if chat_history:
            for msg in chat_history:
                if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        context_content = ""
        if ai_analysis is not None:
            if isinstance(ai_analysis, dict):
                parsed = self._parse_ai_response(ai_analysis)
                if parsed:
                    context_content = self._format_analysis_for_chat(parsed)
            elif isinstance(ai_analysis, AIAnalysisResult):
                context_content = self._format_analysis_for_chat(ai_analysis)
        
        user_message = message
        if context_content:
            user_message = f"Context from current analysis:\n{context_content}\n\nUser question: {message}"
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat_completion(
                messages=messages,
                model=self.client.model_text,
                temperature=0.7,
                max_tokens=1024,
            )
            
            content = self._extract_response_content(response)
            return content
        
        except AIError as e:
            logger.error(f"AI chat failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def _analyze_with_context(
        self,
        context: Dict[str, Any],
    ) -> Optional[AIAnalysisResult]:
        user_prompt = build_ai_analysis_prompt(context)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_AI_ANALYSIS},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            for attempt in range(3):
                try:
                    response = await self.client.chat_completion(
                        messages=messages,
                        model=self.client.model_text,
                        temperature=0.1,
                        max_tokens=4096,
                        response_format={"type": "json_object"},
                    )
                    
                    content = self._extract_response_content(response)
                    parsed = ModelArkClient.parse_json_response(content)
                    
                    result = self._parse_ai_response(parsed)
                    if result:
                        result.model_used = settings.model_text_analysis
                        return result
                    
                except Exception as e:
                    if attempt == 2:
                        raise
                    logger.warning(f"AI analysis attempt {attempt + 1} failed: {e}, retrying...")
                    messages.append({
                        "role": "user",
                        "content": "Please return ONLY a valid JSON object matching the schema. Ensure all required fields are present and valid."
                    })
            
            return None
            
        except AIError as e:
            logger.error(f"AI analysis API error: {e}")
            return None
        except Exception as e:
            logger.error(f"AI analysis failed unexpectedly: {e}", exc_info=True)
            return None
    
    def _extract_response_content(self, response: Dict[str, Any]) -> str:
        try:
            choices = response.get('choices', [])
            if not choices:
                return '{}'
            
            message = choices[0].get('message', {}) if hasattr(choices[0], 'get') else choices[0]
            if isinstance(message, dict):
                content = message.get('content', '{}')
            else:
                content = getattr(message, 'content', '{}')
            
            return content if content else '{}'
        except (KeyError, IndexError, TypeError):
            return '{}'
    
    def _parse_ai_response(self, data: Dict[str, Any]) -> Optional[AIAnalysisResult]:
        try:
            risk_overview_data = data.get('session_risk_overview', {})
            risk_overview = RiskOverview(
                overall_risk_score=float(risk_overview_data.get('overall_risk_score', 0.5)),
                risk_level=risk_overview_data.get('risk_level', 'low'),
                primary_risk_category=risk_overview_data.get('primary_risk_category', 'unknown'),
                imminent_concerns_count=int(risk_overview_data.get('imminent_concerns_count', 0)),
                trend_indicator=risk_overview_data.get('trend_indicator', 'stable'),
            )
            
            insights_data = data.get('insights', [])
            insights = []
            for idx, ins_data in enumerate(insights_data):
                risk_factors = []
                for rf in ins_data.get('risk_factors', []):
                    if isinstance(rf, dict):
                        risk_factors.append(InsightRiskFactor(
                            factor=rf.get('factor', ''),
                            severity=rf.get('severity', 'medium'),
                        ))
                
                insights.append(Insight(
                    id=ins_data.get('id', f'insight_{idx + 1}'),
                    priority=ins_data.get('priority', 'low'),
                    category=ins_data.get('category', 'unknown'),
                    title=ins_data.get('title', ''),
                    evidence=[str(e) for e in ins_data.get('evidence', [])],
                    why_matters=ins_data.get('why_matters', ''),
                    risk_score_contribution=float(ins_data.get('risk_score_contribution', 0.0)),
                    risk_factors=risk_factors,
                ))
            
            predictions_data = data.get('predictions', [])
            predictions = []
            for idx, pred_data in enumerate(predictions_data):
                predictions.append(Prediction(
                    id=pred_data.get('id', f'pred_{idx + 1}'),
                    scenario=pred_data.get('scenario', ''),
                    confidence=float(pred_data.get('confidence', 0.5)),
                    timeframe=pred_data.get('timeframe', ''),
                    estimated_probability=pred_data.get('estimated_probability', ''),
                    risk_factors_driving_this=[str(f) for f in pred_data.get('risk_factors_driving_this', [])],
                    mitigation_potential=pred_data.get('mitigation_potential'),
                    why_concerning=pred_data.get('why_concerning'),
                ))
            
            action_plan_data = data.get('action_plan', {})
            
            def parse_action_items(items_data: List[Dict]) -> List[ActionItem]:
                items = []
                for item_data in items_data:
                    items.append(ActionItem(
                        action=item_data.get('action', ''),
                        priority=item_data.get('priority', 'medium'),
                        steps=[str(s) for s in item_data.get('steps', [])] if item_data.get('steps') else None,
                        why_needed=item_data.get('why_needed'),
                        rationale=item_data.get('rationale'),
                    ))
                return items
            
            action_plan = ActionPlan(
                summary=action_plan_data.get('summary', ''),
                immediate_actions_0_1h=parse_action_items(action_plan_data.get('immediate_actions_0_1h', [])),
                short_term_24h=parse_action_items(action_plan_data.get('short_term_24h', [])),
                long_term_maintenance=parse_action_items(action_plan_data.get('long_term_maintenance', [])),
            )
            
            natural_language_summary = data.get('natural_language_summary', '')
            
            return AIAnalysisResult(
                session_risk_overview=risk_overview,
                insights=insights,
                predictions=predictions,
                action_plan=action_plan,
                natural_language_summary=natural_language_summary,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}", exc_info=True)
            return None
    
    def _format_analysis_for_chat(self, analysis: AIAnalysisResult) -> str:
        lines = []
        
        lines.append("=== CURRENT ANALYSIS SUMMARY ===")
        lines.append(f"Risk Level: {analysis.session_risk_overview.risk_level}")
        lines.append(f"Overall Score: {analysis.session_risk_overview.overall_risk_score}")
        lines.append(f"Trend: {analysis.session_risk_overview.trend_indicator}")
        lines.append("")
        
        if analysis.insights:
            lines.append("=== KEY INSIGHTS ===")
            for idx, ins in enumerate(analysis.insights[:5], 1):
                lines.append(f"{idx}. [{ins.priority.upper()}] {ins.title}")
                lines.append(f"   Why: {ins.why_matters}")
                if ins.evidence:
                    lines.append(f"   Evidence: {', '.join(ins.evidence[:2])}")
                lines.append("")
        
        if analysis.predictions:
            lines.append("=== PREDICTIONS ===")
            for pred in analysis.predictions[:3]:
                lines.append(f"- {pred.scenario}")
                lines.append(f"  Confidence: {pred.estimated_probability} ({pred.confidence*100:.0f}%)")
                lines.append(f"  Timeframe: {pred.timeframe}")
                lines.append("")
        
        if analysis.action_plan.immediate_actions_0_1h:
            lines.append("=== IMMEDIATE ACTIONS (0-1h) ===")
            for action in analysis.action_plan.immediate_actions_0_1h[:3]:
                lines.append(f"- [{action.priority.upper()}] {action.action}")
                if action.why_needed:
                    lines.append(f"  Why: {action.why_needed}")
        
        lines.append(f"\n=== NATURAL SUMMARY ===\n{analysis.natural_language_summary}")
        
        return "\n".join(lines)

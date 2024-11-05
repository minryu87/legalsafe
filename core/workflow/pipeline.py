# core/workflow/pipeline.py

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging
from enum import Enum
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.workflow.coordinator import AgentCoordinator, WorkflowState
from config.azure_config import MODEL_CONFIG

class PipelineStatus(Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStage(Enum):
    INPUT_VALIDATION = "input_validation"
    AGENT_PROCESSING = "agent_processing"
    RESULT_COMPILATION = "result_compilation"
    REPORT_GENERATION = "report_generation"

class LegalAnalysisPipeline:
    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.status = PipelineStatus.READY
        self.current_stage = None
        self.start_time = None
        self.end_time = None
        self.execution_history = []
        self.feedback_queue = []
        
        self.setup_logging()

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LegalAnalysisPipeline')

    async def process_case(self, case_data: Dict, 
                         user_preferences: Optional[Dict] = None) -> Dict:
        """케이스 처리 메인 파이프라인"""
        try:
            self.start_time = datetime.now()
            self.status = PipelineStatus.RUNNING
            self.log_pipeline_event("Starting case processing")

            # 1. 입력 데이터 검증
            if not await self._validate_input(case_data):
                raise ValueError("Invalid input data")

            # 2. 사용자 설정 적용
            processed_data = self._apply_user_preferences(case_data, user_preferences)

            # 3. 에이전트 처리 실행
            self.current_stage = ProcessingStage.AGENT_PROCESSING
            processing_result = await self.coordinator.process_case(processed_data)

            # 4. 결과 컴파일
            self.current_stage = ProcessingStage.RESULT_COMPILATION
            compiled_result = await self._compile_results(processing_result)

            # 5. 최종 보고서 생성
            self.current_stage = ProcessingStage.REPORT_GENERATION
            final_report = await self._generate_report(compiled_result)

            self.status = PipelineStatus.COMPLETED
            self.end_time = datetime.now()
            self.log_pipeline_event("Case processing completed successfully")

            return final_report

        except Exception as e:
            self.status = PipelineStatus.FAILED
            self.log_pipeline_event(f"Pipeline failed: {str(e)}", "ERROR")
            raise

    async def _validate_input(self, case_data: Dict) -> bool:
        """입력 데이터 검증"""
        self.current_stage = ProcessingStage.INPUT_VALIDATION
        required_fields = [
            "case_type",
            "parties_info",
            "case_summary",
            "legal_issues"
        ]

        # 필수 필드 확인
        if not all(field in case_data for field in required_fields):
            self.log_pipeline_event("Missing required fields in input data", "ERROR")
            return False

        # 데이터 형식 검증
        try:
            if not isinstance(case_data["legal_issues"], list):
                raise ValueError("legal_issues must be a list")
            
            if not isinstance(case_data["parties_info"], dict):
                raise ValueError("parties_info must be a dictionary")

            # 당사자 정보 검증
            required_party_info = ["role", "brief"]
            for party in ["our_side", "opposing_side"]:
                if not all(field in case_data["parties_info"][party] 
                          for field in required_party_info):
                    raise ValueError(f"Missing required fields in {party} information")

            return True

        except Exception as e:
            self.log_pipeline_event(f"Input validation failed: {str(e)}", "ERROR")
            return False

    def _apply_user_preferences(self, case_data: Dict, 
                              user_preferences: Optional[Dict]) -> Dict:
        """사용자 설정 적용"""
        if not user_preferences:
            return case_data

        processed_data = case_data.copy()
        
        # 분석 우선순위 적용
        if "priority_issues" in user_preferences:
            self._prioritize_issues(processed_data, user_preferences["priority_issues"])

        # 특별 고려사항 추가
        if "special_considerations" in user_preferences:
            processed_data["special_considerations"] = user_preferences["special_considerations"]

        # 시간 제약 설정
        if "time_constraints" in user_preferences:
            processed_data["time_constraints"] = user_preferences["time_constraints"]

        return processed_data

    async def _compile_results(self, processing_result: Dict) -> Dict:
        """결과 컴파일"""
        try:
            compiled_result = {
                "summary": {
                    "case_overview": processing_result["case_analysis"]["summary"],
                    "key_findings": processing_result["precedent_research"]["key_findings"],
                    "strategic_approach": processing_result["legal_strategy"]["overall_strategy"]
                },
                "detailed_analysis": {
                    "legal_issues": processing_result["case_analysis"]["key_issues"],
                    "precedent_analysis": processing_result["precedent_research"]["precedent_analysis"],
                    "strategy": processing_result["legal_strategy"]["issue_specific_strategies"]
                },
                "recommendations": {
                    "evidence_strategy": processing_result["legal_strategy"]["evidence_strategy"],
                    "timeline": processing_result["legal_strategy"]["litigation_timeline"],
                    "risk_management": self._extract_risk_management(processing_result)
                },
                "metadata": {
                    "processing_time": {
                        "start": self.start_time.isoformat(),
                        "end": datetime.now().isoformat()
                    },
                    "workflow_status": self.coordinator.get_current_state()
                }
            }
            return compiled_result

        except Exception as e:
            self.log_pipeline_event(f"Error compiling results: {str(e)}", "ERROR")
            raise

    async def _generate_report(self, compiled_result: Dict) -> Dict:
        """최종 보고서 생성"""
        try:
            return {
                "report": {
                    "executive_summary": self._create_executive_summary(compiled_result),
                    "detailed_analysis": self._create_detailed_analysis(compiled_result),
                    "strategic_recommendations": self._create_strategic_recommendations(compiled_result),
                    "appendices": self._create_appendices(compiled_result)
                },
                "metadata": {
                    "generated_at": datetime.now().isoformat(),  # 생성 시간 추가
                    "processing_time": compiled_result.get("metadata", {}).get("processing_time", {}),
                    "workflow_status": compiled_result.get("metadata", {}).get("workflow_status", {}),
                    "version": "1.0.0"
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise

    def _create_executive_summary(self, compiled_result: Dict) -> Dict:
        """핵심 요약 생성"""
        return {
            "case_overview": compiled_result["summary"]["case_overview"],
            "key_findings": self._summarize_key_findings(compiled_result),
            "strategic_approach": compiled_result["summary"]["strategic_approach"],
            "success_probability": self._calculate_success_probability(compiled_result)
        }

    def _create_detailed_analysis(self, compiled_result: Dict) -> Dict:
        """상세 분석 생성"""
        return {
            "legal_issues_analysis": self._format_legal_issues(
                compiled_result["detailed_analysis"]["legal_issues"]
            ),
            "precedent_analysis": self._format_precedent_analysis(
                compiled_result["detailed_analysis"]["precedent_analysis"]
            ),
            "strategic_analysis": self._format_strategic_analysis(
                compiled_result["detailed_analysis"]["strategy"]
            )
        }

    def _create_strategic_recommendations(self, compiled_result: Dict) -> Dict:
        """전략적 권고사항 생성"""
        return {
            "evidence_strategy": compiled_result["recommendations"]["evidence_strategy"],
            "action_timeline": self._create_action_timeline(
                compiled_result["recommendations"]["timeline"]
            ),
            "risk_management": compiled_result["recommendations"]["risk_management"]
        }

    def log_pipeline_event(self, message: str, level: str = "INFO"):
        """파이프라인 이벤트 로깅"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "stage": self.current_stage.value if self.current_stage else None,
            "status": self.status.value,
            "level": level,
            "message": message
        }
        self.execution_history.append(event)
        
        if level == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def get_progress(self) -> Dict:
        """진행 상황 반환"""
        return {
            "status": self.status.value,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "execution_history": self.execution_history,
            "coordinator_state": self.coordinator.get_current_state()
        }

    def pause(self) -> bool:
        """파이프라인 일시 중지"""
        if self.status == PipelineStatus.RUNNING:
            self.status = PipelineStatus.PAUSED
            self.log_pipeline_event("Pipeline paused")
            return True
        return False

    def resume(self) -> bool:
        """파이프라인 재개"""
        if self.status == PipelineStatus.PAUSED:
            self.status = PipelineStatus.RUNNING
            self.log_pipeline_event("Pipeline resumed")
            return True
        return False

    def _summarize_key_findings(self, compiled_result: Dict) -> Dict:
        """주요 발견사항 요약"""
        try:
            return {
                "main_points": compiled_result.get("detailed_analysis", {})
                            .get("legal_issues", []),
                "strengths": [
                    issue.get("description", "")
                    for issue in compiled_result.get("detailed_analysis", {})
                    .get("legal_issues", [])
                    if "strength" in issue.get("issue", "").lower()
                ],
                "weaknesses": [
                    issue.get("description", "")
                    for issue in compiled_result.get("detailed_analysis", {})
                    .get("legal_issues", [])
                    if "weakness" in issue.get("issue", "").lower()
                ]
            }
        except Exception as e:
            self.logger.error(f"Error summarizing key findings: {str(e)}")
            return {
                "main_points": [],
                "strengths": [],
                "weaknesses": []
            }

    def _calculate_success_probability(self, compiled_result: Dict) -> Dict:
        """승소 가능성 계산"""
        try:
            strengths = len([
                issue for issue in compiled_result.get("detailed_analysis", {})
                .get("legal_issues", [])
                if "strength" in issue.get("issue", "").lower()
            ])
            
            weaknesses = len([
                issue for issue in compiled_result.get("detailed_analysis", {})
                .get("legal_issues", [])
                if "weakness" in issue.get("issue", "").lower()
            ])
            
            total = max(strengths + weaknesses, 1)  # 0으로 나누기 방지
            probability = strengths / total * 100
            
            return {
                "probability": round(probability, 2),
                "confidence_level": "high" if probability > 70 else "medium" if probability > 40 else "low",
                "key_factors": [
                    factor.get("description", "")
                    for factor in compiled_result.get("detailed_analysis", {})
                    .get("legal_issues", [])
                    if factor.get("impact", "").lower() in ["high", "critical"]
                ]
            }
        except Exception as e:
            self.logger.error(f"Error calculating success probability: {str(e)}")
            return {
                "probability": 0.0,
                "confidence_level": "unknown",
                "key_factors": []
            }

    def _extract_risk_management(self, processing_result: Dict) -> Dict:
        """위험 관리 정보 추출"""
        try:
            return {
                "legal_risks": [
                    {
                        "risk": risk,
                        "severity": "high",
                        "mitigation": "법적 대응 방안 수립"
                    }
                    for risk in processing_result.get("case_analysis", {})
                    .get("legal_analysis", {})
                    .get("potential_challenges", [])
                ],
                "procedural_risks": [
                    {
                        "risk": risk,
                        "severity": "medium",
                        "mitigation": "절차적 대응 방안 수립"
                    }
                    for risk in processing_result.get("case_analysis", {})
                    .get("evidence_requirements", {})
                    .get("potential_difficulties", [])
                ],
                "mitigation_strategies": [
                    {
                        "strategy": strategy,
                        "target_risk": "legal",
                        "priority": "high"
                    }
                    for strategy in processing_result.get("legal_strategy", {})
                    .get("overall_strategy", "").split(". ")
                    if strategy
                ]
            }
        except Exception as e:
            self.logger.error(f"Error extracting risk management info: {str(e)}")
            return {
                "legal_risks": [],
                "procedural_risks": [],
                "mitigation_strategies": []
            }
        
    def _format_legal_issues(self, issues: List[Dict]) -> List[Dict]:
        """법적 쟁점 포맷팅"""
        try:
            return [
                {
                    "issue": issue.get("issue", ""),
                    "description": issue.get("description", ""),
                    "relevant_laws": issue.get("relevant_laws", []),
                    "analysis": issue.get("analysis", ""),
                    "required_evidence": issue.get("required_evidence", [])
                }
                for issue in issues
            ]
        except Exception as e:
            self.logger.error(f"Error formatting legal issues: {str(e)}")
            return []

    def _format_precedent_analysis(self, precedents: List[Dict]) -> List[Dict]:
        """판례 분석 포맷팅"""
        try:
            return [
                {
                    "reference": precedent.get("reference", ""),
                    "relevance": precedent.get("relevance", ""),
                    "key_points": precedent.get("key_points", []),
                    "impact": precedent.get("impact", "")
                }
                for precedent in precedents
            ]
        except Exception as e:
            self.logger.error(f"Error formatting precedent analysis: {str(e)}")
            return []

    def _format_strategic_analysis(self, strategy: Any) -> Dict:
        """전략 분석 포맷팅"""
        try:
            if isinstance(strategy, dict):
                return {
                    "approach": strategy.get("approach", ""),
                    "objectives": strategy.get("objectives", []),
                    "action_items": strategy.get("action_items", []),
                    "timeline": strategy.get("timeline", {})
                }
            elif isinstance(strategy, list):
                return {
                    "approach": "",
                    "objectives": strategy,
                    "action_items": [],
                    "timeline": {}
                }
            else:
                return {
                    "approach": "",
                    "objectives": [],
                    "action_items": [],
                    "timeline": {}
                }
        except Exception as e:
            self.logger.error(f"Error formatting strategic analysis: {str(e)}")
            return {
                "approach": "",
                "objectives": [],
                "action_items": [],
                "timeline": {}
            }

    def _create_action_timeline(self, timeline_data: Any) -> List[Dict]:
        """실행 타임라인 생성"""
        try:
            if isinstance(timeline_data, dict):
                return [
                    {
                        "phase": phase,
                        "actions": actions,
                        "deadline": deadline
                    }
                    for phase, actions, deadline in timeline_data.get("phases", [])
                ]
            elif isinstance(timeline_data, list):
                return [
                    {
                        "phase": f"Phase {i+1}",
                        "actions": [action],
                        "deadline": "TBD"
                    }
                    for i, action in enumerate(timeline_data)
                ]
            return []
        except Exception as e:
            self.logger.error(f"Error creating action timeline: {str(e)}")
            return []
        
    def _create_appendices(self, compiled_result: Dict) -> Dict:
        """부록 생성"""
        try:
            return {
                "referenced_laws": self._extract_referenced_laws(compiled_result),
                "evidence_list": self._extract_evidence_list(compiled_result),
                "methodology": self._create_methodology_description()
            }
        except Exception as e:
            self.logger.error(f"Error creating appendices: {str(e)}")
            return {}

    def _extract_referenced_laws(self, compiled_result: Dict) -> List[str]:
        """참조된 법령 추출"""
        try:
            laws = set()
            for issue in compiled_result.get("detailed_analysis", {}).get("legal_issues", []):
                laws.update(issue.get("relevant_laws", []))
            return list(laws)
        except Exception as e:
            self.logger.error(f"Error extracting referenced laws: {str(e)}")
            return []

    def _extract_evidence_list(self, compiled_result: Dict) -> List[Dict]:
        """증거 목록 추출"""
        try:
            return compiled_result.get("recommendations", {}).get("evidence_strategy", {}).get("evidence_list", [])
        except Exception as e:
            self.logger.error(f"Error extracting evidence list: {str(e)}")
            return []

    def _create_methodology_description(self) -> Dict:
        """방법론 설명 생성"""
        return {
            "approach": "법률 분석 AI 시스템을 활용한 체계적 접근",
            "steps": [
                "사건 분석 및 쟁점 도출",
                "관련 법령 및 판례 검토",
                "증거 분석 및 평가",
                "전략 수립 및 권고사항 도출"
            ],
            "tools": [
                "법률 분석 AI",
                "판례 데이터베이스",
                "증거 평가 프레임워크"
            ]
        }
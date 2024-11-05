# core/agents/strategist.py

from typing import Dict, List
from datetime import datetime
from .base import BaseAgent, AgentRole

class LegalStrategist(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.STRATEGIST, "Legal Strategist")

    def prepare_system_prompt(self) -> str:
        return """당신은 법률 전략 수립 전문가입니다.
        사건 분석과 판례 연구 결과를 바탕으로 효과적인 법적 전략을 수립하는 것이 주요 업무입니다.

        다음 사항들을 중점적으로 고려하여 전략을 수립해주세요(한글로 제공하세요):
        1. 승소 가능성 극대화를 위한 주장 구성
        2. 예상되는 상대방 주장에 대한 대응 방안
        3. 증거 수집 및 제출 전략
        4. 소송 진행 단계별 대응 전략
        
        특히 다음 사항에 유의하세요:
        - 각 주장의 법적 근거 명확화
        - 증거 관련 현실적 제약 고려
        - 시간적 제약사항 고려
        - 비용 대비 효과성 검토
        - 전략의 실현 가능성 검토"""

    def prepare_user_prompt(self, input_data: Dict) -> str:
        case_analysis = input_data.get('case_analysis', {})
        precedent_research = input_data.get('precedent_research', {})
        
        # 분석 결과 포맷팅
        legal_issues = "\n".join([
            f"- 쟁점 {i+1}: {issue.get('issue', '')}\n  "
            f"주요 판례: {', '.join(issue.get('key_precedents', []))}"
            for i, issue in enumerate(case_analysis.get('legal_issues', []))
        ])

        evidence_status = case_analysis.get('evidence_status', {})
        existing_evidence = "\n".join(evidence_status.get('existing_evidence', []))
        potential_evidence = "\n".join(evidence_status.get('potential_evidence', []))

        return f"""다음 분석 결과를 바탕으로 법적 전략을 수립해주세요(한글로 제공하세요):

                    주요 법적 쟁점:
                    {legal_issues}

                    현재 확보한 증거:
                    {existing_evidence}

                    향후 확보 가능한 증거:
                    {potential_evidence}

                    다음 항목들에 대한 전략을 수립해주세요:
                    1. 각 쟁점별 주장 전개 방안
                    2. 증거 수집 및 제출 전략
                    3. 예상되는 상대방 주장과 대응 방안
                    4. 소송 진행 단계별 전략
                    5. 예상되는 위험요소와 대비책"""

    def get_output_format(self) -> Dict:
        return {
            "overall_strategy": {
                "main_approach": "string",
                "key_objectives": ["string"],
                "critical_success_factors": ["string"]
            },
            "issue_specific_strategies": [
                {
                    "issue": "string",
                    "arguments": {
                        "main_points": ["string"],
                        "legal_basis": ["string"],
                        "supporting_evidence": ["string"]
                    },
                    "counter_arguments": {
                        "expected_points": ["string"],
                        "rebuttals": ["string"],
                        "required_evidence": ["string"]
                    },
                    "risk_assessment": {
                        "potential_risks": ["string"],
                        "mitigation_plans": ["string"]
                    }
                }
            ],
            "evidence_strategy": {
                "existing_evidence": {
                    "usage_plan": ["string"],
                    "presentation_timing": "string"
                },
                "required_evidence": {
                    "priority_list": ["string"],
                    "collection_methods": ["string"],
                    "deadlines": ["string"]
                },
                "contingency_plans": ["string"]
            },
            "litigation_timeline": {
                "pre_trial": {
                    "key_actions": ["string"],
                    "deadlines": ["string"]
                },
                "trial": {
                    "key_arguments": ["string"],
                    "evidence_presentation": ["string"]
                },
                "post_trial": {
                    "contingency_plans": ["string"]
                }
            },
            "success_probability": {
                "assessment": "string",
                "key_factors": ["string"],
                "improvement_suggestions": ["string"]
            }
        }

    def validate_response(self, response: Dict) -> bool:
        """응답 유효성 검증"""
        required_keys = [
            "overall_strategy",
            "issue_specific_strategies",
            "evidence_strategy",
            "litigation_timeline",
            "success_probability"
        ]
        
        # 필수 키 존재 확인
        if not all(key in response for key in required_keys):
            return False

        # overall_strategy 검증
        if not all(key in response["overall_strategy"] for key in ["main_approach", "key_objectives", "critical_success_factors"]):
            return False

        # issue_specific_strategies 검증
        if not response["issue_specific_strategies"] or not isinstance(response["issue_specific_strategies"], list):
            return False

        for strategy in response["issue_specific_strategies"]:
            required_strategy_keys = ["issue", "arguments", "counter_arguments", "risk_assessment"]
            if not all(key in strategy for key in required_strategy_keys):
                return False

        return True

    def format_output(self, response: Dict) -> Dict:
        """출력 형식 정리"""
        formatted_response = {
            "summary": {
                "strategy_date": datetime.now().isoformat(),
                "total_issues": len(response["issue_specific_strategies"]),
                "key_strategy_points": response["overall_strategy"]["key_objectives"],
                "critical_timeline": {
                    phase: timeline["key_actions"][0] if timeline.get("key_actions") else "Not specified"
                    for phase, timeline in response["litigation_timeline"].items()
                }
            },
            "detailed_strategy": response,
            "immediate_actions": {
                "priority_tasks": [
                    task for task in response["evidence_strategy"]["required_evidence"]["priority_list"][:3]
                ],
                "key_deadlines": response["litigation_timeline"]["pre_trial"]["deadlines"]
            },
            "risk_management": {
                "high_priority_risks": [
                    strategy["risk_assessment"]["potential_risks"][0]
                    for strategy in response["issue_specific_strategies"]
                    if strategy["risk_assessment"]["potential_risks"]
                ],
                "mitigation_strategies": [
                    strategy["risk_assessment"]["mitigation_plans"][0]
                    for strategy in response["issue_specific_strategies"]
                    if strategy["risk_assessment"]["mitigation_plans"]
                ]
            }
        }
        
        return formatted_response

    def analyze_strategy_feasibility(self, strategy: Dict) -> Dict:
        """전략의 실현 가능성 분석"""
        feasibility_analysis = {
            "timeline_feasibility": self._analyze_timeline_feasibility(strategy),
            "evidence_feasibility": self._analyze_evidence_feasibility(strategy),
            "resource_requirements": self._analyze_resource_requirements(strategy),
            "risk_assessment": self._analyze_risks(strategy)
        }
        return feasibility_analysis

    def _analyze_timeline_feasibility(self, strategy: Dict) -> Dict:
        """타임라인 실현 가능성 분석"""
        timeline = strategy["litigation_timeline"]
        return {
            "critical_deadlines": timeline["pre_trial"]["deadlines"],
            "potential_bottlenecks": [
                deadline for deadline in timeline["pre_trial"]["deadlines"]
                if self._is_tight_deadline(deadline)
            ]
        }

    def _analyze_evidence_feasibility(self, strategy: Dict) -> Dict:
        """증거 수집 가능성 분석"""
        evidence_strategy = strategy["evidence_strategy"]
        return {
            "high_priority_evidence": evidence_strategy["required_evidence"]["priority_list"],
            "collection_challenges": [
                method for method in evidence_strategy["required_evidence"]["collection_methods"]
                if self._has_collection_challenges(method)
            ]
        }

    def _analyze_resource_requirements(self, strategy: Dict) -> Dict:
        """필요 자원 분석"""
        return {
            "required_resources": [
                "Legal research resources",
                "Evidence collection resources",
                "Expert consultation resources"
            ],
            "estimated_timeline": "Required timeline based on strategy phases"
        }

    def _analyze_risks(self, strategy: Dict) -> Dict:
        """위험 요소 분석"""
        return {
            "high_priority_risks": [
                strategy["risk_assessment"]["potential_risks"]
                for strategy in strategy["issue_specific_strategies"]
            ],
            "mitigation_strategies": [
                strategy["risk_assessment"]["mitigation_plans"]
                for strategy in strategy["issue_specific_strategies"]
            ]
        }

    def _is_tight_deadline(self, deadline: str) -> bool:
        """타이트한 데드라인인지 확인"""
        # 실제 구현 시 날짜 비교 로직 추가
        return False

    def _has_collection_challenges(self, method: str) -> bool:
        """증거 수집의 어려움이 있는지 확인"""
        # 실제 구현 시 구체적인 판단 로직 추가
        return False
# core/agents/researcher.py

from typing import Dict, List
from datetime import datetime
from .base import BaseAgent, AgentRole

class PrecedentResearcher(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.RESEARCHER, "Precedent Researcher")

    def prepare_system_prompt(self) -> str:
        return """당신은 법률 판례 연구 전문가입니다. 
        주어진 사건의 쟁점과 관련된 판례들을 분석하고, 
        본 사건에 대한 시사점을 도출하는 것이 주요 업무입니다.

        다음 사항들을 중점적으로 분석해주세요(한글로 제공):
        1. 사실관계의 유사성 검토
        2. 법원의 판단 기준 분석
        3. 당사자들의 주장과 법원의 판단 근거 정리
        4. 본 사건에 대한 시사점 도출
        
        특히 다음 사항에 유의하세요:
        - 최신 판례를 우선적으로 검토
        - 상급심 판례의 우선 검토
        - 사실관계 유사성과 법리적 유사성을 구분하여 분석
        - 판례의 특수성과 일반 법리를 구분하여 분석"""

    def prepare_user_prompt(self, input_data: Dict) -> str:
        legal_issues = input_data.get('legal_issues', [])
        case_type = input_data.get('case_type', '')
        case_summary = input_data.get('case_summary', '')

        # 법적 쟁점 포맷팅
        issues_str = "\n".join([
            f"- 쟁점 {i+1}: {issue.get('issue', '')}\n  "
            f"관련 법령: {issue.get('relevant_law', '없음')}"
            for i, issue in enumerate(legal_issues)
        ])

        return f"""다음 사건의 관련 판례를 분석해주세요(한글로 제공):

                사건 종류: {case_type}

                사건 개요:
                {case_summary}

                주요 법적 쟁점:
                {issues_str}

                각 쟁점별로 다음 사항을 분석해주세요:
                1. 관련된 주요 판례들의 요지
                2. 판례에서 나타난 법원의 판단 기준
                3. 본 사건과의 유사점과 차이점
                4. 예상되는 법원의 판단 방향
                5. 특별히 참고해야 할 법리나 판시사항"""

    def get_output_format(self) -> Dict:
        return {
            "precedent_analysis": [
                {
                    "issue": "string",  # 관련 쟁점
                    "precedents": [
                        {
                            "case_number": "string",
                            "court": "string",
                            "date": "string",
                            "summary": "string",
                            "key_holdings": ["string"],
                            "similarity_analysis": {
                                "factual_similarity": "string",
                                "legal_similarity": "string",
                                "differences": ["string"]
                            }
                        }
                    ],
                    "legal_principles": ["string"],
                    "implications": "string"
                }
            ],
            "key_findings": {
                "favorable_precedents": ["string"],
                "unfavorable_precedents": ["string"],
                "distinguishing_factors": ["string"]
            },
            "strategic_implications": {
                "strengths": ["string"],
                "weaknesses": ["string"],
                "recommendations": ["string"]
            },
            "court_tendency": {
                "general_approach": "string",
                "key_considerations": ["string"],
                "likely_outcome": "string"
            }
        }

    def validate_response(self, response: Dict) -> bool:
        """응답 유효성 검증"""
        required_keys = [
            "precedent_analysis", 
            "key_findings",
            "strategic_implications",
            "court_tendency"
        ]
        
        # 필수 키 존재 확인
        if not all(key in response for key in required_keys):
            return False

        # precedent_analysis 검증
        if not response["precedent_analysis"] or not isinstance(response["precedent_analysis"], list):
            return False

        for analysis in response["precedent_analysis"]:
            if not all(key in analysis for key in ["issue", "precedents", "legal_principles", "implications"]):
                return False
            
            # precedents 배열의 각 요소 검증
            for precedent in analysis["precedents"]:
                required_precedent_keys = [
                    "case_number", "court", "date", "summary",
                    "key_holdings", "similarity_analysis"
                ]
                if not all(key in precedent for key in required_precedent_keys):
                    return False

        return True

    def format_output(self, response: Dict) -> Dict:
        """출력 형식 정리"""
        formatted_response = {
            "summary": {
                "analysis_date": datetime.now().isoformat(),
                "total_precedents_analyzed": sum(
                    len(analysis["precedents"]) 
                    for analysis in response["precedent_analysis"]
                ),
                "key_legal_principles": list(set(
                    principle
                    for analysis in response["precedent_analysis"]
                    for principle in analysis["legal_principles"]
                ))
            },
            "detailed_analysis": response,
            "recommendations": {
                "priority_precedents": [
                    precedent["case_number"]
                    for analysis in response["precedent_analysis"]
                    for precedent in analysis["precedents"]
                    if any(
                        similarity in precedent["similarity_analysis"]["factual_similarity"].lower()
                        for similarity in ["high", "strong", "very"]
                    )
                ],
                "key_arguments": response["strategic_implications"]["recommendations"]
            }
        }
        
        return formatted_response
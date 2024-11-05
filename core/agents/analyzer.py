import json
from typing import Dict, Optional
from datetime import datetime
import logging
from .base import BaseAgent, AgentRole
from ..utils.azure_gpt import AzureGPTClient

class CaseAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.ANALYZER, "Case Analyzer")
        self.gpt_client = AzureGPTClient()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def prepare_system_prompt(self) -> str:
        return """당신은 법률 사건 분석 전문가입니다. 
        주어진 사건의 사실관계를 분석하고, 법적 쟁점을 도출하며, 
        관련 법령을 파악하는 것이 주요 업무입니다.
        
        다음 사항에 특히 주의하여 분석해주세요:
        1. 사실관계의 시간순 정리
        2. 주요 법적 쟁점 도출
        3. 적용 가능한 법령 검토
        4. 입증이 필요한 주요 사실 파악
        
        분석은 객관적이고 논리적이어야 하며, 
        모든 판단의 근거를 명확히 제시해야 합니다."""
        
    def prepare_user_prompt(self, input_data: Dict) -> str:
        case_summary = input_data.get('case_summary', '')
        timeline = input_data.get('timeline', [])
        case_type = input_data.get('case_type', '')
        
        # 타임라인 정보 포맷팅
        timeline_str = ""
        if timeline:
            timeline_str = "\n".join([
                f"- {event.get('date', 'N/A')}: {event.get('event', 'N/A')}" 
                for event in timeline
            ])
        
        return f"""다음 사건을 분석해주세요:
                    사건 종류: {case_type}
                    사건 개요:
                    {case_summary}
                    사건 경위:
                    {timeline_str if timeline_str else '타임라인 정보 없음'}
                    다음 항목들을 분석해주세요:
                    1. 사건의 핵심 쟁점
                    2. 관련 법령
                    3. 입증이 필요한 주요 사실
                    4. 법적 분석 및 검토 의견"""
        
    def get_output_format(self) -> Dict:
        return {
            "key_issues": [
                {
                    "issue": "string",
                    "description": "string",
                    "relevant_laws": ["string"],
                    "required_evidence": ["string"]
                }
            ],
            "legal_analysis": {
                "main_points": ["string"],
                "potential_challenges": ["string"],
                "recommended_focus": "string"
            },
            "evidence_requirements": {
                "critical_facts": ["string"],
                "suggested_evidence": ["string"],
                "potential_difficulties": ["string"]
            },
            "initial_opinion": {
                "strengths": ["string"],
                "weaknesses": ["string"],
                "key_considerations": ["string"]
            }
        }

    async def process(self, input_data: Dict) -> Optional[Dict]:
        """사건 분석 수행"""
        try:
            self.logger.info("Starting case analysis")
            
            if not input_data:
                self.logger.error("Empty input data received")
                return None

            # 입력 데이터 로깅
            self.logger.debug(f"Processing input data: {json.dumps(input_data, ensure_ascii=False, indent=2)}")

            # GPT 응답 생성
            system_prompt = self.prepare_system_prompt()
            user_prompt = self.prepare_user_prompt(input_data)
            output_format = self.get_output_format()
            
            self.logger.debug(f"Sending request to GPT with system prompt: {system_prompt[:100]}...")
            self.logger.debug(f"User prompt: {user_prompt[:100]}...")
            
            response = await self.gpt_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output_format=output_format
            )
            
            self.logger.debug(f"Raw GPT response: {json.dumps(response, ensure_ascii=False, indent=2)}")
            
            if response is None:
                self.logger.error("Received null response from GPT")
                return None

            # 응답 검증
            if not self.validate_response(response):
                self.logger.error("Response validation failed")
                self.logger.debug(f"Invalid response structure: {json.dumps(response, ensure_ascii=False, indent=2)}")
                return None

            # 결과 포맷팅
            formatted_result = self.format_output(response)
            if formatted_result is None:
                self.logger.error("Failed to format output")
                return None
                
            self.logger.info("Case analysis completed successfully")
            self.logger.debug(f"Final formatted result: {json.dumps(formatted_result, ensure_ascii=False, indent=2)}")
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Error in case analysis: {str(e)}", exc_info=True)
            return None

    def validate_response(self, response: dict) -> bool:
        """응답 유효성 검증 및 세부 오류 로깅"""
        try:
            required_keys = ["key_issues", "legal_analysis", "evidence_requirements", "initial_opinion"]
            
            if not isinstance(response, dict):
                self.logger.error(f"Response is not a dictionary: {type(response)}")
                return False

            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                self.logger.error(f"Missing required top-level keys: {missing_keys}")
                return False

            # Validate key_issues
            if not isinstance(response["key_issues"], list):
                self.logger.error("'key_issues' is not a list")
                return False

            for idx, issue in enumerate(response["key_issues"]):
                if not isinstance(issue, dict):
                    self.logger.error(f"key_issues[{idx}] is not a dictionary")
                    return False
                    
                for key in ["issue", "description", "relevant_laws", "required_evidence"]:
                    if key not in issue:
                        self.logger.error(f"Missing '{key}' in key_issues[{idx}]")
                        return False

            # Validate structure of other sections
            sections = {
                "legal_analysis": ["main_points", "potential_challenges", "recommended_focus"],
                "evidence_requirements": ["critical_facts", "suggested_evidence", "potential_difficulties"],
                "initial_opinion": ["strengths", "weaknesses", "key_considerations"]
            }

            for section, fields in sections.items():
                if not isinstance(response[section], dict):
                    self.logger.error(f"'{section}' is not a dictionary")
                    return False
                    
                for field in fields:
                    if field not in response[section]:
                        self.logger.error(f"Missing '{field}' in {section}")
                        return False

            return True
            
        except Exception as e:
            self.logger.error(f"Error during response validation: {str(e)}", exc_info=True)
            return False

    def format_output(self, response: Dict) -> Optional[Dict]:
        """출력 형식 정리"""
        try:
            self.logger.debug(f"Formatting GPT response: {json.dumps(response, ensure_ascii=False)}")

            # 응답 구조화
            result = {
                "key_issues": response.get("key_issues", []),
                "legal_analysis": response.get("legal_analysis", {}),
                "evidence_requirements": response.get("evidence_requirements", {}),
                "initial_opinion": response.get("initial_opinion", {}),
                "case_analysis": {  # coordinator가 기대하는 구조
                    "summary": {
                        "case_type": "민사",
                        "main_points": response.get("legal_analysis", {}).get("main_points", []),
                        "analysis_date": datetime.now().isoformat()
                    },
                    "key_issues": response.get("key_issues", []),
                    "legal_analysis": response.get("legal_analysis", {})
                },
                "precedent_research": {
                    "key_findings": response.get("initial_opinion", {}).get("key_considerations", []),
                    "precedent_analysis": []
                },
                "legal_strategy": {
                    "overall_strategy": response.get("legal_analysis", {}).get("recommended_focus", ""),
                    "issue_specific_strategies": response.get("legal_analysis", {}).get("main_points", []),
                    "evidence_strategy": response.get("evidence_requirements", {}),
                    "litigation_timeline": []
                }
            }

            self.logger.debug(f"Formatted output: {json.dumps(result, ensure_ascii=False)}")
            return result

        except Exception as e:
            self.logger.error(f"Error formatting output: {str(e)}", exc_info=True)
            return None
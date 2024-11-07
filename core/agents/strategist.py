# core/agents/strategist.py

import json
import logging
import asyncio
from typing import Dict
from .base import BaseAgent, AgentRole
from core.utils.azure_gpt import AzureGPTClient  # 또는 정확한 경로로 수정

class LegalStrategist(BaseAgent):
    def __init__(self, name: str = "Legal Strategist"):
        super().__init__(AgentRole.STRATEGIST, name)
        self.gpt_client = AzureGPTClient()  # 추가
        self.setup_logging()  # 추가
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.name}")

    def prepare_system_prompt(self) -> str:
        output_format = json.dumps(self.get_output_format(), ensure_ascii=False, indent=2)
        return f"""당신은 법률 전략 수립 전문가입니다.
사건 분석과 판례 연구 결과를 바탕으로 다음 형식의 전략을 수립해주세요(한글로):

{output_format}

다음 사항들을 고려하여 전략을 수립해주세요:
1. 승소 가능성 극대화를 위한 주장 구성
2. 예상되는 상대방 주장에 대한 대응 방안
3. 증거 수집 및 제출 전략
4. 소송 진행 단계별 대응 전략

응답은 반드시 위의 JSON 형식을 준수해야 합니다.
"""

    async def prepare_user_prompt(self, input_data: Dict) -> str:
        # 필요한 데이터 추출 및 포맷팅
        input_str = json.dumps(input_data, ensure_ascii=False, indent=2)
        output_format = json.dumps(self.get_output_format(), ensure_ascii=False, indent=2)

        return f"""다음은 사건 분석과 판례 연구 결과입니다:

{input_str}

위 정보를 바탕으로 법적 전략을 수립해주세요. 결과는 다음과 같은 JSON 형식으로 제공해주세요:

{output_format}

반드시 위의 형식과 키를 정확히 지켜서 응답해주세요.
"""

    def get_output_format(self) -> Dict:
        """전략가용 출력 형식"""
        return {
            "overall_strategy": "전체적인 소송 전략을 기술합니다.",
            "issue_specific_strategies": {
                "이슈1": "이슈1에 대한 전략을 기술합니다.",
                "이슈2": "이슈2에 대한 전략을 기술합니다.",
                "...": "..."
            },
            "evidence_strategy": "증거 수집 및 활용 전략을 기술합니다.",
            "litigation_timeline": "예상 소송 일정 및 주요 단계를 기술합니다."
        }

    def validate_result(self, result: Dict) -> bool:
        """결과 검증"""
        try:
            self.logger.debug("Validating strategy response")
            required_keys = [
                'overall_strategy',
                'issue_specific_strategies',
                'evidence_strategy',
                'litigation_timeline'
            ]
            
            if not isinstance(result, dict):
                self.logger.error(f"Result is not a dictionary: {type(result)}")
                return False

            # 필수 키 존재 확인
            for key in required_keys:
                if key not in result:
                    self.logger.error(f"Missing required key: {key}")
                    return False

            # overall_strategy, evidence_strategy, litigation_timeline는 문자열이어야 함
            if not isinstance(result['overall_strategy'], str):
                self.logger.error("overall_strategy is not a string")
                return False
            if not isinstance(result['evidence_strategy'], str):
                self.logger.error("evidence_strategy is not a string")
                return False
            if not isinstance(result['litigation_timeline'], str):
                self.logger.error("litigation_timeline is not a string")
                return False

            # issue_specific_strategies는 딕셔너리여야 함
            if not isinstance(result['issue_specific_strategies'], dict):
                self.logger.error("issue_specific_strategies is not a dictionary")
                return False

            # 각 이슈와 전략은 문자열이어야 함
            for issue, strategy in result['issue_specific_strategies'].items():
                if not isinstance(issue, str) or not isinstance(strategy, str):
                    self.logger.error("Issue and strategy in issue_specific_strategies must be strings")
                    return False

            self.logger.debug("Strategy response validation successful")
            return True

        except Exception as e:
            self.logger.error(f"Error during strategy validation: {str(e)}", exc_info=True)
            return False

    async def process(self, input_data: Dict) -> Dict:
        """입력 데이터를 처리하고 결과를 반환합니다."""
        try:
            self.logger.info(f"Starting processing with role: {self.role}")
            self.logger.debug(f"Input data: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            user_prompt = await self.prepare_user_prompt(input_data)
            system_prompt = self.prepare_system_prompt()
            
            for attempt in range(3):
                try:
                    response = await self.gpt_client.generate_structured_response(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        output_format=self.get_output_format()
                    )
                    self.logger.debug(f"GPT response: {response}")

                    if self.validate_result(response):
                        self.logger.info("Strategy response validation successful")
                        return response
                    else:
                        self.logger.warning("Strategy response validation failed")
                except Exception as e:
                    self.logger.error(f"Error in generating response: {str(e)}")
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1)

            raise ValueError("Failed to generate valid strategy response after 3 attempts")
        except Exception as e:
            self.logger.error(f"Error during processing: {str(e)}", exc_info=True)
            raise e

# core/agents/base.py

from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import json
import logging
import sys
import os
from abc import ABC, abstractmethod

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.utils.azure_gpt import AzureGPTClient
from config.azure_config import MODEL_CONFIG

class AgentRole(Enum):
    ANALYZER = "analyzer"        # 사건 분석
    RESEARCHER = "researcher"    # 판례 연구
    STRATEGIST = "strategist"    # 전략 수립

class AgentState(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING_FEEDBACK = "waiting_feedback"
    COMPLETED = "completed"
    ERROR = "error"

class BaseAgent:
    def __init__(self, role: AgentRole, name: str):
        self.role = role
        self.name = name
        self.state = AgentState.IDLE
        self.gpt_client = AzureGPTClient()
        self.conversation_history: List[Dict] = []
        self.work_results: Dict = {}
        self.max_retries = 3
        self.setup_logging()

    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.name}")
        self.logger.setLevel(logging.DEBUG)
        
        # logs 디렉토리 생성
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 파일 핸들러 추가
        fh = logging.FileHandler(os.path.join(log_dir, f"{self.name.lower()}.log"))
        fh.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 추가
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # 핸들러 추가
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
    # BaseAgent의 process 메서드 수정
    async def process(self, input_data: Dict) -> Dict:
        try:
            self.logger.info(f"Starting processing with role: {self.role}")
            self.logger.debug(f"Input data: {json.dumps(input_data, ensure_ascii=False)}")

            # 시스템 프롬프트 준비
            system_prompt = self.prepare_system_prompt()
            if not system_prompt:
                raise ValueError("System prompt is not prepared")

            # 사용자 프롬프트 준비
            user_prompt = self.prepare_user_prompt(input_data)
            if not user_prompt:
                raise ValueError("User prompt is not prepared")

            # GPT 응답 생성
            result = await self.gpt_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output_format=self.get_output_format()
            )

            if not result:
                raise ValueError("No result generated")

            # 결과 검증
            if not self.validate_result(result):
                raise ValueError("Invalid result format")

            return result

        except Exception as e:
            self.logger.error("Processing failed:", exc_info=True)
            raise


    def prepare_system_prompt(self) -> str:
        """시스템 프롬프트 준비 - 하위 클래스에서 구현"""
        raise NotImplementedError
        
    def prepare_user_prompt(self, input_data: Dict) -> str:
        """사용자 프롬프트 준비 - 하위 클래스에서 구현"""
        raise NotImplementedError
        
    def get_output_format(self) -> Dict:
        """출력 형식 정의"""
        return {
            "analysis": "string",
            "recommendations": ["string"],
            "risks": ["string"],
            "next_steps": ["string"]
        }
        
    def validate_response(self, response: Dict) -> bool:
        """응답 유효성 검증 - 하위 클래스에서 구현"""
        raise NotImplementedError
        
    def format_output(self, response: Dict) -> Dict:
        """출력 형식 변환 - 하위 클래스에서 구현"""
        raise NotImplementedError
        
    def add_to_conversation(self, role: str, content: str):
        """대화 기록 추가"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.conversation_history.append(entry)
        self.logger.debug(f"Added conversation entry: {json.dumps(entry, indent=2)}")
        
    def get_conversation_history(self) -> List[Dict]:
        """대화 기록 반환"""
        return self.conversation_history
        
    def get_state(self) -> AgentState:
        """현재 상태 반환"""
        return self.state
        
    def reset(self):
        """상태 초기화"""
        self.logger.info("Resetting agent state")
        self.state = AgentState.IDLE
        self.conversation_history = []
        self.work_results = {}

    def validate_result(self, result: Dict) -> bool:
        """결과 검증"""
        required_keys = [
            'analysis',
            'recommendations',
            'risks',
            'next_steps'
        ]
        return all(key in result for key in required_keys)

class AgentException(Exception):
    """에이전트 관련 예외"""
    def __init__(self, message: str, agent_name: str, error_type: str):
        self.agent_name = agent_name
        self.error_type = error_type
        super().__init__(f"{agent_name}: {error_type} - {message}")
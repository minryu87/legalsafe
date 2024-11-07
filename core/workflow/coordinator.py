# core/workflow/coordinator.py

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.agents.analyzer import LegalAnalyzer
from core.agents.researcher import LegalResearcher
from core.agents.strategist import LegalStrategist
from core.agents.base import AgentState

class WorkflowState(Enum):
    INITIALIZED = "initialized"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    STRATEGIZING = "strategizing"
    COMPLETED = "completed"
    ERROR = "error"

class WorkflowStage(Enum):
    CASE_ANALYSIS = "case_analysis"
    PRECEDENT_RESEARCH = "precedent_research"
    STRATEGY_DEVELOPMENT = "strategy_development"

class AgentCoordinator:
    def __init__(self):
        self.execution_log = []  # 실행 로그 초기화
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.current_stage = None
        self.results = {}  # 결과를 저장할 딕셔너리 초기화       

        # BaseAgent 구현체들 초기화
        self.analyzer = LegalAnalyzer()
        self.researcher = LegalResearcher("판례연구원")  # researcher가 None이 되지 않도록 함
        self.strategist = LegalStrategist()
        
        self.workflow_state = WorkflowState.INITIALIZED

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AgentCoordinator')

    async def process_case(self, case_data: Dict) -> Dict:
        self.workflow_state = WorkflowState.INITIALIZED  # 초기화 상태로 설정
        try:
            # Case Analysis
            self.current_stage = WorkflowStage.CASE_ANALYSIS
            self.workflow_state = WorkflowState.ANALYZING  # 분석 중 상태로 변경
            analysis_result = await self._run_case_analysis(case_data)
            self.results[WorkflowStage.CASE_ANALYSIS] = analysis_result

            # Precedent Research
            self.current_stage = WorkflowStage.PRECEDENT_RESEARCH
            self.workflow_state = WorkflowState.RESEARCHING  # 연구 중 상태로 변경
            research_result = await self._run_precedent_research(analysis_result)
            self.results[WorkflowStage.PRECEDENT_RESEARCH] = research_result

            # Strategy Development
            self.current_stage = WorkflowStage.STRATEGY_DEVELOPMENT
            self.workflow_state = WorkflowState.STRATEGIZING  # 전략 수립 중 상태로 변경
            strategy_result = await self._run_strategy_development(analysis_result, research_result)
            self.results[WorkflowStage.STRATEGY_DEVELOPMENT] = strategy_result

            self.workflow_state = WorkflowState.COMPLETED  # 완료 상태로 변경
            return self._compile_final_results()

        except Exception as e:
            self.workflow_state = WorkflowState.ERROR  # 에러 상태로 변경
            self.logger.error(f"Error in case processing: {e}")
            # 필요한 경우 부분 결과 반환
            return self._compile_final_results()

    async def _run_case_analysis(self, case_data: Dict) -> Dict:
        """사건 분석 실행"""
        try:
            self.log_execution_step("Starting case analysis")
            if not self.analyzer:
                raise ValueError("Analyzer is not initialized")
                
            result = await self.analyzer.process(case_data)
            if result:
                self.log_execution_step("Case analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in case analysis: {str(e)}", exc_info=True)
            raise

    async def _run_precedent_research(self, analysis_result: Dict) -> Dict:
        """판례 연구 실행"""
        try:
            self.logger.info("Starting precedent research")
            if not self.researcher:
                self.researcher = LegalResearcher("판례연구원")  # 필요한 경우 researcher 재초기화
            
            research_input = self._prepare_research_input(analysis_result)
            result = await self.researcher.process(research_input)
            if not result:
                raise ValueError("Precedent research returned no result")
                
            if not self._validate_research_result(result):
                raise ValueError("Research result validation failed")
                
            self.logger.info("Precedent research completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in precedent research: {str(e)}", exc_info=True)
            raise

    async def _run_strategy_development(self,
                                        analysis_result: Dict,
                                        research_result: Dict) -> Optional[Dict]:
        """전략 수립 단계 실행"""
        try:
            self.current_stage = WorkflowStage.STRATEGY_DEVELOPMENT
            self.log_execution_step("Starting strategy development")

            strategy_input = self._prepare_strategy_input(
                analysis_result, research_result
            )
            
            # 전략 수립 실행
            result = await self.strategist.process(strategy_input)

            # 검증 단계에서 LegalStrategist의 validate_result 메서드 호출
            if result and self.strategist.validate_result(result):
                self.results[WorkflowStage.STRATEGY_DEVELOPMENT] = result
                self.log_execution_step("Strategy development completed successfully")
                return result

            self.log_execution_step("Strategy development failed validation", "ERROR")
            return None

        except Exception as e:
            self.log_execution_step(str(e), "ERROR")
            raise

    def _prepare_research_input(self, analysis_result: Dict) -> Dict:
        """판례 연구를 위한 입력 데이터 준비"""
        return {
            "case_type": analysis_result.get("case_type", ""),
            "legal_issues": analysis_result.get("key_issues", [])
        }

    def _prepare_strategy_input(self, 
                                analysis_result: Dict, 
                                research_result: Dict) -> Dict:
        """전략 수립을 위한 입력 데이터 준비"""
        return {
            "case_analysis": analysis_result,
            "precedent_research": research_result,
            "evidence_status": {
                "existing_evidence": analysis_result.get("evidence_requirements", {}).get("existing_evidence", []),
                "potential_evidence": analysis_result.get("evidence_requirements", {}).get("potential_evidence", [])
            }
        }

    def _validate_analysis_result(self, result: Dict) -> bool:
        """분석 결과 유효성 검증"""
        required_keys = ["key_issues", "legal_analysis", "evidence_requirements"]
        return all(key in result for key in required_keys)

    def _validate_research_result(self, result: Dict) -> bool:
        """연구 결과 유효성 검증 - 상세 로깅 추가"""
        if not isinstance(result, dict):
            self.logger.error(f"Research result is not a dictionary: {type(result)}")
            return False

        required_keys = ["key_findings", "precedent_analysis"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            self.logger.error(f"Missing required keys in research result: {missing_keys}")
            self.logger.debug(f"Available keys: {list(result.keys())}")
            return False
            
        return True

    def _validate_strategy_result(self, result: Dict) -> bool:
        """전략 결과 유효성 검증"""
        required_keys = ["overall_strategy", "issue_specific_strategies", "evidence_strategy"]
        return all(key in result for key in required_keys)

    def _compile_final_results(self) -> Dict:
        """최종 결과 취합"""
        final_results = {}
        if WorkflowStage.CASE_ANALYSIS in self.results:
            final_results["case_analysis"] = self.results[WorkflowStage.CASE_ANALYSIS]
        if WorkflowStage.PRECEDENT_RESEARCH in self.results:
            final_results["precedent_research"] = self.results[WorkflowStage.PRECEDENT_RESEARCH]
        if WorkflowStage.STRATEGY_DEVELOPMENT in self.results:
            final_results["legal_strategy"] = self.results[WorkflowStage.STRATEGY_DEVELOPMENT]
        final_results["metadata"] = {
            "completion_time": datetime.now().isoformat(),
            "workflow_state": self.workflow_state.value,
            "execution_log": self.execution_log
        }
        return final_results

    def log_execution_step(self, message: str, level: str = "INFO"):
        """실행 단계 로깅"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'state': self.workflow_state.value,
            'message': message,
            'level': level
        }
        self.execution_log.append(log_entry)
        
        # 로그 레벨에 따른 로깅
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def get_execution_log(self) -> List[Dict]:
        """실행 로그 반환"""
        return self.execution_log

    def get_current_state(self) -> Dict:
        """현재 상태 정보 반환"""
        return {
            "workflow_state": self.workflow_state.value,
            "analyzer_state": "completed" if WorkflowStage.CASE_ANALYSIS in self.results else "pending",
            "researcher_state": "completed" if WorkflowStage.PRECEDENT_RESEARCH in self.results else "pending",
            "strategist_state": "completed" if WorkflowStage.STRATEGY_DEVELOPMENT in self.results else "pending"
        }

    def clear_execution_log(self) -> None:
        """실행 로그 초기화"""
        self.execution_log = []
        
    def export_execution_log(self, file_path: str) -> None:
        """실행 로그 파일로 저장"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'log': self.execution_log,
                'exported_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

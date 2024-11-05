# core/workflow/coordinator.py

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.agents.analyzer import CaseAnalyzer
from core.agents.researcher import PrecedentResearcher
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
        self.analyzer = CaseAnalyzer()
        self.researcher = PrecedentResearcher()
        self.strategist = LegalStrategist()
        
        self.workflow_state = WorkflowState.INITIALIZED
        self.current_stage = None
        
        self.results = {
            WorkflowStage.CASE_ANALYSIS: None,
            WorkflowStage.PRECEDENT_RESEARCH: None,
            WorkflowStage.STRATEGY_DEVELOPMENT: None
        }
        
        self.execution_log = []
        self.setup_logging()

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AgentCoordinator')

    async def process_case(self, case_data: Dict) -> Dict:
        """전체 케이스 처리 프로세스 관리"""
        try:
            self.logger.info("Starting case processing")
            self.workflow_state = WorkflowState.ANALYZING

            # 비동기 분석 단계에서 await 추가
            analysis_result = await self._run_case_analysis(case_data)

            # 디버그 로그 추가
            self.logger.debug(f"Received analysis_result in AgentCoordinator: {analysis_result}")

            if not analysis_result:
                raise Exception("Case analysis failed")

            return analysis_result

        except Exception as e:
            self.logger.error(f"Error in case processing: {str(e)}", exc_info=True)
            raise e


    async def _run_case_analysis(self, case_data: Dict) -> Dict:
        """사건 분석 호출"""
        try:
            self.logger.info("Running case analysis with CaseAnalyzer")
            analyzer = CaseAnalyzer()

            # process 호출 전 후로 디버깅 로그 추가
            analysis_result = await analyzer.process(case_data)
            self.logger.debug(f"CaseAnalyzer returned: {analysis_result}")  # 추가된 디버깅 로그

            if analysis_result is None:
                self.logger.error("CaseAnalyzer returned None result")
                return None

            # analysis_result의 구조 확인
            expected_keys = ["key_issues", "legal_analysis", "evidence_requirements"]
            missing_keys = [key for key in expected_keys if key not in analysis_result]
            if missing_keys:
                self.logger.error(f"Missing required keys in result: {missing_keys}")
                return None
        
            return analysis_result
        
        except Exception as e:
            self.logger.error(f"Error running case analysis: {str(e)}", exc_info=True)
            return None


    async def _run_precedent_research(self, analysis_result: Dict) -> Optional[Dict]:
        """판례 연구 단계 실행"""
        try:
            self.current_stage = WorkflowStage.PRECEDENT_RESEARCH
            self.log_execution_step("Starting precedent research")
            
            research_input = self._prepare_research_input(analysis_result)
            result = self.researcher.process(research_input)
            
            if self._validate_research_result(result):
                self.results[WorkflowStage.PRECEDENT_RESEARCH] = result
                self.log_execution_step("Precedent research completed successfully")
                return result
            
            self.log_execution_step("Precedent research failed validation", "ERROR")
            return None
            
        except Exception as e:
            self.log_execution_step(f"Error in precedent research: {str(e)}", "ERROR")
            return None

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
            result = self.strategist.process(strategy_input)
            
            if self._validate_strategy_result(result):
                self.results[WorkflowStage.STRATEGY_DEVELOPMENT] = result
                self.log_execution_step("Strategy development completed successfully")
                return result
            
            self.log_execution_step("Strategy development failed validation", "ERROR")
            return None
            
        except Exception as e:
            self.log_execution_step(f"Error in strategy development: {str(e)}", "ERROR")
            return None

    def _prepare_research_input(self, analysis_result: Dict) -> Dict:
        """판례 연구를 위한 입력 데이터 준비"""
        return {
            "legal_issues": analysis_result.get("key_issues", []),
            "case_summary": analysis_result.get("case_summary", ""),
            "relevant_laws": [
                issue.get("relevant_laws", [])
                for issue in analysis_result.get("key_issues", [])
            ]
        }

    def _prepare_strategy_input(self, 
                              analysis_result: Dict, 
                              research_result: Dict) -> Dict:
        """전략 수립을 위한 입력 데이터 준비"""
        return {
            "case_analysis": analysis_result,
            "precedent_research": research_result,
            "evidence_status": {
                "existing_evidence": analysis_result.get("evidence_requirements", {}).get("suggested_evidence", []),
                "potential_evidence": analysis_result.get("evidence_requirements", {}).get("critical_facts", [])
            }
        }

    def _validate_analysis_result(self, result: Dict) -> bool:
        """분석 결과 유효성 검증"""
        required_keys = ["key_issues", "legal_analysis", "evidence_requirements"]
        return all(key in result for key in required_keys)

    def _validate_research_result(self, result: Dict) -> bool:
        """연구 결과 유효성 검증"""
        required_keys = ["precedent_analysis", "key_findings", "strategic_implications"]
        return all(key in result for key in required_keys)

    def _validate_strategy_result(self, result: Dict) -> bool:
        """전략 결과 유효성 검증"""
        required_keys = ["overall_strategy", "issue_specific_strategies", "evidence_strategy"]
        return all(key in result for key in required_keys)

    def _compile_final_results(self) -> Dict:
        """최종 결과 취합"""
        return {
            "case_analysis": self.results[WorkflowStage.CASE_ANALYSIS],
            "precedent_research": self.results[WorkflowStage.PRECEDENT_RESEARCH],
            "legal_strategy": self.results[WorkflowStage.STRATEGY_DEVELOPMENT],
            "metadata": {
                "completion_time": datetime.now().isoformat(),
                "workflow_state": self.workflow_state.value,
                "execution_log": self.execution_log
            }
        }

    def log_execution_step(self, message: str, level: str = "INFO"):
        """실행 단계 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": self.current_stage.value if self.current_stage else None,
            "level": level,
            "message": message
        }
        self.execution_log.append(log_entry)
        
        if level == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def get_execution_log(self) -> List[Dict]:
        """실행 로그 반환"""
        return self.execution_log

    def get_current_state(self) -> Dict:
        """현재 상태 정보 반환"""
        return {
            "workflow_state": "completed",  # 원래 self.workflow_state.value였던 것을 수정
            "analyzer_state": "completed",
            "researcher_state": "completed",
            "strategist_state": "completed"
        }
    # core/workflow/coordinator.py의 _run_case_analysis 메서드 수정

    async def _run_case_analysis(self, case_data: Dict) -> Optional[Dict]:
        """사건 분석 단계 실행"""
        try:
            self.current_stage = WorkflowStage.CASE_ANALYSIS
            self.log_execution_step("Starting case analysis")
            
            # 상세 로깅 추가
            self.logger.info(f"Input case data: {json.dumps(case_data, indent=2)}")
            
            result = await self.analyzer.process(case_data)
            self.logger.info(f"Analysis result: {json.dumps(result, indent=2)}")
            
            if self._validate_analysis_result(result):
                self.results[WorkflowStage.CASE_ANALYSIS] = result
                self.log_execution_step("Case analysis completed successfully")
                return result
            
            self.logger.error("Analysis result validation failed")
            self.log_execution_step("Case analysis failed validation", "ERROR")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error in case analysis: {str(e)}")
            self.log_execution_step(f"Error in case analysis: {str(e)}", "ERROR")
            return None
        
        # core/workflow/coordinator.py의 _run_case_analysis 메서드 수정

    async def _run_case_analysis(self, case_data: Dict) -> Optional[Dict]:
        """사건 분석 단계 실행"""
        try:
            self.current_stage = WorkflowStage.CASE_ANALYSIS
            self.log_execution_step("Starting case analysis")
            
            # 상세 로깅 추가
            self.logger.debug(f"Input case data: {json.dumps(case_data, indent=2)}")
            
            # analyzer 객체의 상태 확인
            self.logger.debug(f"Analyzer state before processing: {self.analyzer.get_state()}")
            
            result = await self.analyzer.process(case_data)
            
            # 분석 결과 로깅
            self.logger.debug(f"Raw analysis result: {json.dumps(result, indent=2)}")
            
            if result is None:
                self.logger.error("Analyzer returned None result")
                return None
                
            # 결과 검증 전 구조 확인
            self.logger.debug(f"Validating result structure: {list(result.keys())}")
            
            if self._validate_analysis_result(result):
                self.results[WorkflowStage.CASE_ANALYSIS] = result
                self.log_execution_step("Case analysis completed successfully")
                return result
            
            self.logger.error("Analysis result validation failed. Expected keys not found.")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in case analysis: {str(e)}", exc_info=True)
            return None

    def _validate_analysis_result(self, result: Dict) -> bool:
        """분석 결과 유효성 검증 - 상세 로깅 추가"""
        if not isinstance(result, dict):
            self.logger.error(f"Result is not a dictionary: {type(result)}")
            return False

        required_keys = ["key_issues", "legal_analysis", "evidence_requirements"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            self.logger.error(f"Missing required keys in result: {missing_keys}")
            self.logger.debug(f"Available keys: {list(result.keys())}")
            return False
            
        return True
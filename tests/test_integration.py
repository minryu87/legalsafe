# tests/test_integration.py

import sys
import os
import asyncio
import pytest
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workflow.coordinator import AgentCoordinator
from core.workflow.pipeline import LegalAnalysisPipeline
from core.workflow.reporter import LegalReporter, ReportFormat

class TestIntegration:
    @pytest.fixture
    def sample_case_data(self):
        """테스트용 샘플 케이스 데이터"""
        return {
            "case_type": "민사",
            "parties_info": {
                "our_side": {
                    "role": "원고",
                    "brief": "A회사 - IT 서비스 제공업체"
                },
                "opposing_side": {
                    "role": "피고",
                    "brief": "B회사 - 소프트웨어 개발업체"
                }
            },
            "case_summary": """
            계약 위반 및 손해배상 청구 사건
            원고 A회사는 피고 B회사에 소프트웨어 개발을 의뢰하였으나,
            피고는 계약상 정해진 기한 내에 개발을 완료하지 못했으며,
            제공된 소프트웨어에도 심각한 하자가 있었음.
            이에 원고는 계약 위반에 따른 손해배상을 청구함.
            """,
            "legal_issues": [
                {
                    "issue": "계약 위반의 성립 여부",
                    "relevant_law": "민법 제390조",
                    "opinion": "개발 지연 및 품질 미달은 명백한 계약 위반에 해당"
                },
                {
                    "issue": "손해배상의 범위",
                    "relevant_law": "민법 제393조",
                    "opinion": "개발 지연으로 인한 영업 손실 및 대체 솔루션 도입 비용 청구"
                }
            ],
            "evidence_info": {
                "existing_evidence": "계약서, 업무 미팅 회의록, 이메일 교신 기록",
                "potential_evidence": "개발 진행 상황 보고서, 품질 테스트 결과",
                "evidence_difficulties": "피고측의 내부 개발 문서 확보 어려움"
            }
        }

    @pytest.fixture
    def pipeline(self):
        """파이프라인 인스턴스 생성"""
        return LegalAnalysisPipeline()

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, pipeline, sample_case_data):
        """전체 파이프라인 실행 테스트"""
        # 1. 파이프라인 실행
        result = await pipeline.process_case(sample_case_data)
        
        # 2. 결과 검증
        assert result is not None
        assert "report" in result
        assert "metadata" in result
        
        # 3. 상태 확인
        assert pipeline.status.value == "completed"
        
        return result

    @pytest.mark.asyncio
    async def test_agent_coordination(self, pipeline, sample_case_data):
        """에이전트 간 협업 테스트"""
        coordinator = pipeline.coordinator
        
        # 1. 분석 단계 테스트
        analysis_result = await coordinator.process_case(sample_case_data)
        
        # 2. 결과 검증
        assert analysis_result is not None
        assert "case_analysis" in analysis_result
        assert "precedent_research" in analysis_result
        assert "legal_strategy" in analysis_result
        
        # 3. 에이전트 상태 확인
        agent_states = coordinator.get_current_state()
        assert all(state in ["completed", "idle"] for state in agent_states.values())
        
        return analysis_result

    def test_report_generation(self, sample_case_data):
        """보고서 생성 테스트"""
        reporter = LegalReporter()

        # 분석 결과를 모의 데이터로 설정 (실제 구조에 맞게 수정 필요)
        analysis_results = {
            "key_issues": [...],  # 필요한 데이터 입력
            "legal_analysis": {...},
            "evidence_requirements": {...},
            "initial_opinion": {...},
            # 추가적으로 필요한 필드들...
        }

        # 1. 상세 보고서 테스트
        detailed_report = reporter.generate_report(
            analysis_results,
            report_format=ReportFormat.DETAILED
        )
        assert detailed_report is not None
        assert "sections" in detailed_report
        assert "metadata" in detailed_report
        
        # 2. 요약 보고서 테스트
        concise_report = reporter.generate_report(
            sample_case_data, 
            report_format=ReportFormat.CONCISE
        )
        assert concise_report is not None
        assert "summary" in concise_report
        assert "key_recommendations" in concise_report
        
        return detailed_report, concise_report

    @pytest.mark.asyncio
    async def test_error_handling(self, pipeline):
        """에러 처리 테스트"""
        # 1. 잘못된 입력 데이터로 테스트
        invalid_data = {"invalid": "data"}
        
        with pytest.raises(ValueError):
            await pipeline.process_case(invalid_data)
        
        # 2. 상태 확인
        assert pipeline.status.value == "failed"
        
        # 3. 로그 확인
        assert len(pipeline.execution_history) > 0
        assert any(event["level"] == "ERROR" for event in pipeline.execution_history)

    @pytest.mark.asyncio
    async def test_full_system_integration(self, pipeline, sample_case_data):
        """전체 시스템 통합 테스트"""
        try:
            # 1. 파이프라인 실행
            pipeline_result = await pipeline.process_case(sample_case_data)
            assert pipeline_result is not None
            
            # 2. 보고서 생성
            reporter = LegalReporter()
            detailed_report = reporter.generate_report(pipeline_result)
            assert detailed_report is not None
            
            # 3. 결과 검증
            self._validate_final_output(detailed_report)
            
            # 4. 보고서 저장
            reporter.export_report(detailed_report)
            
            return detailed_report
            
        except Exception as e:
            pytest.fail(f"Integration test failed: {str(e)}")

    def _validate_final_output(self, report):
        """최종 출력 검증"""
        required_sections = [
            "executive_summary",
            "case_analysis",
            "precedent_review",
            "strategy_recommendations",
            "risk_analysis",
            "evidence_plan",
            "timeline",
            "appendices"
        ]
        
        # 1. 필수 섹션 확인
        assert all(section in report["sections"] for section in required_sections)
        
        # 2. 내용 유효성 검증
        exec_summary = report["sections"]["executive_summary"]
        assert "case_overview" in exec_summary
        assert "key_findings" in exec_summary
        assert "strategic_direction" in exec_summary
        
        # 3. 메타데이터 검증
        assert "generated_at" in report["metadata"]
        assert "report_format" in report["metadata"]

def run_tests():
    """테스트 실행"""
    pytest.main(["-v", __file__])

if __name__ == "__main__":
    run_tests()
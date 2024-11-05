# core/workflow/reporter.py

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.azure_config import MODEL_CONFIG

class ReportSection(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    CASE_ANALYSIS = "case_analysis"
    CASE_SUMMARY = "case_summary"
    PRECEDENT_REVIEW = "precedent_review"
    STRATEGY_RECOMMENDATIONS = "strategy_recommendations"
    RISK_ANALYSIS = "risk_analysis"
    EVIDENCE_PLAN = "evidence_plan"
    TIMELINE = "timeline"
    APPENDICES = "appendices"
    CONCLUSIONS = "conclusions"  # 추가

class ReportFormat(Enum):
    DETAILED = "detailed"
    CONCISE = "concise"
    PRESENTATION = "presentation"

class LegalReporter:
    def __init__(self):
        self.setup_logging()
        self.report_sections = {}
        self.metadata = {}
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('LegalReporter')

    def generate_report(self, analysis_results: Dict, report_format: ReportFormat = ReportFormat.DETAILED) -> Dict:
        """보고서 생성 함수"""
        try:
            # 보고서 섹션 초기화
            self.report_sections = {
                ReportSection.EXECUTIVE_SUMMARY: self._create_executive_summary(analysis_results),
                ReportSection.CASE_ANALYSIS: self._create_case_analysis(analysis_results),
                ReportSection.PRECEDENT_REVIEW: self._create_precedent_review(analysis_results),
                ReportSection.STRATEGY_RECOMMENDATIONS: self._create_strategy_recommendations(analysis_results),
                ReportSection.RISK_ANALYSIS: self._create_risk_analysis(analysis_results),
                ReportSection.EVIDENCE_PLAN: self._create_evidence_plan(analysis_results),
                ReportSection.TIMELINE: self._create_timeline(analysis_results),
                ReportSection.APPENDICES: self._create_appendices(analysis_results),
                ReportSection.CONCLUSIONS: self._create_conclusions(analysis_results)
            }

            # 메타데이터 설정
            self.metadata = {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "report_format": report_format.value
            }

            # 포맷에 따라 보고서 생성
            return self._format_report(report_format)
                
        except Exception as e:
            self.logger.error(f"Error generating report: {e}", exc_info=True)
            return None

    def _create_executive_summary(self, results: Dict) -> Dict:
        """핵심 요약 생성"""
        return {
            "case_overview": {
                "type": results.get("case_type"),
                "key_issues": self._summarize_key_issues(results),
                "summary": results.get("case_summary")
            },
            "key_findings": {
                "main_points": self._extract_key_findings(results),
                "success_factors": self._extract_success_factors(results),
                "risk_factors": self._extract_risk_factors(results)
            },
            "strategic_direction": {
                "recommended_approach": self._extract_strategic_approach(results),
                "critical_next_steps": self._extract_critical_steps(results)
            },
            "success_probability": {
                "overall_assessment": self._calculate_success_probability(results),
                "key_factors": self._extract_probability_factors(results)
            }
        }

    def _create_case_analysis(self, results: Dict) -> Dict:
        """사건 분석 섹션 생성"""
        return {
            "legal_issues": self._format_legal_issues(
                results.get("case_analysis", {}).get("key_issues", [])
            ),
            "factual_analysis": {
                "key_facts": self._extract_key_facts(results),
                "disputed_facts": self._extract_disputed_facts(results),
                "timeline": self._create_detailed_timeline(results)
            },
            "legal_framework": {
                "applicable_laws": self._extract_applicable_laws(results),
                "key_legal_principles": self._extract_legal_principles(results)
            },
            "preliminary_assessment": {
                "strengths": self._extract_case_strengths(results),
                "weaknesses": self._extract_case_weaknesses(results),
                "uncertainties": self._extract_uncertainties(results)
            }
        }

    def _create_precedent_review(self, results: Dict) -> Dict:
        """판례 분석 섹션 생성"""
        return {
            "key_precedents": self._format_key_precedents(
                results.get("precedent_research", {}).get("precedent_analysis", [])
            ),
            "legal_principles": {
                "established_principles": self._extract_established_principles(results),
                "relevant_interpretations": self._extract_legal_interpretations(results)
            },
            "comparative_analysis": {
                "similarities": self._extract_case_similarities(results),
                "differences": self._extract_case_differences(results),
                "implications": self._extract_precedent_implications(results)
            }
        }

    def _create_strategy_recommendations(self, results: Dict) -> Dict:
        """전략 제안 섹션 생성"""
        return {
            "overall_strategy": {
                "main_approach": self._extract_main_strategy(results),
                "key_objectives": self._extract_strategic_objectives(results),
                "success_metrics": self._extract_success_metrics(results)
            },
            "tactical_recommendations": {
                "immediate_actions": self._extract_immediate_actions(results),
                "medium_term_actions": self._extract_medium_term_actions(results),
                "long_term_considerations": self._extract_long_term_considerations(results)
            },
            "counter_strategy": {
                "anticipated_opposition": self._extract_anticipated_opposition(results),
                "proposed_responses": self._extract_proposed_responses(results)
            }
        }

    def _create_risk_analysis(self, results: Dict) -> Dict:
            """위험 분석 섹션 생성"""
            return {
                "legal_risks": self._format_legal_risks(results.get("legal_risks", {})),
                "procedural_risks": self._format_procedural_risks(results.get("procedural_risks", {})),
            }



    def _create_evidence_plan(self, results: Dict) -> Dict:
        """증거 계획 섹션 생성"""
        return {
            "existing_evidence": self._format_existing_evidence(results),
            "required_evidence": self._format_required_evidence(results),
            "collection_strategy": self._format_collection_strategy(results),
            "presentation_plan": self._format_presentation_plan(results)
        }

    def _create_timeline(self, results: Dict) -> Dict:
        """타임라인 섹션 생성"""
        return {
            "procedural_timeline": self._create_procedural_timeline(results),
            "evidence_collection_timeline": self._create_evidence_timeline(results),
            "strategic_action_timeline": self._create_strategic_timeline(results),
            "key_deadlines": self._extract_key_deadlines(results)
        }

    def _create_appendices(self, results: Dict) -> Dict:
        """부록 섹션 생성"""
        return {
            "detailed_precedent_summaries": self._create_precedent_summaries(results),
            "legal_references": self._create_legal_references(results),
            "evidence_details": self._create_evidence_details(results),
            "analysis_methodology": self._create_methodology_description()
        }

    def _format_report(self, report_format: ReportFormat) -> Dict:
        """보고서 최종 포맷팅"""
        if report_format == ReportFormat.DETAILED:
            return self._format_detailed_report()
        elif report_format == ReportFormat.CONCISE:
            return self._format_concise_report()
        else:  # PRESENTATION
            return self._format_presentation_report()

    def _format_detailed_report(self) -> Dict:
        """상세 보고서 포맷팅"""
        return {
            "metadata": self.metadata,
            "sections": {
                section.value: content
                for section, content in self.report_sections.items()
            }
        }

    def _format_concise_report(self) -> Dict:
        """요약 보고서 포맷팅"""
        return {
            "metadata": self.metadata,
            "summary": self.report_sections[ReportSection.EXECUTIVE_SUMMARY],
            "key_recommendations": self.report_sections[ReportSection.STRATEGY_RECOMMENDATIONS]["overall_strategy"],
            "critical_risks": self._extract_critical_risks(),
            "next_steps": self._extract_next_steps()
        }

    def _format_presentation_report(self) -> Dict:
        """프레젠테이션 형식 보고서 포맷팅"""
        return {
            "metadata": self.metadata,
            "slides": self._create_presentation_slides()
        }

    def export_report(self, report: Dict, format: str = "json") -> None:
        """보고서 파일 출력"""
        try:
            filename = f"legal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Report exported successfully to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            raise

    def _extract_critical_risks(self) -> List[str]:
        """주요 위험 요소 추출"""
        try:
            risk_analysis = self.report_sections[ReportSection.RISK_ANALYSIS]
            critical_risks = []
            for risk_type, risks in risk_analysis.items():
                if isinstance(risks, list):
                    critical_risks.extend(risks)
                elif isinstance(risks, dict) and "high_priority_risks" in risks:
                    critical_risks.extend(risks["high_priority_risks"])
            return critical_risks
        except Exception as e:
            self.logger.error(f"Error extracting critical risks: {e}")
            return []

    def _extract_next_steps(self) -> List[str]:
        """다음 단계 추출"""
        try:
            if ReportSection.STRATEGY_RECOMMENDATIONS in self.report_sections:
                strategy = self.report_sections[ReportSection.STRATEGY_RECOMMENDATIONS]
                if isinstance(strategy, dict) and "tactical_recommendations" in strategy:
                    return strategy["tactical_recommendations"].get("immediate_actions", [])
            return []
        except Exception as e:
            self.logger.error(f"Error extracting next steps: {e}")
            return []

    def _create_presentation_slides(self) -> List[Dict]:
        """프레젠테이션 슬라이드 생성"""
        return [
            {
                "title": "Case Overview",
                "content": self.report_sections[ReportSection.EXECUTIVE_SUMMARY]["case_overview"]
            },
            {
                "title": "Key Findings",
                "content": self.report_sections[ReportSection.EXECUTIVE_SUMMARY]["key_findings"]
            },
            {
                "title": "Strategic Recommendations",
                "content": self.report_sections[ReportSection.STRATEGY_RECOMMENDATIONS]["overall_strategy"]
            },
            {
                "title": "Critical Risks",
                "content": self._extract_critical_risks()
            },
            {
                "title": "Next Steps",
                "content": self._extract_next_steps()
            }
        ]
 
    def _summarize_key_issues(self, results: Dict) -> List[str]:
        """주요 쟁점 요약"""
        issues = results.get("legal_issues", [])
        return [issue.get("issue", "") for issue in issues]

    def _extract_key_findings(self, results: Dict) -> List[str]:
        """주요 발견사항 추출"""
        return results.get("key_findings", {}).get("main_points", [])

    def _extract_success_factors(self, results: Dict) -> List[str]:
        """성공 요인 추출"""
        return results.get("key_findings", {}).get("success_factors", [])

    def _extract_risk_factors(self, results: Dict) -> List[str]:
        """위험 요인 추출"""
        return results.get("key_findings", {}).get("risk_factors", [])

    def _extract_strategic_approach(self, results: Dict) -> str:
        """전략적 접근 방법 추출"""
        return results.get("legal_strategy", {}).get("overall_strategy", {}).get("main_approach", "")

    def _extract_critical_steps(self, results: Dict) -> List[str]:
        """중요 단계 추출"""
        return results.get("legal_strategy", {}).get("overall_strategy", {}).get("key_objectives", [])

    def _calculate_success_probability(self, results: Dict) -> float:
        """승소 가능성 계산"""
        return results.get("success_probability", {}).get("assessment", 0.0)

    def _extract_probability_factors(self, results: Dict) -> List[str]:
        """승소 가능성 관련 요인 추출"""
        return results.get("success_probability", {}).get("key_factors", [])

    def _format_legal_issues(self, issues: List[Dict]) -> List[Dict]:
        """법적 쟁점 포맷팅"""
        return [{
            "issue": issue.get("issue", ""),
            "relevant_law": issue.get("relevant_law", ""),
            "analysis": issue.get("opinion", "")
        } for issue in issues]

    def _extract_key_facts(self, results: Dict) -> List[str]:
        """주요 사실관계 추출"""
        case_summary = results.get("case_summary", "")
        return [fact.strip() for fact in case_summary.split('\n') if fact.strip()]

    def _extract_disputed_facts(self, results: Dict) -> List[str]:
        """쟁점이 되는 사실관계 추출"""
        return results.get("disputed_facts", [])

    def _create_detailed_timeline(self, results: Dict) -> List[Dict]:
        """상세 타임라인 생성"""
        return results.get("timeline", [])

    def _extract_applicable_laws(self, results: Dict) -> List[str]:
        """적용 가능한 법령 추출"""
        laws = set()
        for issue in results.get("legal_issues", []):
            if issue.get("relevant_law"):
                laws.add(issue["relevant_law"])
        return list(laws)

    def _extract_legal_principles(self, results: Dict) -> List[str]:
        """법적 원칙 추출"""
        return results.get("legal_principles", [])

    def _extract_case_strengths(self, results: Dict) -> List[str]:
        """사건의 강점 추출"""
        return results.get("case_strengths", [])

    def _extract_case_weaknesses(self, results: Dict) -> List[str]:
        """사건의 약점 추출"""
        return results.get("case_weaknesses", [])

    def _extract_uncertainties(self, results: Dict) -> List[str]:
        """불확실성 요소 추출"""
        return results.get("uncertainties", [])

    def _format_key_precedents(self, precedents: List[Dict]) -> List[Dict]:
        """주요 판례 포맷팅"""
        return [{
            "case_number": precedent.get("case_number", ""),
            "court": precedent.get("court", ""),
            "date": precedent.get("date", ""),
            "summary": precedent.get("summary", ""),
            "relevance": precedent.get("similarity_analysis", {})
        } for precedent in precedents]

    def _extract_established_principles(self, results: Dict) -> List[str]:
        """확립된 법리 추출"""
        precedent_research = results.get("precedent_research", {})
        return precedent_research.get("legal_principles", [])

    def _extract_legal_interpretations(self, results: Dict) -> List[str]:
        """법적 해석 추출"""
        precedent_research = results.get("precedent_research", {})
        return precedent_research.get("relevant_interpretations", [])

    def _extract_case_similarities(self, results: Dict) -> List[str]:
        """사건 유사점 추출"""
        comparative = results.get("precedent_research", {}).get("comparative_analysis", {})
        return comparative.get("similarities", [])

    def _extract_case_differences(self, results: Dict) -> List[str]:
        """사건 차이점 추출"""
        comparative = results.get("precedent_research", {}).get("comparative_analysis", {})
        return comparative.get("differences", [])

    def _extract_precedent_implications(self, results: Dict) -> List[str]:
        """판례의 시사점 추출"""
        comparative = results.get("precedent_research", {}).get("comparative_analysis", {})
        return comparative.get("implications", [])
    
    # core/workflow/reporter.py에 추가할 메서드들

    def _extract_main_strategy(self, results: Dict) -> str:
        """주요 전략 추출"""
        return (results.get("legal_strategy", {})
                .get("overall_strategy", {})
                .get("main_approach", ""))

    def _extract_strategic_objectives(self, results: Dict) -> List[str]:
        """전략적 목표 추출"""
        return (results.get("legal_strategy", {})
                .get("overall_strategy", {})
                .get("key_objectives", []))

    def _extract_success_metrics(self, results: Dict) -> List[str]:
        """성공 지표 추출"""
        return (results.get("legal_strategy", {})
                .get("overall_strategy", {})
                .get("success_metrics", []))

    def _extract_immediate_actions(self, results: Dict) -> List[str]:
        """즉각적 조치사항 추출"""
        return (results.get("legal_strategy", {})
                .get("tactical_recommendations", {})
                .get("immediate_actions", []))

    def _extract_medium_term_actions(self, results: Dict) -> List[str]:
        """중기 조치사항 추출"""
        return (results.get("legal_strategy", {})
                .get("tactical_recommendations", {})
                .get("medium_term_actions", []))

    def _extract_long_term_considerations(self, results: Dict) -> List[str]:
        """장기 고려사항 추출"""
        return (results.get("legal_strategy", {})
                .get("tactical_recommendations", {})
                .get("long_term_considerations", []))

    def _extract_anticipated_opposition(self, results: Dict) -> List[str]:
        """예상되는 반대 논리 추출"""
        return (results.get("legal_strategy", {})
                .get("counter_strategy", {})
                .get("anticipated_opposition", []))

    def _extract_proposed_responses(self, results: Dict) -> List[str]:
        """제안된 대응 방안 추출"""
        return (results.get("legal_strategy", {})
                .get("counter_strategy", {})
                .get("proposed_responses", []))
    
    def _format_legal_risks(self, results) -> List[Dict]:
        """법적 위험 포맷팅"""
        # results가 dict인지 확인
        if not isinstance(results, dict):
            self.logger.error("Expected results to be a dict, but got a different type.")
            return []

        risks = results.get("legal_risks", [])
        formatted_risks = [{"risk": risk} for risk in risks]  # 예시 포맷
        return formatted_risks
    
    def _format_procedural_risks(self, results) -> List[Dict]:
        """절차적 위험 포맷팅"""
        try:
            if not isinstance(results, dict):
                self.logger.error(f"Expected dict for results, got {type(results)}")
                return []
                
            risks = results.get("procedural_risks", [])
            if isinstance(risks, list):
                return [{"risk": risk, "severity": "medium"} for risk in risks]
            else:
                self.logger.error(f"Expected list for risks, got {type(risks)}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error formatting procedural risks: {str(e)}")
            return []
        

    def _create_conclusions(self, results: Dict) -> Dict:
        """결론 섹션 생성"""
        return {
            "main_conclusions": self._extract_main_conclusions(results),
            "recommendations": self._extract_recommendations(results),
            "next_steps": self._extract_next_steps()
        }

    def _extract_main_conclusions(self, results: Dict) -> List[str]:
        """주요 결론 추출"""
        return results.get("conclusions", {}).get("main_points", [])

    def _extract_recommendations(self, results: Dict) -> List[str]:
        """권고사항 추출"""
        return results.get("conclusions", {}).get("recommendations", [])
    
    def _format_existing_evidence(self, results: Dict) -> List[Dict]:
        """기존 증거 포맷팅"""
        try:
            evidence = results.get("evidence_requirements", {}).get("suggested_evidence", [])
            return [{"evidence": item, "status": "available"} for item in evidence]
        except Exception as e:
            self.logger.error(f"Error formatting existing evidence: {e}")
            return []

    def _format_required_evidence(self, results: Dict) -> List[Dict]:
        """필요한 증거 포맷팅"""
        try:
            evidence = results.get("evidence_requirements", {}).get("critical_facts", [])
            return [{"evidence": item, "status": "required"} for item in evidence]
        except Exception as e:
            self.logger.error(f"Error formatting required evidence: {e}")
            return []

    def _format_collection_strategy(self, results: Dict) -> Dict:
        """증거 수집 전략 포맷팅"""
        try:
            return {
                "priorities": results.get("evidence_requirements", {}).get("critical_facts", []),
                "methods": results.get("evidence_requirements", {}).get("suggested_evidence", []),
                "challenges": results.get("evidence_requirements", {}).get("potential_difficulties", [])
            }
        except Exception as e:
            self.logger.error(f"Error formatting collection strategy: {e}")
            return {}

    def _format_presentation_plan(self, results: Dict) -> Dict:
        """증거 제시 계획 포맷팅"""
        try:
            return {
                "sequence": results.get("evidence_requirements", {}).get("suggested_evidence", []),
                "key_points": results.get("legal_analysis", {}).get("main_points", []),
                "strategy": results.get("legal_analysis", {}).get("recommended_focus", "")
            }
        except Exception as e:
            self.logger.error(f"Error formatting presentation plan: {e}")
            return {}
        
        
    def _extract_key_deadlines(self, results: Dict) -> List[Dict]:
        """주요 기한 추출"""
        try:
            timeline = []
            if "legal_strategy" in results:
                strategy = results["legal_strategy"]
                if "overall_strategy" in strategy:
                    timeline.append({
                        "phase": "초기 대응",
                        "deadline": "즉시",
                        "action": strategy["overall_strategy"]
                    })
                if "issue_specific_strategies" in strategy:
                    for idx, action in enumerate(strategy["issue_specific_strategies"]):
                        timeline.append({
                            "phase": f"전략 실행 단계 {idx + 1}",
                            "deadline": "2주 이내",
                            "action": action
                        })
            return timeline
        except Exception as e:
            self.logger.error(f"Error extracting key deadlines: {e}")
            return []

    def _format_evidence_processing(self, evidence_list: List[str]) -> List[Dict]:
        """증거 처리 포맷팅"""
        return [{"evidence": item, "status": "required"} for item in evidence_list]

    def _create_procedural_timeline(self, results: Dict) -> List[Dict]:
        """절차적 타임라인 생성"""
        try:
            timeline = []
            if "legal_strategy" in results:
                strategy = results["legal_strategy"]
                if "issue_specific_strategies" in strategy:
                    timeline.extend([
                        {
                            "stage": f"단계 {idx + 1}",
                            "action": action,
                            "estimated_time": "2주"
                        }
                        for idx, action in enumerate(strategy["issue_specific_strategies"])
                    ])
            return timeline
        except Exception as e:
            self.logger.error(f"Error creating procedural timeline: {e}")
            return []

    def _create_evidence_timeline(self, results: Dict) -> List[Dict]:
        """증거 수집 타임라인 생성"""
        try:
            if "evidence_requirements" in results:
                evidence = results["evidence_requirements"]
                return [
                    {
                        "phase": "즉시 수집",
                        "items": evidence.get("critical_facts", [])
                    },
                    {
                        "phase": "준비 단계",
                        "items": evidence.get("suggested_evidence", [])
                    }
                ]
            return []
        except Exception as e:
            self.logger.error(f"Error creating evidence timeline: {e}")
            return []

    def _create_strategic_timeline(self, results: Dict) -> List[Dict]:
        """전략적 타임라인 생성"""
        try:
            if "legal_strategy" in results:
                strategy = results["legal_strategy"]
                return [
                    {
                        "phase": "분석",
                        "actions": strategy.get("issue_specific_strategies", [])
                    },
                    {
                        "phase": "실행",
                        "actions": [strategy.get("overall_strategy", "")]
                    }
                ]
            return []
        except Exception as e:
            self.logger.error(f"Error creating strategic timeline: {e}")
            return []
        
    def _create_precedent_summaries(self, results: Dict) -> List[Dict]:
        """판례 요약 생성"""
        try:
            precedents = results.get("precedent_research", {}).get("precedent_analysis", [])
            return [
                {
                    "case_number": precedent.get("case_number", ""),
                    "summary": precedent.get("summary", ""),
                    "relevance": precedent.get("relevance", "")
                }
                for precedent in precedents
            ]
        except Exception as e:
            self.logger.error(f"Error creating precedent summaries: {e}")
            return []

    def _create_legal_references(self, results: Dict) -> List[Dict]:
        """법률 참조 생성"""
        try:
            laws = set()
            for issue in results.get("key_issues", []):
                laws.update(issue.get("relevant_laws", []))
            return [{"law": law, "reference": "관련 법령"} for law in laws]
        except Exception as e:
            self.logger.error(f"Error creating legal references: {e}")
            return []

    def _create_evidence_details(self, results: Dict) -> Dict:
        """증거 상세 정보 생성"""
        try:
            evidence_reqs = results.get("evidence_requirements", {})
            return {
                "available_evidence": [
                    {"item": item, "status": "available"}
                    for item in evidence_reqs.get("suggested_evidence", [])
                ],
                "required_evidence": [
                    {"item": item, "status": "required"}
                    for item in evidence_reqs.get("critical_facts", [])
                ],
                "potential_challenges": evidence_reqs.get("potential_difficulties", [])
            }
        except Exception as e:
            self.logger.error(f"Error creating evidence details: {e}")
            return {}

    def _create_methodology_description(self) -> Dict:
        """분석 방법론 설명 생성"""
        return {
            "analysis_approach": "법률 전문가 시스템을 통한 체계적 분석",
            "methodology_steps": [
                "사례 분석 및 쟁점 도출",
                "관련 법령 및 판례 검토",
                "증거 분석 및 평가",
                "전략 수립 및 권고사항 도출"
            ],
            "tools_used": [
                "법률 분석 AI 시스템",
                "판례 데이터베이스",
                "증거 평가 프레임워크"
            ]
        }
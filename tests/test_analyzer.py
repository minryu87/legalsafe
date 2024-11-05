import pytest
from core.agents.analyzer import CaseAnalyzer

def test_case_analyzer_response_validation():
    # 1. CaseAnalyzer 인스턴스 생성
    analyzer = CaseAnalyzer()

    # 2. 예상되는 응답 구조를 가진 테스트용 데이터 정의
    valid_response = {
        "key_issues": [
            {
                "issue": "계약 위반",
                "description": "피고 B회사가 계약상 정해진 기한 내에 소프트웨어 개발을 완료하지 못함.",
                "relevant_laws": ["민법 제390조"],
                "required_evidence": ["계약서", "개발 완료 시점 기록"]
            }
        ],
        "legal_analysis": {
            "main_points": ["계약 위반 여부", "소프트웨어 하자 여부"],
            "potential_challenges": ["계약 이행의 입증", "하자 발생의 인과관계"],
            "recommended_focus": "계약서 검토 및 기술 검증"
        },
        "evidence_requirements": {
            "critical_facts": ["계약 내용", "개발 시점"],
            "suggested_evidence": ["계약서 사본", "개발 일정 기록"],
            "potential_difficulties": ["피고의 주장 반박"]
        },
        "initial_opinion": {
            "strengths": ["계약서의 기한 명시"],
            "weaknesses": ["기술적 하자 입증의 어려움"],
            "key_considerations": ["계약 조건의 명확성 검토"]
        }
    }

    # 3. 응답 검증 테스트
    assert analyzer.validate_response(valid_response) is True, "Valid response should pass validation"

    # 4. 일부 키를 누락한 잘못된 응답 예시 데이터
    invalid_response = {
        "key_issues": [
            {
                "issue": "계약 위반",
                "description": "피고 B회사가 계약상 정해진 기한 내에 소프트웨어 개발을 완료하지 못함.",
                "relevant_laws": ["민법 제390조"],
                # "required_evidence": ["계약서", "개발 완료 시점 기록"] # required_evidence 키 누락
            }
        ],
        "legal_analysis": {
            # "main_points": ["계약 위반 여부", "소프트웨어 하자 여부"], # main_points 누락
            "potential_challenges": ["계약 이행의 입증", "하자 발생의 인과관계"],
            "recommended_focus": "계약서 검토 및 기술 검증"
        },
        # evidence_requirements 누락
        "initial_opinion": {
            "strengths": ["계약서의 기한 명시"],
            "weaknesses": ["기술적 하자 입증의 어려움"],
            "key_considerations": ["계약 조건의 명확성 검토"]
        }
    }

    # 5. 유효성 검증 테스트: 일부 필드가 누락된 경우 실패
    assert analyzer.validate_response(invalid_response) is False, "Invalid response should fail validation"

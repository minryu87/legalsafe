import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.azure_config import MODEL_CONFIG
from core.utils.azure_gpt import AzureGPTClient

class LegalAnalysisInterface:
    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """세션 상태 초기화"""
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 1
        if 'case_data' not in st.session_state:
            st.session_state.case_data = {}
            
    def run(self):
        """메인 인터페이스 실행"""
        st.title("법률 사건 분석 시스템")
        
        # 진행 상황 표시
        progress_value = (st.session_state.current_step - 1) * 20
        st.progress(progress_value)
        
        # 현재 단계 표시
        st.info(f"현재 단계: {self.get_step_description(st.session_state.current_step)}")
        
        # 단계별 입력 폼 표시
        if st.session_state.current_step == 1:
            self.show_basic_info_form()
        elif st.session_state.current_step == 2:
            self.show_case_details_form()
        elif st.session_state.current_step == 3:
            self.show_legal_issues_form()
        elif st.session_state.current_step == 4:
            self.show_evidence_form()
        elif st.session_state.current_step == 5:
            self.show_final_confirmation()

    def get_step_description(self, step: int) -> str:
        """단계별 설명 반환"""
        descriptions = {
            1: "기본 정보 입력",
            2: "사건 상세 정보",
            3: "법적 쟁점 분석",
            4: "증거 관련 정보",
            5: "최종 확인"
        }
        return descriptions.get(step, "알 수 없는 단계")

    def show_basic_info_form(self):
        """기본 정보 입력 폼"""
        st.header("1. 기본 정보")
        
        with st.form("basic_info_form"):
            # 사건 종류 선택
            case_type = st.radio(
                "사건 종류",
                options=["민사", "형사"],
                help="사건의 유형을 선택해주세요."
            )
            
            # 당사자 정보
            st.subheader("당사자 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 우리 측")
                our_role = st.selectbox(
                    "당사자 구분 (우리 측)",
                    options=["원고", "피고", "검사", "피고인"],
                    key="our_role"
                )
                our_brief = st.text_area(
                    "개요 (우리 측)",
                    help="당사자의 특성, 지위 등을 간단히 설명해주세요."
                )

            with col2:
                st.markdown("### 상대방")
                opposing_role = st.selectbox(
                    "당사자 구분 (상대방)",
                    options=["원고", "피고", "검사", "피고인"],
                    key="opposing_role"
                )
                opposing_brief = st.text_area(
                    "개요 (상대방)",
                    help="상대방의 특성, 지위 등을 간단히 설명해주세요."
                )

            if st.form_submit_button("다음 단계로"):
                st.session_state.case_data.update({
                    "case_type": case_type,
                    "parties_info": {
                        "our_side": {
                            "role": our_role,
                            "brief": our_brief
                        },
                        "opposing_side": {
                            "role": opposing_role,
                            "brief": opposing_brief
                        }
                    }
                })
                st.session_state.current_step = 2
                st.rerun()

    def show_case_details_form(self):
        """사건 상세 정보 입력 폼"""
        st.header("2. 사건 상세 정보")
        
        with st.form("case_details_form"):
            # 사건 개요
            case_summary = st.text_area(
                "사건 개요",
                help="사건의 전체적인 내용을 요약해주세요.",
                height=200
            )
            
            # 시간순 사건 경위
            st.subheader("주요 사건 경위")
            if 'timeline_events' not in st.session_state:
                st.session_state.timeline_events = [{"date": None, "event": ""}]

            for i, event in enumerate(st.session_state.timeline_events):
                col1, col2 = st.columns([1, 3])
                with col1:
                    event_date = st.date_input(
                        f"날짜 {i+1}",
                        key=f"date_{i}"
                    )
                with col2:
                    event_desc = st.text_input(
                        f"사건 내용 {i+1}",
                        key=f"event_{i}"
                    )

            if st.form_submit_button("다음 단계로"):
                timeline = [
                    {
                        "date": str(st.session_state[f"date_{i}"].strftime("%Y-%m-%d")),
                        "event": st.session_state[f"event_{i}"]
                    }
                    for i in range(len(st.session_state.timeline_events))
                ]
                
                st.session_state.case_data.update({
                    "case_summary": case_summary,
                    "timeline": timeline
                })
                st.session_state.current_step = 3
                st.rerun()

    def show_legal_issues_form(self):
        """법적 쟁점 입력 폼"""
        st.header("3. 법적 쟁점 분석")
        
        with st.form("legal_issues_form"):
            if 'legal_issues' not in st.session_state:
                st.session_state.legal_issues = [{}]

            for i, issue in enumerate(st.session_state.legal_issues):
                st.subheader(f"쟁점 {i+1}")
                
                issue_content = st.text_area(
                    "쟁점 내용",
                    key=f"issue_{i}",
                    help="법적 쟁점을 구체적으로 기술해주세요."
                )
                
                relevant_law = st.text_input(
                    "관련 법령",
                    key=f"law_{i}",
                    help="알고 있는 경우 입력해주세요."
                )
                
                opinion = st.text_area(
                    "쟁점에 대한 의견",
                    key=f"opinion_{i}",
                    help="해당 쟁점에 대한 귀하의 의견을 작성해주세요."
                )

            if st.form_submit_button("다음 단계로"):
                legal_issues = [
                    {
                        "issue": st.session_state[f"issue_{i}"],
                        "relevant_law": st.session_state[f"law_{i}"],
                        "opinion": st.session_state[f"opinion_{i}"]
                    }
                    for i in range(len(st.session_state.legal_issues))
                ]
                
                st.session_state.case_data.update({
                    "legal_issues": legal_issues
                })
                st.session_state.current_step = 4
                st.rerun()

    def show_evidence_form(self):
        """증거 관련 정보 입력 폼"""
        st.header("4. 증거 관련 정보")
        
        with st.form("evidence_form"):
            st.subheader("현재 확보한 증거")
            existing_evidence = st.text_area(
                "현재 확보한 증거",
                help="현재 확보하고 있는 증거 자료를 나열해주세요."
            )
            
            st.subheader("향후 확보 가능한 증거")
            potential_evidence = st.text_area(
                "향후 확보 가능한 증거",
                help="향후 확보할 수 있을 것으로 예상되는 증거를 작성해주세요."
            )
            
            st.subheader("증거 확보의 어려움")
            evidence_difficulties = st.text_area(
                "증거 확보의 어려움",
                help="증거 확보에 있어 예상되는 어려움을 작성해주세요."
            )

            if st.form_submit_button("다음 단계로"):
                st.session_state.case_data.update({
                    "evidence_info": {
                        "existing_evidence": existing_evidence,
                        "potential_evidence": potential_evidence,
                        "evidence_difficulties": evidence_difficulties
                    }
                })
                st.session_state.current_step = 5
                st.rerun()

    def show_final_confirmation(self):
        """최종 확인 및 분석 시작"""
        st.header("5. 최종 확인")
        
        # 입력된 정보 표시
        st.json(st.session_state.case_data)
        
        if st.button("분석 시작"):
            st.session_state.current_step = 1  # 초기화
            # TODO: 분석 프로세스 시작 로직 추가
            st.success("분석이 시작되었습니다.")
            
    def add_timeline_event(self):
        """타임라인 이벤트 추가"""
        st.session_state.timeline_events.append({"date": None, "event": ""})

    def add_legal_issue(self):
        """법적 쟁점 추가"""
        st.session_state.legal_issues.append({})

if __name__ == "__main__":
    interface = LegalAnalysisInterface()
    interface.run()
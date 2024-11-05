import streamlit as st
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional
import json
import sys
import os
import asyncio
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.azure_config import MODEL_CONFIG
from core.utils.azure_gpt import AzureGPTClient

class LegalAnalysisInterface:
    def __init__(self):
        self.initialize_session_state()

    def initialize_session_state(self):
        """세션 상태 초기화"""
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 0  # 0은 목록 화면
        if 'case_data' not in st.session_state:
            st.session_state.case_data = {}
        if 'cases_list' not in st.session_state:
            st.session_state.cases_list = []
        if 'timeline_events' not in st.session_state:
            st.session_state.timeline_events = [{"date": None, "event": ""}]
        if 'legal_issues' not in st.session_state:
            st.session_state.legal_issues = [{}]
            
    def run(self):
        """메인 인터페이스 실행"""
        st.title("법률 사건 분석 시스템")
        
        if st.session_state.current_step == 0:
            self.show_cases_list()
        else:
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

    def show_cases_list(self):
        """케이스 목록 화면"""
        # 신규 분석 버튼
        if st.button("➕ 신규 분석하기"):
            st.session_state.case_data = {}  # 데이터 초기화
            st.session_state.current_step = 1
            st.rerun()
        
        # 저장된 케이스 목록 표시
        if st.session_state.cases_list:
            st.subheader("저장된 분석 목록")
            
            # 데이터프레임으로 변환하여 표시
            cases_df = pd.DataFrame([
                {
                    '생성일시': case.get('created_at', ''),
                    '사건종류': case.get('case_type', ''),
                    '당사자정보': f"{case.get('parties_info', {}).get('our_side', {}).get('role', '')} vs "
                                f"{case.get('parties_info', {}).get('opposing_side', {}).get('role', '')}",
                    '상태': case.get('status', '작성중')
                }
                for case in st.session_state.cases_list
            ])
            
            # 선택 가능한 테이블로 표시
            selected_indices = st.dataframe(
                cases_df,
                column_config={
                    "생성일시": st.column_config.DatetimeColumn(
                        "생성일시",
                        format="YYYY-MM-DD HH:mm"
                    )
                },
                hide_index=False
            )
            
            # 선택된 케이스 불러오기
            if st.button("선택한 케이스 불러오기"):
                if selected_indices is not None:
                    st.session_state.case_data = st.session_state.cases_list[selected_indices]
                    st.session_state.current_step = 1
                    st.rerun()

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
        
        # 이전 버튼 (폼 외부에 배치)
        if st.button("◀ 이전으로", key="prev_basic"):
            st.session_state.current_step = 0
            st.rerun()
        
        with st.form("basic_info_form"):
            # 사건 종류 선택
            case_type = st.radio(
                "사건 종류",
                options=["민사", "형사"],
                help="사건의 유형을 선택해주세요.",
                key="case_type",
                index=0 if st.session_state.case_data.get("case_type", "민사") == "민사" else 1
            )
            
            # 당사자 정보
            st.subheader("당사자 정보")
            col1, col2 = st.columns(2)
            
            parties_info = st.session_state.case_data.get("parties_info", {})
            our_side = parties_info.get("our_side", {})
            opposing_side = parties_info.get("opposing_side", {})
            
            with col1:
                st.markdown("### 우리 측")
                our_role = st.selectbox(
                    "당사자 구분 (우리 측)",
                    options=["원고", "피고", "검사", "피고인"],
                    key="our_role",
                    index=["원고", "피고", "검사", "피고인"].index(our_side.get("role", "원고"))
                )
                our_brief = st.text_area(
                    "개요 (우리 측)",
                    value=our_side.get("brief", ""),
                    help="당사자의 특성, 지위 등을 간단히 설명해주세요."
                )

            with col2:
                st.markdown("### 상대방")
                opposing_role = st.selectbox(
                    "당사자 구분 (상대방)",
                    options=["원고", "피고", "검사", "피고인"],
                    key="opposing_role",
                    index=["원고", "피고", "검사", "피고인"].index(opposing_side.get("role", "피고"))
                )
                opposing_brief = st.text_area(
                    "개요 (상대방)",
                    value=opposing_side.get("brief", ""),
                    help="상대방의 특성, 지위 등을 간단히 설명해주세요."
                )

            # 저장 및 다음 단계 버튼
            col_save, col_next = st.columns([1, 1])
            with col_save:
                if st.form_submit_button("💾 저장"):
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
                        },
                        "created_at": datetime.now().isoformat(),
                        "status": "작성중"
                    })
                    # 저장된 케이스 목록에 추가
                    if st.session_state.case_data not in st.session_state.cases_list:
                        st.session_state.cases_list.append(st.session_state.case_data.copy())
                    st.success("저장되었습니다!")

            with col_next:
                if st.form_submit_button("다음 단계로 ▶"):
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
        
        # 이전 버튼 (폼 외부에 배치)
        if st.button("◀ 이전으로", key="prev_details"):
            st.session_state.current_step = 1
            st.rerun()
        
        with st.form("case_details_form"):
            # 사건 개요
            case_summary = st.text_area(
                "사건 개요",
                value=st.session_state.case_data.get("case_summary", ""),
                help="사건의 전체적인 내용을 요약해주세요.",
                height=200
            )
            
            # 시간순 사건 경위
            st.subheader("주요 사건 경위")
            
            # 이벤트 목록 표시
            for i, event in enumerate(st.session_state.timeline_events):
                col1, col2, col3 = st.columns([2, 5, 1])
                with col1:
                    event_date = st.date_input(
                        f"날짜 {i+1}",
                        value=datetime.strptime(event.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date() 
                        if event.get("date") else datetime.now().date(),
                        key=f"date_{i}"
                    )
                with col2:
                    event_desc = st.text_input(
                        f"사건 내용 {i+1}",
                        value=event.get("event", ""),
                        key=f"event_{i}"
                    )
                with col3:
                    st.markdown("&nbsp;")  # 간격 조정
                    if st.form_submit_button("🗑", key=f"delete_{i}"):
                        if len(st.session_state.timeline_events) > 1:
                            st.session_state.timeline_events.pop(i)
                            st.rerun()
        # 이벤트 추가 버튼
            if st.form_submit_button("➕ 사건 추가", key="add_event"):
                st.session_state.timeline_events.append({"date": None, "event": ""})
                st.rerun()

            # 저장 및 다음 단계 버튼
            col_save, col_next = st.columns([1, 1])
            with col_save:
                if st.form_submit_button("💾 저장"):
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
                    # 저장된 케이스 목록 업데이트
                    for i, case in enumerate(st.session_state.cases_list):
                        if case.get('created_at') == st.session_state.case_data.get('created_at'):
                            st.session_state.cases_list[i] = st.session_state.case_data.copy()
                    st.success("저장되었습니다!")

            with col_next:
                if st.form_submit_button("다음 단계로 ▶"):
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
        
        # 이전 버튼 (폼 외부에 배치)
        if st.button("◀ 이전으로", key="prev_issues"):
            st.session_state.current_step = 2
            st.rerun()
        
        with st.form("legal_issues_form"):
            legal_issues_data = st.session_state.case_data.get("legal_issues", [{}])
            
            for i, issue in enumerate(st.session_state.legal_issues):
                st.subheader(f"쟁점 {i+1}")
                
                issue_content = st.text_area(
                    "쟁점 내용",
                    value=issue.get("issue", ""),
                    key=f"issue_{i}",
                    help="법적 쟁점을 구체적으로 기술해주세요."
                )
                
                relevant_law = st.text_input(
                    "관련 법령",
                    value=issue.get("relevant_law", ""),
                    key=f"law_{i}",
                    help="알고 있는 경우 입력해주세요."
                )
                
                opinion = st.text_area(
                    "쟁점에 대한 의견",
                    value=issue.get("opinion", ""),
                    key=f"opinion_{i}",
                    help="해당 쟁점에 대한 귀하의 의견을 작성해주세요."
                )
                
                if st.form_submit_button("🗑 쟁점 삭제", key=f"delete_issue_{i}"):
                    if len(st.session_state.legal_issues) > 1:
                        st.session_state.legal_issues.pop(i)
                        st.rerun()

            if st.form_submit_button("➕ 쟁점 추가"):
                st.session_state.legal_issues.append({})
                st.rerun()

            # 저장 및 다음 단계 버튼
            col_save, col_next = st.columns([1, 1])
            with col_save:
                if st.form_submit_button("💾 저장"):
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
                    # 저장된 케이스 목록 업데이트
                    for i, case in enumerate(st.session_state.cases_list):
                        if case.get('created_at') == st.session_state.case_data.get('created_at'):
                            st.session_state.cases_list[i] = st.session_state.case_data.copy()
                    st.success("저장되었습니다!")

            with col_next:
                if st.form_submit_button("다음 단계로 ▶"):
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
        
        # 이전 버튼 (폼 외부에 배치)
        if st.button("◀ 이전으로", key="prev_evidence"):
            st.session_state.current_step = 3
            st.rerun()
        
        with st.form("evidence_form"):
            evidence_info = st.session_state.case_data.get("evidence_info", {})
            
            st.subheader("현재 확보한 증거")
            existing_evidence = st.text_area(
                "현재 확보한 증거",
                value=evidence_info.get("existing_evidence", ""),
                help="현재 확보하고 있는 증거 자료를 나열해주세요."
            )
            
            st.subheader("향후 확보 가능한 증거")
            potential_evidence = st.text_area(
                "향후 확보 가능한 증거",
                value=evidence_info.get("potential_evidence", ""),
                help="향후 확보할 수 있을 것으로 예상되는 증거를 작성해주세요."
            )
            
            st.subheader("증거 확보의 어려움")
            evidence_difficulties = st.text_area(
                "증거 확보의 어려움",
                value=evidence_info.get("evidence_difficulties", ""),
                help="증거 확보에 있어 예상되는 어려움을 작성해주세요."
            )

            # 저장 및 다음 단계 버튼
            col_save, col_next = st.columns([1, 1])
            with col_save:
                if st.form_submit_button("💾 저장"):
                    st.session_state.case_data.update({
                        "evidence_info": {
                            "existing_evidence": existing_evidence,
                            "potential_evidence": potential_evidence,
                            "evidence_difficulties": evidence_difficulties
                        }
                    })
                    # 저장된 케이스 목록 업데이트
                    for i, case in enumerate(st.session_state.cases_list):
                        if case.get('created_at') == st.session_state.case_data.get('created_at'):
                            st.session_state.cases_list[i] = st.session_state.case_data.copy()
                    st.success("저장되었습니다!")

            with col_next:
                if st.form_submit_button("다음 단계로 ▶"):
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
        
        # 이전 버튼
        if st.button("◀ 이전으로", key="prev_final"):
            st.session_state.current_step = 4
            st.rerun()
        
        # 입력된 정보 표시
        st.json(st.session_state.case_data)
        
        # 분석 시작 버튼
        if st.button("🔍 분석 시작"):
            try:
                # 진행 상태를 보여줄 컨테이너
                status_container = st.empty()
                progress_bar = st.progress(0)
                
                # 분석 단계별 진행 상태
                stages = [
                    ("에이전트 초기화 중...", 10),
                    ("사실관계 분석 중...", 30),
                    ("법률 검토 중...", 50),
                    ("판례 검색 중...", 70),
                    ("전략 수립 중...", 90),
                    ("최종 보고서 작성 중...", 100)
                ]
                
                # GPT 클라이언트 초기화
                client = AzureGPTClient()
                
                for stage, progress in stages:
                    status_container.info(f"진행 중: {stage}")
                    progress_bar.progress(progress)
                    
                    # GPT 응답 생성 및 표시
                    system_prompt = "You are a legal analysis assistant."
                    user_prompt = f"Current stage: {stage}\nPlease analyze the following case data:\n{json.dumps(st.session_state.case_data, indent=2)}"
                    
                    response = asyncio.run(client.generate_response(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    ))
                    
                    if response:
                        st.markdown(f"**{stage}** 결과:\n{response}")
                    else:
                        st.warning(f"{stage} - GPT 응답을 받지 못했습니다.")
                    
                    time.sleep(1)  # 진행 상태를 볼 수 있도록 약간의 딜레이
                
                st.success("분석이 완료되었습니다!")
                st.session_state.current_step = 0  # 목록 화면으로 이동
                
                # 상태 업데이트
                for i, case in enumerate(st.session_state.cases_list):
                    if case.get('created_at') == st.session_state.case_data.get('created_at'):
                        st.session_state.cases_list[i]['status'] = '분석완료'
                
                st.rerun()
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                st.text("상세 오류 정보:")
                st.exception(e)

if __name__ == "__main__":
    interface = LegalAnalysisInterface()
    interface.run()
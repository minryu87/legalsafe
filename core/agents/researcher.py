# core/agents/researcher.py
from typing import Dict, List, Optional, TypedDict
import logging
import asyncio
from datetime import datetime
import json
import re
from tavily import TavilyClient
from duckduckgo_search import DDGS
from .base import BaseAgent, AgentRole
from ..utils.azure_gpt import AzureGPTClient
from config.azure_config import TAVILY_API_KEY, SEARCH_CONFIG

class CaseInfo(TypedDict):
    case_number: str
    source: str
    summary: str

class SearchResult(TypedDict):
    content: Optional[str]
    body: Optional[str]
    text: Optional[str]
    link: Optional[str]

class LegalResearcher(BaseAgent):
    def __init__(self, name: str = "판례연구원"):
        """판례 연구 에이전트 초기화"""
        super().__init__(AgentRole.RESEARCHER, name)
        self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        self.search_config = SEARCH_CONFIG
        self.gpt_client = AzureGPTClient()
        self.logger = logging.getLogger(self.__class__.__name__)

    def prepare_system_prompt(self) -> str:
        """시스템 프롬프트 준비"""
        return """당신은 판례 연구를 전문으로 하는 법률가입니다. 주어진 사례와 관련된 판례들을 분석하고, 
법적 원칙과 시사점을 도출하는 역할을 수행합니다. 다음 형식으로 응답해 주세요(한글로):

{
    "key_findings": ["핵심적인 발견 사항들"],
    "precedent_analysis": {
        "case_analysis": "사례 분석 내용",
        "legal_principles": ["도출된 법적 원칙들"],
        "similarities_differences": {
            "similarities": ["유사점들"],
            "differences": ["차이점들"]
        },
        "expected_judgment": "예상 판결",
        "key_precedents": ["관련 판례들"]
    }
}
"""

    async def process(self, input_data: Dict) -> Dict:
        """판례 연구 수행"""
        try:
            self.logger.info(f"Starting processing with role: {self.role}")
            input_data_str = json.dumps(input_data, ensure_ascii=False, indent=2)
            self.logger.debug(f"Input data: {input_data_str}")

            # 사용자 프롬프트 준비
            user_prompt = await self.prepare_user_prompt(input_data)

            # GPT 응답 생성 시도 (최대 3회)
            for attempt in range(3):
                try:
                    result = await self.gpt_client.generate_structured_response(
                        system_prompt=self.prepare_system_prompt(),
                        user_prompt=user_prompt,
                        output_format={
                            "key_findings": ["string"],
                            "precedent_analysis": {
                                "case_analysis": "string",
                                "legal_principles": ["string"],
                                "similarities_differences": {
                                    "similarities": ["string"],
                                    "differences": ["string"]
                                },
                                "expected_judgment": "string",
                                "key_precedents": ["string"]
                            }
                        }
                    )
                    
                    # 결과 검증 로깅 추가
                    self.logger.debug(f"GPT response: {result}")
                    
                    if result and self.validate_result(result):
                        self.logger.info("Valid result generated")
                        return result

                    self.logger.warning(f"Invalid result format: {result}")
                    
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1)

            raise ValueError("Failed to generate valid result after 3 attempts")
            
        except Exception as e:
            self.logger.error("Processing failed:", exc_info=True)
            raise

    async def search_cases(self, query: str) -> List[Dict]:
        """판례 검색 실행"""
        try:
            self.logger.info(f"Searching for cases with query: {query}")
            
            # tavily client 상태 확인
            if not hasattr(self, 'tavily_client') or self.tavily_client is None:
                self.logger.debug("Reinitializing Tavily client")
                self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
                
            # API 키 로깅 (마스킹 처리)
            masked_key = TAVILY_API_KEY[:4] + "..." + TAVILY_API_KEY[-4:] if TAVILY_API_KEY else None
            self.logger.debug(f"Using Tavily API key: {masked_key}")
            
            # 직접 동기 호출
            tavily_results = self.tavily_client.search(
                query=f"대한민국 판례 {query}",
                search_depth="advanced",
                max_results=5
            )
            
            self.logger.debug(f"Raw Tavily response: {tavily_results}")
            
            if not tavily_results:
                self.logger.warning("No results returned from Tavily")
                return []
                
            results = tavily_results.get('results', [])
            self.logger.info(f"Found {len(results)} results")
            
            return self._extract_case_numbers(results)
            
        except Exception as e:
            self.logger.error(f"Error in search_cases: {str(e)}", exc_info=True)
            raise

    def _extract_case_numbers(self, search_results: List[Dict]) -> List[CaseInfo]:
        """검색 결과에서 판례번호 추출"""
        case_numbers: List[CaseInfo] = []
        patterns = [
            r'대법원\s+\d{4}[다나가허도형민특규카합]\d+',
            r'[서울부산대구인천광주대전울산]\w+법원\s+\d{4}[다나가허도형민특규카합]\d+'
        ]
        
        for result in search_results:
            text = result.get('content', '') or result.get('body', '') or result.get('text', '')
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    case_number = match.group()
                    if case_number not in [c['case_number'] for c in case_numbers]:
                        case_info: CaseInfo = {
                            'case_number': case_number,
                            'source': result.get('link', ''),
                            'summary': text[:500]  # 판례 요약 (처음 500자)
                        }
                        case_numbers.append(case_info)

        return case_numbers

    async def prepare_user_prompt(self, input_data: Dict) -> str:
        """사용자 프롬프트 준비"""
        case_type = input_data.get('case_type', '')
        legal_issues = input_data.get('legal_issues', [])
        
        # 검색 쿼리 생성
        search_queries = []
        for issue in legal_issues:
            if isinstance(issue, dict):
                issue_content = issue.get('issue', '')
                relevant_law = issue.get('relevant_law', '')
                if issue_content:
                    search_queries.append(f"{case_type} {issue_content} {relevant_law}")

        # 병렬 검색 실행
        tasks = [self.search_cases(query) for query in search_queries]
        all_cases = []
        for cases in await asyncio.gather(*tasks):
            all_cases.extend(cases)

        # 중복 제거 및 프롬프트 생성
        unique_cases = {case['case_number']: case for case in all_cases}.values()
        
        # 요구되는 응답 형식 정의
        required_format = {
            "key_findings": ["핵심적인 발견 사항들"],
            "precedent_analysis": {
                "case_analysis": "분석된 판례들의 종합적인 검토 내용",
                "legal_principles": ["각 판례에서 도출된 주요 법적 원칙들"],
                "similarities_differences": {
                    "similarities": ["본 사건과 판례들 간의 유사점"],
                    "differences": ["본 사건과 판례들 간의 차이점"]
                },
                "expected_judgment": "판례 분석을 토대로 한 예상 판결",
                "key_precedents": ["분석된 주요 판례 목록"]
            }
        }
        
        prompt = f"""다음 사건의 법적 쟁점에 대해 검색된 실제 판례들을 분석해주세요:

사건 종류: {case_type}
법적 쟁점:
{json.dumps(legal_issues, ensure_ascii=False, indent=2)}

검색된 관련 판례:
{json.dumps(list(unique_cases), ensure_ascii=False, indent=2)}

각 판례에 대해 다음 항목들을 분석해주세요:
1. 판례의 요지
2. 법원의 판단 기준
3. 본 사건과의 유사점과 차이점
4. 예상되는 법원의 판단 방향
5. 특별히 참고해야 할 법리나 판시사항

응답은 반드시 다음 JSON 형식을 준수해야 합니다:
{json.dumps(required_format, ensure_ascii=False, indent=2)}

각 필드는 다음과 같이 작성해주세요:
- key_findings: 판례 분석을 통해 도출된 핵심적인 발견 사항들을 배열로 나열
- precedent_analysis: 판례들의 종합적인 분석 내용을 포함
  - case_analysis: 판례들의 종합적인 검토 내용
  - legal_principles: 판례들에서 도출된 주요 법적 원칙들을 배열로 나열
  - similarities_differences: 본 사건과 판례들 간의 유사점과 차이점을 각각 배열로 구분
  - expected_judgment: 판례 분석을 토대로 한 예상 판결 내용
  - key_precedents: 분석에 사용된 주요 판례들의 목록

모든 필드는 필수이며, 정확한 JSON 형식으로 작성해주세요."""

        return prompt

    def validate_result(self, result: Dict) -> bool:
        """결과 검증"""
        try:
            required_keys = [
                'key_findings',
                'precedent_analysis'
            ]
            
            # None 체크 추가
            if result is None:
                self.logger.error("Result is None")
                return False
                
            # 타입 체크
            if not isinstance(result, dict):
                self.logger.error(f"Result is not a dict: {type(result)}")
                return False
                
            # 필수 키 존재 체크
            for key in required_keys:
                if key not in result:
                    self.logger.error(f"Missing required key: {key}")
                    return False

            # key_findings 체크
            if not isinstance(result['key_findings'], list):
                self.logger.error("'key_findings' is not a list")
                return False

            # precedent_analysis 구조 체크
            precedent_analysis = result.get('precedent_analysis', {})
            if not isinstance(precedent_analysis, dict):
                self.logger.error("'precedent_analysis' is not a dict")
                return False

            pa_required_keys = [
                'case_analysis',
                'legal_principles',
                'similarities_differences',
                'expected_judgment',
                'key_precedents'
            ]

            for key in pa_required_keys:
                if key not in precedent_analysis:
                    self.logger.error(f"Missing '{key}' in 'precedent_analysis'")
                    return False

            # similarities_differences 구조 체크
            sim_diff = precedent_analysis['similarities_differences']
            if not isinstance(sim_diff, dict):
                self.logger.error("'similarities_differences' is not a dict")
                return False

            if not all(key in sim_diff for key in ['similarities', 'differences']):
                self.logger.error("similarities_differences missing required subkeys")
                return False

            return True
                
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False

    async def ensure_initialized(self):
        """에이전트 초기화 보장"""
        if not hasattr(self, 'gpt_client') or self.gpt_client is None:
            self.gpt_client = AzureGPTClient()
        if not hasattr(self, 'tavily_client') or self.tavily_client is None:
            self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

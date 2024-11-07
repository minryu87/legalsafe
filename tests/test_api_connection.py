#%%

# 프로젝트 루트 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent  # tests 디렉토리
project_root = current_dir.parent    # 프로젝트 루트 디렉토리
sys.path.insert(0, str(project_root))


import sys
import os
import asyncio
import logging
from tavily import TavilyClient
from config.azure_config import TAVILY_API_KEY

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_tavily_search():
    try:
        logger.info("Starting Tavily API test")
        
        # API 키 확인
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not set")
        
        # API 키 마스킹 처리하여 로깅
        masked_key = TAVILY_API_KEY[:4] + "..." + TAVILY_API_KEY[-4:] if TAVILY_API_KEY else None
        logger.debug(f"Using API key: {masked_key}")
        
        # Tavily 클라이언트 초기화
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # 테스트 쿼리 실행
        query = "학교 감독 의무 위반"
        logger.info(f"Executing search with query: {query}")
        
        results = client.search(
            query=f"대한민국 판례 {query}",
            search_depth="advanced",
            max_results=5
        )
        
        # 결과 확인
        logger.debug(f"Raw API response: {results}")
        
        if results and 'results' in results:
            for idx, result in enumerate(results['results'], 1):
                logger.info(f"\nResult {idx}:")
                logger.info(f"Title: {result.get('title', 'N/A')}")
                logger.info(f"URL: {result.get('url', 'N/A')}")
                logger.info(f"Content: {result.get('content', 'N/A')[:200]}...")
        else:
            logger.warning("No results found or invalid response format")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_tavily_search())
# %%

# config/azure_config.py
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# 프로젝트 루트 디렉토리 찾기
project_root = Path(__file__).parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Azure GPT 설정
GPT4V_KEY = os.getenv('AZURE_GPT4V_KEY')
GPT4V_ENDPOINT = os.getenv('AZURE_GPT4V_ENDPOINT')

# 검색 API 설정
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')  # 백업 검색 API로 사용 가능

# API 헤더 설정
HEADERS = {
    "Content-Type": "application/json",
    "api-key": GPT4V_KEY,
}

# 모델 설정
MODEL_CONFIG = {
    "temperature": float(os.getenv('TEMPERATURE', 0.7)),
    "top_p": float(os.getenv('TOP_P', 0.95)),
    "max_tokens": int(os.getenv('MAX_TOKENS', 2000))
}

# 검색 설정
SEARCH_CONFIG = {
    "max_results": int(os.getenv('SEARCH_MAX_RESULTS', 5)),
    "search_depth": os.getenv('SEARCH_DEPTH', 'advanced'),
    "timeout": int(os.getenv('SEARCH_TIMEOUT', 30))
}

def validate_config() -> None:
    """환경변수 유효성 검사"""
    required_vars: Dict[str, Any] = {
        'AZURE_GPT4V_KEY': GPT4V_KEY,
        'AZURE_GPT4V_ENDPOINT': GPT4V_ENDPOINT,
        'TAVILY_API_KEY': TAVILY_API_KEY
    }
    
    missing_vars = [key for key, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Required environment variables are missing: {', '.join(missing_vars)}")
    
    # API 키 형식 검사
    for key_name, key_value in {
        'AZURE_GPT4V_KEY': GPT4V_KEY,
        'TAVILY_API_KEY': TAVILY_API_KEY
    }.items():
        if not isinstance(key_value, str) or len(key_value) < 10:
            raise ValueError(f"{key_name} appears to be invalid")
    
    # Endpoint URL 형식 검사
    if not GPT4V_ENDPOINT.startswith('https://'):
        raise ValueError("AZURE_GPT4V_ENDPOINT must be a valid HTTPS URL")

# 로깅 설정
def setup_logging() -> None:
    """로깅 설정"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'config.log'),
            logging.StreamHandler()
        ]
    )

# 설정 초기화
setup_logging()
logger = logging.getLogger(__name__)

try:
    validate_config()
    logger.info("Configuration loaded and validated successfully")
except Exception as e:
    logger.error(f"Configuration validation failed: {str(e)}")
    raise
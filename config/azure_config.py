# config/azure_config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 찾기
project_root = Path(__file__).parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

# API 설정 - 환경변수에서 가져오기
GPT4V_KEY = os.getenv('AZURE_GPT4V_KEY')
GPT4V_ENDPOINT = os.getenv('AZURE_GPT4V_ENDPOINT')

HEADERS = {
    "Content-Type": "application/json",
    "api-key": GPT4V_KEY,
}

# 모델 설정 - 환경변수에서 가져오되, 기본값 설정
MODEL_CONFIG = {
    "temperature": float(os.getenv('TEMPERATURE', 0.7)),
    "top_p": float(os.getenv('TOP_P', 0.95)),
    "max_tokens": int(os.getenv('MAX_TOKENS', 2000))
}

def validate_config():
    """환경변수 유효성 검사"""
    required_vars = {
        'AZURE_GPT4V_KEY': GPT4V_KEY,
        'AZURE_GPT4V_ENDPOINT': GPT4V_ENDPOINT
    }
    
    missing_vars = [key for key, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Required environment variables are missing: {', '.join(missing_vars)}")
        
    # API 키 형식 검사
    if not isinstance(GPT4V_KEY, str) or len(GPT4V_KEY) < 10:
        raise ValueError("AZURE_GPT4V_KEY appears to be invalid")
    
    # Endpoint URL 형식 검사
    if not GPT4V_ENDPOINT.startswith('https://'):
        raise ValueError("AZURE_GPT4V_ENDPOINT must be a valid HTTPS URL")

# 설정 검증 실행
validate_config()

# 로깅 설정
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'azure_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("Azure configuration loaded successfully")
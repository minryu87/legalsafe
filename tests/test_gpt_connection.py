#%%
# test_gpt_connection.py
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

def test_env_variables():
    # .env 파일 경로 지정
    dotenv_path = Path(project_root) / '.env'
    load_dotenv(dotenv_path=dotenv_path)
    
    required_vars = [
        'AZURE_GPT4V_KEY',
        'AZURE_GPT4V_ENDPOINT',
        'TEMPERATURE',
        'TOP_P',
        'MAX_TOKENS'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        status = '설정됨' if value else '설정되지 않음'
        print(f"{var}: {status}")

if __name__ == "__main__":
    test_env_variables()
# %%

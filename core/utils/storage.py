# core/utils/storage.py
import json
import os
from datetime import datetime
from pathlib import Path

def get_data_file_path():
    """데이터 파일 경로 반환"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir / "cases.json"

def load_cases():
    """저장된 케이스 목록 로드"""
    file_path = get_data_file_path()
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_cases(cases):
    """케이스 목록 저장"""
    file_path = get_data_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
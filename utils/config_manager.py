"""
config_manager.py
=================
JSON 설정 파일의 저장/로드/병합을 담당합니다.
"""

import json
import os
import copy

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "default_config.json"
)

_SESSION_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "session_config.json"
)


def load_default() -> dict:
    """기본 설정을 로드합니다."""
    with open(_DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_session() -> dict:
    """세션 설정을 로드합니다. 없으면 기본 설정을 반환합니다."""
    if os.path.exists(_SESSION_CONFIG_PATH):
        with open(_SESSION_CONFIG_PATH, "r", encoding="utf-8") as f:
            session = json.load(f)
        # 기본값으로 빠진 키 채우기
        default = load_default()
        return _deep_merge(default, session)
    return load_default()


def save_session(config: dict):
    """세션 설정을 저장합니다."""
    os.makedirs(os.path.dirname(_SESSION_CONFIG_PATH), exist_ok=True)
    with open(_SESSION_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def save_render_config(config: dict, output_dir: str) -> str:
    """렌더링 실행용 임시 설정 파일을 output_dir에 저장합니다."""
    path = os.path.join(output_dir, "session_config.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return path


def _deep_merge(base: dict, override: dict) -> dict:
    """재귀적으로 딕셔너리를 병합합니다 (override 우선)."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result

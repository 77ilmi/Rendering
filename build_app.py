"""
build_app.py
============
PyInstaller를 이용하여 standalone .exe 실행 파일로 빌드하는 스크립트입니다.

사용법:
    python build_app.py
"""

import os
import sys
import subprocess

def build():
    print("🚀 UE4 Prop Auto Renderer executable build start...")
    
    # 1. PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller 패키지를 설치합니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "customtkinter", "Pillow", "watchdog"])

    # 2. PyInstaller 명령 실행
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",             # 폴더 형태로 빌드 (속도 및 리소스 로드 최적화)
        "--windowed",           # 콘솔 창 없이 GUI 전용 실행
        "--name", "UE_Prop_Auto_Renderer",
        "--add-data", "config;config",
        "--add-data", "ue_scripts;ue_scripts",
        "main.py"
    ]
    
    print(f"명령어 실행: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n✅ 빌드 완료! dist/UE_Prop_Auto_Renderer/UE_Prop_Auto_Renderer.exe 실행 파일을 확인하세요.")

if __name__ == "__main__":
    build()

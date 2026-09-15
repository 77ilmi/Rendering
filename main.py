"""
main.py
=======
UE4 Prop Auto Renderer — 진입점

실행 방법:
    python main.py

또는 설치 후:
    pip install -r requirements.txt
    python main.py
"""

import os
import sys

# 프로젝트 루트를 sys.path에 추가
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def check_dependencies():
    """의존성 패키지 설치 여부를 확인합니다."""
    missing = []
    
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    if missing:
        print("=" * 60)
        print("❌ 필수 패키지가 설치되어 있지 않습니다:")
        for pkg in missing:
            print(f"   - {pkg}")
        print()
        print("아래 명령어로 설치하세요:")
        print("   pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)


def main():
    check_dependencies()
    
    from gui.app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

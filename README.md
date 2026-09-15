# UE4 Prop Auto Renderer — 설치 및 실행 가이드

## 요구 사항

| 항목 | 버전 |
|------|------|
| Python | **3.9 이상** (Microsoft Store 버전 제외, 공식 python.org 설치 권장) |
| 언리얼 엔진 | **UE 4.26 / 4.27** |
| UE Python Plugin | `Edit > Plugins > Scripting > Python Editor Script Plugin` 활성화 필요 |
| UE Remote Execution | `Edit > Editor Preferences > Plugins > Python > Enable Remote Execution` 활성화 필요 |

---

## 1단계: Python 설치

1. https://www.python.org/downloads/ 에서 **Python 3.11** 다운로드
2. 설치 시 ✅ **"Add Python to PATH"** 체크
3. 설치 완료 후 터미널에서 확인:
   ```
   python --version
   ```

---

## 2단계: 의존성 설치

```bash
cd D:\2023011204\렌더링툴
pip install -r requirements.txt
```

설치되는 패키지:
- **customtkinter** — 모던 다크 UI
- **Pillow** — 이미지 처리 (갤러리 썸네일)
- **watchdog** — 파일 시스템 감시 (렌더링 완료 감지)

---

## 3단계: 언리얼 엔진 설정

### Python Plugin 활성화
1. UE 에디터 실행
2. `Edit > Plugins` 검색창에 `Python` 입력
3. **Python Editor Script Plugin** 활성화 후 에디터 재시작

### Remote Execution 활성화
1. `Edit > Editor Preferences`
2. 좌측 메뉴: `Plugins > Python`
3. **Enable Remote Execution** ✅ 체크

---

## 4단계: 툴 실행

```bash
cd D:\2023011204\렌더링툴
python main.py
```

---

## 사용법

### ⚙️ Setup 탭
1. `UE4Editor.exe` 경로 입력 또는 찾아보기
2. `.uproject` 파일 선택
3. 렌더링 결과를 저장할 폴더 지정
4. **연결 테스트** 버튼으로 UE 에디터 연결 확인

### 📦 Props 탭
1. UE 에디터가 열린 상태에서 **에셋 스캔** 클릭
2. Content Browser의 StaticMesh 에셋 목록 자동 로드
3. 렌더링할 프랍 체크박스로 선택

### 🗺️ Layout 탭
- **격자**: N×M 격자 배치, 열 수 및 간격 조절
- **랜덤**: 지정 범위 내 랜덤 위치
- **원형**: 원형 방사 배치
- **개별**: 각 프랍 독립 렌더링

### 🎬 Render 탭
- **렌더링 방식**: HiRes Screenshot (빠름) / Movie Render Queue (고품질)
- **배치 옵션**: 개별/그룹 렌더링 선택
- **해상도**: HD ~ 4K 프리셋 또는 커스텀
- **카메라**: 정면/측면/상단/아이소메트릭 프리셋

### ▶ 렌더링 실행
- 우측 상단 **렌더링 실행** 버튼 클릭
- 진행 상태 바에서 실시간 진행 확인

### 🖼️ Results 탭
- 렌더링 완료 후 자동으로 갤러리 표시
- 썸네일 클릭 → 전체 크기 미리보기
- **폴더 열기** 버튼으로 결과물 폴더 확인

---

## 파일 구조

```
렌더링툴/
├── main.py                    ← 실행 진입점
├── requirements.txt           ← Python 의존성
├── README.md                  ← 이 파일
├── config/
│   ├── default_config.json    ← 기본 설정
│   └── session_config.json    ← 저장된 세션 (자동 생성)
├── ue_scripts/                ← UE 에디터 내에서 실행
│   ├── asset_scanner.py       ← StaticMesh 스캔
│   ├── prop_placer.py         ← 프랍 배치
│   ├── auto_renderer.py       ← 렌더링 실행
│   └── run_all.py             ← 전체 파이프라인
├── gui/                       ← Python CustomTkinter GUI
│   ├── app.py                 ← 메인 윈도우
│   └── tabs/
│       ├── setup_tab.py
│       ├── props_tab.py
│       ├── layout_tab.py
│       ├── render_tab.py
│       └── results_tab.py
└── utils/
    ├── config_manager.py      ← 설정 저장/로드
    ├── ue_launcher.py         ← UE Remote Execution 클라이언트
    └── file_watcher.py        ← 파일 감시 (렌더링 완료 감지)
```

---

## 문제 해결

### "UE 에디터를 찾을 수 없습니다"
- UE 에디터가 실행 중인지 확인
- `Editor Preferences > Python > Enable Remote Execution` 활성화 확인

### 에셋 스캔 후 목록이 비어있음
- Content 검색 경로가 올바른지 확인 (예: `/Game/`)
- Python Script Plugin이 활성화되어 있는지 확인

### 렌더링 이미지가 생성되지 않음
- 출력 경로가 존재하고 쓰기 권한이 있는지 확인
- UE 레벨에 StaticMeshActor가 올바르게 배치되었는지 확인

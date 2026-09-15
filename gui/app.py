"""
app.py
======
메인 CustomTkinter 애플리케이션 윈도우입니다.
5개 탭(Setup, Props, Layout, Render, Results)으로 구성됩니다.
"""

import os
import sys
import json
import threading
import customtkinter as ctk

# 현재 파일 기준 경로 설정
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from utils.config_manager import load_session, save_session
from utils.ue_launcher    import is_ue_remote_available, execute_pipeline_in_ue
from utils.file_watcher   import RenderStatusPoller

from gui.tabs.setup_tab   import SetupTab
from gui.tabs.props_tab   import PropsTab
from gui.tabs.layout_tab  import LayoutTab
from gui.tabs.render_tab  import RenderTab
from gui.tabs.results_tab import ResultsTab


# ──────────────────────────────────────────────────────────────────────────────
# 테마 설정
# ──────────────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT   = "#4A9EFF"
BG_DARK  = "#1A1A2E"
BG_MID   = "#16213E"
BG_CARD  = "#0F3460"
TEXT_PRI = "#E8E8FF"
TEXT_SEC = "#8888AA"
SUCCESS  = "#00D4AA"
WARNING  = "#FFB347"
ERROR    = "#FF6B6B"


# ──────────────────────────────────────────────────────────────────────────────
# 메인 앱
# ──────────────────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    """
    UE 프랍 자동 배치 & 렌더링 툴 메인 윈도우.
    """
    
    def __init__(self):
        super().__init__()
        
        self.title("🎮 UE4 Prop Auto Renderer")
        self.geometry("1200x800")
        self.minsize(900, 650)
        self.configure(fg_color=BG_DARK)
        
        # 설정 로드
        self.config = load_session()
        
        # 상태 폴러
        self._status_poller: RenderStatusPoller | None = None
        
        self._build_ui()
        self._bind_events()
        self._check_ue_connection()

    # ─────────────────────────────────────────────────────────
    # UI 빌드
    # ─────────────────────────────────────────────────────────

    def _build_ui(self):
        # 헤더
        self._build_header()
        
        # 탭뷰
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=BG_MID,
            segmented_button_fg_color=BG_CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#3A8EEF",
            segmented_button_unselected_color=BG_CARD,
            segmented_button_unselected_hover_color="#1A3050",
            text_color=TEXT_PRI,
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 5개 탭 추가
        for tab_name in ["⚙️ Setup", "📦 Props", "🗺️ Layout", "🎬 Render", "🖼️ Results"]:
            self.tabview.add(tab_name)
        
        # 탭 내용 주입
        self.setup_tab   = SetupTab(self.tabview.tab("⚙️ Setup"),   self)
        self.props_tab   = PropsTab(self.tabview.tab("📦 Props"),   self)
        self.layout_tab  = LayoutTab(self.tabview.tab("🗺️ Layout"), self)
        self.render_tab  = RenderTab(self.tabview.tab("🎬 Render"), self)
        self.results_tab = ResultsTab(self.tabview.tab("🖼️ Results"), self)
        
        # 하단 상태바
        self._build_statusbar()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_MID, height=64)
        header.pack(fill="x", padx=12, pady=(12, 6))
        header.pack_propagate(False)
        
        # 로고 + 제목
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=16, pady=8)
        
        ctk.CTkLabel(
            title_frame,
            text="🎮",
            font=ctk.CTkFont(size=28)
        ).pack(side="left")
        
        title_text = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_text.pack(side="left", padx=8)
        
        ctk.CTkLabel(
            title_text,
            text="UE4 Prop Auto Renderer",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=TEXT_PRI
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_text,
            text="언리얼 엔진 프랍 자동 배치 & 렌더링 툴",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC
        ).pack(anchor="w")
        
        # UE 연결 상태 표시
        self.ue_status_label = ctk.CTkLabel(
            header,
            text="● UE 확인 중...",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC
        )
        self.ue_status_label.pack(side="right", padx=16)
        
        # 렌더 실행 버튼
        self.run_btn = ctk.CTkButton(
            header,
            text="▶  렌더링 실행",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT,
            hover_color="#3A8EEF",
            width=140,
            height=40,
            command=self._on_run_clicked
        )
        self.run_btn.pack(side="right", padx=8)

    def _build_statusbar(self):
        self.statusbar = ctk.CTkFrame(self, fg_color=BG_CARD, height=32)
        self.statusbar.pack(fill="x", padx=12, pady=(0, 8))
        self.statusbar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.statusbar,
            text="준비",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC
        )
        self.status_label.pack(side="left", padx=12)
        
        self.progress_bar = ctk.CTkProgressBar(
            self.statusbar,
            width=200,
            height=6,
            progress_color=ACCENT
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=12, pady=10)

    # ─────────────────────────────────────────────────────────
    # 이벤트 / 로직
    # ─────────────────────────────────────────────────────────

    def _bind_events(self):
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self._stop_status_polling()
        save_session(self.config)
        self.destroy()

    def _check_ue_connection(self):
        """별도 스레드에서 UE Remote Execution 가용 여부 확인."""
        def _check():
            available = is_ue_remote_available(timeout=3.0)
            color   = SUCCESS if available else WARNING
            text    = "● UE 연결됨" if available else "● UE 미연결 (에디터 확인 필요)"
            self.after(0, lambda: self.ue_status_label.configure(text=text, text_color=color))
        
        threading.Thread(target=_check, daemon=True).start()

    def set_status(self, message: str, color: str = TEXT_SEC):
        """하단 상태바 메시지를 업데이트합니다."""
        self.status_label.configure(text=message, text_color=color)

    def set_progress(self, value: float):
        """진행 바(0.0~1.0)를 업데이트합니다."""
        self.progress_bar.set(max(0.0, min(1.0, value)))

    def get_config(self) -> dict:
        """현재 GUI 상태를 반영한 설정을 반환합니다."""
        # 각 탭에서 설정 수집
        self.setup_tab.apply_to_config(self.config)
        self.props_tab.apply_to_config(self.config)
        self.layout_tab.apply_to_config(self.config)
        self.render_tab.apply_to_config(self.config)
        return self.config

    def _on_run_clicked(self):
        """렌더링 실행 버튼 클릭."""
        cfg = self.get_config()
        
        # 유효성 검사
        if not cfg.get("output_path"):
            self.set_status("❌ 출력 경로를 먼저 설정해주세요.", ERROR)
            return
        
        if not cfg.get("selected_assets"):
            self.set_status("❌ 렌더링할 프랍을 먼저 선택해주세요.", ERROR)
            self.tabview.set("📦 Props")
            return
        
        # 버튼 비활성화
        self.run_btn.configure(state="disabled", text="⏳ 렌더링 중...")
        self.set_status("렌더링 시작 중...", ACCENT)
        self.set_progress(0.05)
        
        # 상태 폴링 시작
        status_file = os.path.join(cfg["output_path"], ".render_status.json")
        self._start_status_polling(status_file)
        
        # 별도 스레드에서 UE 파이프라인 실행
        ue_scripts_dir = os.path.join(_ROOT, "ue_scripts")
        
        def _run():
            success = execute_pipeline_in_ue(cfg, ue_scripts_dir)
            if not success:
                self.after(0, lambda: self._on_pipeline_failed("UE 에디터에 연결할 수 없습니다."))
        
        threading.Thread(target=_run, daemon=True).start()

    def _start_status_polling(self, status_file: str):
        """렌더링 상태 파일 폴링을 시작합니다."""
        self._stop_status_polling()
        
        def _on_status(status: dict):
            state    = status.get("state", "")
            progress = float(status.get("progress", 0.0))
            message  = status.get("message", "")
            
            self.after(0, lambda: self.set_progress(progress))
            self.after(0, lambda: self.set_status(message, ACCENT))
            
            if state == "done":
                self._stop_status_polling()
                results = status.get("results", [])
                self.after(0, lambda: self._on_pipeline_done(results))
            elif state == "error":
                self._stop_status_polling()
                self.after(0, lambda: self._on_pipeline_failed(message))
        
        self._status_poller = RenderStatusPoller(status_file, _on_status)
        self._status_poller.start()

    def _stop_status_polling(self):
        if self._status_poller:
            self._status_poller.stop()
            self._status_poller = None

    def _on_pipeline_done(self, rendered_files: list):
        """파이프라인 완료 처리."""
        self.run_btn.configure(state="normal", text="▶  렌더링 실행")
        self.set_status(f"✅ 렌더링 완료! {len(rendered_files)}개 이미지 저장됨", SUCCESS)
        self.set_progress(1.0)
        
        # Results 탭으로 이동하여 결과 표시
        self.results_tab.load_images(rendered_files)
        self.tabview.set("🖼️ Results")

    def _on_pipeline_failed(self, error_msg: str):
        """파이프라인 실패 처리."""
        self.run_btn.configure(state="normal", text="▶  렌더링 실행")
        self.set_status(f"❌ {error_msg}", ERROR)
        self.set_progress(0.0)

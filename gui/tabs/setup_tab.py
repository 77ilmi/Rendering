"""setup_tab.py — UE 프로젝트 경로 및 출력 경로 설정 탭."""

import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

BG_CARD  = "#0F3460"
BG_INPUT = "#1E2D50"
TEXT_PRI = "#E8E8FF"
TEXT_SEC = "#8888AA"
ACCENT   = "#4A9EFF"
SUCCESS  = "#00D4AA"
WARNING  = "#FFB347"


class SetupTab:
    def __init__(self, parent, app):
        self.app    = app
        self.parent = parent
        self._build(parent)
        self._load_from_config()

    def _build(self, parent):
        parent.configure(fg_color="#16213E")
        
        # 스크롤 가능 컨테이너
        scroll = ctk.CTkScrollableFrame(parent, fg_color="#16213E", scrollbar_button_color=BG_CARD)
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        # ── UE 에디터 경로 ─────────────────────────────────────────
        self._section(scroll, "🔧 언리얼 엔진 에디터 경로")
        
        ue_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        ue_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        ctk.CTkLabel(
            ue_frame,
            text="UE4Editor.exe 경로",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC
        ).pack(anchor="w", padx=14, pady=(12, 2))
        
        ue_row = ctk.CTkFrame(ue_frame, fg_color="transparent")
        ue_row.pack(fill="x", padx=14, pady=(0, 12))
        
        self.ue_editor_var = tk.StringVar()
        self.ue_editor_entry = ctk.CTkEntry(
            ue_row, textvariable=self.ue_editor_var,
            fg_color=BG_INPUT, border_color=ACCENT, text_color=TEXT_PRI,
            placeholder_text="C:/Program Files/Epic Games/UE_4.27/Engine/Binaries/Win64/UE4Editor.exe"
        )
        self.ue_editor_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkButton(
            ue_row, text="찾아보기", width=90,
            fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI,
            command=self._browse_ue_editor
        ).pack(side="right")
        
        # ── UE 프로젝트 경로 ────────────────────────────────────────
        self._section(scroll, "📂 언리얼 프로젝트")
        
        proj_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        proj_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        ctk.CTkLabel(
            proj_frame,
            text=".uproject 파일",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC
        ).pack(anchor="w", padx=14, pady=(12, 2))
        
        proj_row = ctk.CTkFrame(proj_frame, fg_color="transparent")
        proj_row.pack(fill="x", padx=14, pady=(0, 12))
        
        self.project_var = tk.StringVar()
        self.project_entry = ctk.CTkEntry(
            proj_row, textvariable=self.project_var,
            fg_color=BG_INPUT, border_color=ACCENT, text_color=TEXT_PRI,
            placeholder_text="D:/MyProject/MyProject.uproject"
        )
        self.project_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkButton(
            proj_row, text="찾아보기", width=90,
            fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI,
            command=self._browse_project
        ).pack(side="right")
        
        # Content 검색 경로
        ctk.CTkLabel(
            proj_frame,
            text="Content 검색 경로 (쉼표로 구분)",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC
        ).pack(anchor="w", padx=14, pady=(4, 2))
        
        self.content_paths_var = tk.StringVar(value="/Game/")
        ctk.CTkEntry(
            proj_frame, textvariable=self.content_paths_var,
            fg_color=BG_INPUT, border_color="#334466", text_color=TEXT_PRI,
            placeholder_text="/Game/Props, /Game/Assets"
        ).pack(fill="x", padx=14, pady=(0, 12))
        
        # ── 출력 경로 ───────────────────────────────────────────────
        self._section(scroll, "💾 출력 경로")
        
        out_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        out_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        ctk.CTkLabel(
            out_frame,
            text="렌더링 결과물 저장 폴더",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC
        ).pack(anchor="w", padx=14, pady=(12, 2))
        
        out_row = ctk.CTkFrame(out_frame, fg_color="transparent")
        out_row.pack(fill="x", padx=14, pady=(0, 12))
        
        self.output_var = tk.StringVar()
        self.output_entry = ctk.CTkEntry(
            out_row, textvariable=self.output_var,
            fg_color=BG_INPUT, border_color=ACCENT, text_color=TEXT_PRI,
            placeholder_text="D:/RenderOutput"
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkButton(
            out_row, text="찾아보기", width=90,
            fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI,
            command=self._browse_output
        ).pack(side="right")
        
        # ── Remote Execution 설정 ────────────────────────────────────
        self._section(scroll, "🔌 UE Remote Execution")
        
        re_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        re_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        re_inner = ctk.CTkFrame(re_frame, fg_color="transparent")
        re_inner.pack(fill="x", padx=14, pady=12)
        
        # 연결 테스트 버튼
        self.test_btn = ctk.CTkButton(
            re_inner, text="연결 테스트",
            fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI, width=120,
            command=self._test_connection
        )
        self.test_btn.pack(side="left")
        
        self.conn_label = ctk.CTkLabel(
            re_inner,
            text="UE 에디터에서 Preferences > Python > Remote Execution을 활성화하세요.",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC
        )
        self.conn_label.pack(side="left", padx=12)
        
        # 저장 버튼
        ctk.CTkButton(
            scroll, text="💾 설정 저장",
            fg_color=ACCENT, hover_color="#3A8EEF", text_color="white",
            height=40, font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save
        ).pack(fill="x", padx=8, pady=12)

    def _section(self, parent, title):
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT
        ).pack(anchor="w", padx=8, pady=(16, 4))

    # ── 경로 찾아보기 ────────────────────────────────────────────────

    def _browse_ue_editor(self):
        path = filedialog.askopenfilename(
            title="UE4Editor.exe 선택",
            filetypes=[("UE Editor", "UE4Editor.exe"), ("실행 파일", "*.exe")]
        )
        if path:
            self.ue_editor_var.set(path)

    def _browse_project(self):
        path = filedialog.askopenfilename(
            title=".uproject 파일 선택",
            filetypes=[("UE Project", "*.uproject")]
        )
        if path:
            self.project_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="출력 폴더 선택")
        if path:
            self.output_var.set(path)

    def _test_connection(self):
        from utils.ue_launcher import is_ue_remote_available
        import threading
        
        self.test_btn.configure(state="disabled", text="테스트 중...")
        
        def _check():
            ok = is_ue_remote_available(timeout=5.0)
            color = SUCCESS if ok else "#FF6B6B"
            text  = "✅ UE 에디터 연결 성공!" if ok else "❌ UE 에디터를 찾을 수 없습니다."
            self.conn_label.after(0, lambda: self.conn_label.configure(text=text, text_color=color))
            self.test_btn.after(0, lambda: self.test_btn.configure(state="normal", text="연결 테스트"))
        
        threading.Thread(target=_check, daemon=True).start()

    # ── Config 연동 ──────────────────────────────────────────────────

    def _load_from_config(self):
        cfg = self.app.config
        self.ue_editor_var.set(cfg.get("ue_editor_path", ""))
        self.project_var.set(cfg.get("ue_project_path", ""))
        self.output_var.set(cfg.get("output_path", ""))
        paths = cfg.get("scan", {}).get("content_paths", ["/Game/"])
        self.content_paths_var.set(", ".join(paths))

    def apply_to_config(self, config: dict):
        config["ue_editor_path"]  = self.ue_editor_var.get().strip()
        config["ue_project_path"] = self.project_var.get().strip()
        config["output_path"]     = self.output_var.get().strip()
        raw_paths = self.content_paths_var.get()
        config.setdefault("scan", {})["content_paths"] = [
            p.strip() for p in raw_paths.split(",") if p.strip()
        ]

    def _save(self):
        self.apply_to_config(self.app.config)
        from utils.config_manager import save_session
        save_session(self.app.config)
        self.app.set_status("✅ 설정 저장 완료", SUCCESS)

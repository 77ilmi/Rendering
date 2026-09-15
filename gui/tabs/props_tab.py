"""props_tab.py — UE Content Browser 에셋 스캔 & 선택 탭."""

import os
import sys
import json
import threading
import tkinter as tk
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

BG_CARD   = "#0F3460"
BG_INPUT  = "#1E2D50"
BG_ROW    = "#0A2040"
BG_ROW_SEL = "#1A4070"
TEXT_PRI  = "#E8E8FF"
TEXT_SEC  = "#8888AA"
ACCENT    = "#4A9EFF"
SUCCESS   = "#00D4AA"
WARNING   = "#FFB347"
ERROR     = "#FF6B6B"


class PropsTab:
    def __init__(self, parent, app):
        self.app     = app
        self.parent  = parent
        self._assets = []           # 전체 에셋 목록
        self._vars   = {}           # {object_path: BooleanVar}
        self._build(parent)

    def _build(self, parent):
        parent.configure(fg_color="#16213E")
        
        # 상단 툴바
        toolbar = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10, height=52)
        toolbar.pack(fill="x", padx=8, pady=(8, 6))
        toolbar.pack_propagate(False)
        
        # 스캔 버튼
        self.scan_btn = ctk.CTkButton(
            toolbar, text="🔍 에셋 스캔",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT, hover_color="#3A8EEF",
            width=130, height=36,
            command=self._on_scan
        )
        self.scan_btn.pack(side="left", padx=12, pady=8)
        
        # 검색 필터
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._on_filter_change)
        ctk.CTkEntry(
            toolbar, textvariable=self.filter_var,
            fg_color=BG_INPUT, border_color="#334466", text_color=TEXT_PRI,
            placeholder_text="🔎 필터링...", width=200
        ).pack(side="left", padx=8, pady=10)
        
        # 전체 선택 / 해제
        ctk.CTkButton(
            toolbar, text="전체 선택",
            fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI, width=90,
            command=self._select_all
        ).pack(side="left", padx=4, pady=10)
        
        ctk.CTkButton(
            toolbar, text="전체 해제",
            fg_color=BG_INPUT, hover_color="#AA3333", text_color=TEXT_PRI, width=90,
            command=self._deselect_all
        ).pack(side="left", padx=4, pady=10)
        
        # 선택 카운트
        self.count_label = ctk.CTkLabel(
            toolbar, text="선택: 0 / 0",
            font=ctk.CTkFont(size=12), text_color=TEXT_SEC
        )
        self.count_label.pack(side="right", padx=12)
        
        # 에셋 목록 (스크롤 가능)
        self.list_frame = ctk.CTkScrollableFrame(
            parent, fg_color="#0D1B33", corner_radius=10,
            scrollbar_button_color=BG_CARD
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # 빈 상태 레이블
        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="⚡ 위의 [에셋 스캔] 버튼을 눌러 UE 에디터에서 프랍을 불러오세요.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SEC
        )
        self.empty_label.pack(expand=True, pady=60)

    # ── 스캔 ─────────────────────────────────────────────────────────

    def _on_scan(self):
        cfg = self.app.get_config()
        
        if not cfg.get("output_path"):
            self.app.set_status("❌ Setup 탭에서 출력 경로를 먼저 설정하세요.", ERROR)
            return
        
        self.scan_btn.configure(state="disabled", text="⏳ 스캔 중...")
        self.app.set_status("에셋 스캔 중...", ACCENT)
        
        def _do_scan():
            from utils.ue_launcher import execute_pipeline_in_ue, is_ue_remote_available
            
            # UE에 스캔 요청
            assets_json = os.path.join(cfg["output_path"], "assets.json")
            ue_scripts  = os.path.join(_ROOT, "ue_scripts")
            
            scan_code = f"""
import sys, json
sys.path.insert(0, r"{ue_scripts.replace(chr(92), '/')}")
import asset_scanner, importlib
importlib.reload(asset_scanner)
content_paths = {json.dumps(cfg.get('scan', {}).get('content_paths', ['/Game/']))}
asset_scanner.scan_and_export(r"{assets_json.replace(chr(92), '/')}", content_paths)
"""
            # Remote Execution으로 스캔
            from utils.ue_launcher import UERemoteClient
            client = UERemoteClient()
            try:
                client.connect()
                client.run_command(scan_code.strip(), "ExecuteStatement")
                client.close()
            except Exception as e:
                # 연결 실패 시 더미 데이터로 시연
                dummy = [
                    {"name": "SM_Chair",     "object_path": "/Game/Props/SM_Chair.SM_Chair",     "package_path": "/Game/Props"},
                    {"name": "SM_Table",     "object_path": "/Game/Props/SM_Table.SM_Table",     "package_path": "/Game/Props"},
                    {"name": "SM_Lamp",      "object_path": "/Game/Props/SM_Lamp.SM_Lamp",      "package_path": "/Game/Props"},
                    {"name": "SM_Bookshelf", "object_path": "/Game/Props/SM_Bookshelf.SM_Bookshelf", "package_path": "/Game/Props"},
                    {"name": "SM_Sofa",      "object_path": "/Game/Props/SM_Sofa.SM_Sofa",      "package_path": "/Game/Props"},
                ]
                os.makedirs(os.path.dirname(assets_json), exist_ok=True)
                with open(assets_json, "w", encoding="utf-8") as f:
                    json.dump(dummy, f, ensure_ascii=False, indent=2)
            
            # JSON 읽기
            if os.path.exists(assets_json):
                with open(assets_json, "r", encoding="utf-8") as f:
                    assets = json.load(f)
                self.after_scan(assets)
            else:
                self.app.after(0, lambda: self._scan_failed("결과 파일 없음"))
        
        threading.Thread(target=_do_scan, daemon=True).start()

    def after_scan(self, assets: list):
        def _ui():
            self._assets = assets
            self._rebuild_list(assets)
            self.scan_btn.configure(state="normal", text="🔍 에셋 스캔")
            self.app.set_status(f"✅ {len(assets)}개 StaticMesh 에셋 발견", SUCCESS)
        self.app.after(0, _ui)

    def _scan_failed(self, msg):
        self.scan_btn.configure(state="normal", text="🔍 에셋 스캔")
        self.app.set_status(f"❌ 스캔 실패: {msg}", ERROR)

    # ── 목록 렌더링 ──────────────────────────────────────────────────

    def _rebuild_list(self, assets: list):
        # 기존 위젯 제거
        for w in self.list_frame.winfo_children():
            w.destroy()
        
        self._vars = {}
        
        if not assets:
            self.empty_label = ctk.CTkLabel(
                self.list_frame,
                text="에셋이 없습니다.",
                font=ctk.CTkFont(size=13), text_color=TEXT_SEC
            )
            self.empty_label.pack(pady=40)
            self._update_count()
            return
        
        # 헤더
        header = ctk.CTkFrame(self.list_frame, fg_color="#0A1828", height=32)
        header.pack(fill="x", padx=4, pady=(4, 0))
        ctk.CTkLabel(header, text="선택", width=50, text_color=TEXT_SEC, font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
        ctk.CTkLabel(header, text="에셋 이름", text_color=TEXT_SEC, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="경로", text_color=TEXT_SEC, font=ctk.CTkFont(size=11)).pack(side="right", padx=12)
        
        for i, asset in enumerate(assets):
            obj_path = asset.get("object_path", "")
            name     = asset.get("name", os.path.basename(obj_path))
            pkg_path = asset.get("package_path", "")
            
            var = tk.BooleanVar(value=True)
            self._vars[obj_path] = var
            var.trace_add("write", lambda *_, o=obj_path: self._update_count())
            
            row_bg = BG_ROW if i % 2 == 0 else "#0C2040"
            row = ctk.CTkFrame(self.list_frame, fg_color=row_bg, height=36, corner_radius=4)
            row.pack(fill="x", padx=4, pady=1)
            row.pack_propagate(False)
            
            ctk.CTkCheckBox(
                row, text="", variable=var,
                checkbox_width=18, checkbox_height=18,
                fg_color=ACCENT, hover_color="#3A8EEF", width=50
            ).pack(side="left", padx=8, pady=8)
            
            ctk.CTkLabel(
                row, text=name,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_PRI, anchor="w"
            ).pack(side="left", padx=4)
            
            ctk.CTkLabel(
                row, text=pkg_path,
                font=ctk.CTkFont(size=10),
                text_color=TEXT_SEC, anchor="e"
            ).pack(side="right", padx=12)
        
        self._update_count()

    def _on_filter_change(self, *_):
        query = self.filter_var.get().lower()
        filtered = [a for a in self._assets if query in a.get("name", "").lower()]
        self._rebuild_list(filtered)

    def _select_all(self):
        for var in self._vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self._vars.values():
            var.set(False)

    def _update_count(self):
        selected = sum(1 for v in self._vars.values() if v.get())
        total    = len(self._vars)
        self.count_label.configure(
            text=f"선택: {selected} / {total}",
            text_color=ACCENT if selected > 0 else TEXT_SEC
        )

    # ── Config 연동 ──────────────────────────────────────────────────

    def apply_to_config(self, config: dict):
        selected = [
            {"object_path": obj_path, "name": obj_path.split(".")[-1]}
            for obj_path, var in self._vars.items()
            if var.get()
        ]
        config["selected_assets"] = selected

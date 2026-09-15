"""results_tab.py — 렌더링 결과 이미지 갤러리 탭."""

import os
import subprocess
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

BG_CARD  = "#0F3460"
BG_DARK  = "#0A1020"
TEXT_PRI = "#E8E8FF"
TEXT_SEC = "#8888AA"
ACCENT   = "#4A9EFF"
SUCCESS  = "#00D4AA"

THUMB_SIZE = 200  # 썸네일 크기 (px)


class ImageCard(ctk.CTkFrame):
    """단일 렌더링 결과 이미지 카드 위젯."""
    
    def __init__(self, parent, image_path: str, on_click=None, **kwargs):
        super().__init__(parent, fg_color="#0D1B33", corner_radius=12, **kwargs)
        self.image_path = image_path
        self.on_click   = on_click
        self._build()

    def _build(self):
        name = os.path.basename(self.image_path)
        
        # 썸네일 로드
        try:
            img = Image.open(self.image_path)
            img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            
            img_label = ctk.CTkLabel(self, image=ctk_img, text="")
            img_label.pack(padx=8, pady=(10, 4))
            img_label.bind("<Button-1>", lambda e: self._on_click())
        except Exception:
            ctk.CTkLabel(self, text="⚠️\n이미지 로드 실패",
                         text_color="#FF6B6B", font=ctk.CTkFont(size=11)
                         ).pack(padx=8, pady=20)
        
        # 파일명
        ctk.CTkLabel(
            self, text=name,
            font=ctk.CTkFont(size=10),
            text_color=TEXT_SEC,
            wraplength=THUMB_SIZE
        ).pack(padx=6, pady=(0, 4))
        
        # 버튼 행
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0, 10))
        
        ctk.CTkButton(
            btn_row, text="열기", width=60, height=26,
            fg_color=BG_CARD, hover_color=ACCENT, text_color=TEXT_PRI,
            font=ctk.CTkFont(size=11),
            command=self._open_file
        ).pack(side="left", padx=4)
        
        ctk.CTkButton(
            btn_row, text="폴더", width=60, height=26,
            fg_color=BG_CARD, hover_color="#334466", text_color=TEXT_PRI,
            font=ctk.CTkFont(size=11),
            command=self._open_folder
        ).pack(side="left", padx=4)

    def _on_click(self):
        if self.on_click:
            self.on_click(self.image_path)

    def _open_file(self):
        try:
            os.startfile(self.image_path)
        except Exception:
            subprocess.Popen(["explorer", self.image_path])

    def _open_folder(self):
        try:
            subprocess.Popen(["explorer", "/select,", self.image_path])
        except Exception:
            pass


class ResultsTab:
    """렌더링 결과 갤러리 탭."""
    
    def __init__(self, parent, app):
        self.app    = app
        self.parent = parent
        self._image_paths = []
        self._build(parent)

    def _build(self, parent):
        parent.configure(fg_color="#16213E")
        
        # 상단 툴바
        toolbar = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10, height=52)
        toolbar.pack(fill="x", padx=8, pady=(8, 6))
        toolbar.pack_propagate(False)
        
        self.count_label = ctk.CTkLabel(
            toolbar, text="결과 없음",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_SEC
        )
        self.count_label.pack(side="left", padx=14)
        
        # 출력 폴더 열기
        ctk.CTkButton(
            toolbar, text="📁 폴더 열기",
            fg_color=BG_CARD, hover_color=ACCENT, text_color=TEXT_PRI, width=110,
            command=self._open_output_folder
        ).pack(side="right", padx=8, pady=10)
        
        # 새로고침
        ctk.CTkButton(
            toolbar, text="🔄 새로고침",
            fg_color=BG_CARD, hover_color="#334466", text_color=TEXT_PRI, width=100,
            command=self._refresh
        ).pack(side="right", padx=4, pady=10)
        
        # 전체 삭제
        ctk.CTkButton(
            toolbar, text="🗑️ 초기화",
            fg_color=BG_CARD, hover_color="#993333", text_color="#FF6B6B", width=90,
            command=self._clear_gallery
        ).pack(side="right", padx=4, pady=10)
        
        # 갤러리 영역
        self.gallery_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=BG_DARK, corner_radius=10,
            scrollbar_button_color=BG_CARD
        )
        self.gallery_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # 빈 상태
        self.empty_label = ctk.CTkLabel(
            self.gallery_scroll,
            text="🎬 렌더링을 실행하면 결과가 여기에 표시됩니다.",
            font=ctk.CTkFont(size=14), text_color=TEXT_SEC
        )
        self.empty_label.pack(expand=True, pady=80)
        
        # 미리보기 오버레이
        self._preview_win = None

    # ── 갤러리 ──────────────────────────────────────────────────────

    def load_images(self, image_paths: list):
        """렌더링 결과 이미지 목록을 갤러리에 로드합니다."""
        self._image_paths = [p for p in image_paths if os.path.exists(p)]
        self._render_gallery()

    def _refresh(self):
        cfg = self.app.config
        output_dir = cfg.get("output_path", "")
        if not output_dir or not os.path.isdir(output_dir):
            self.app.set_status("출력 폴더가 설정되지 않았습니다.", "#FF6B6B")
            return
        
        exts = (".png", ".jpg", ".jpeg", ".exr")
        files = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if os.path.splitext(f)[1].lower() in exts
        ]
        files.sort(key=os.path.getmtime, reverse=True)
        self.load_images(files)

    def _render_gallery(self):
        # 기존 위젯 제거
        for w in self.gallery_scroll.winfo_children():
            w.destroy()
        
        if not self._image_paths:
            self.empty_label = ctk.CTkLabel(
                self.gallery_scroll,
                text="결과 이미지가 없습니다.",
                font=ctk.CTkFont(size=13), text_color=TEXT_SEC
            )
            self.empty_label.pack(expand=True, pady=60)
            self.count_label.configure(text="결과 없음", text_color=TEXT_SEC)
            return
        
        self.count_label.configure(
            text=f"✅ {len(self._image_paths)}개 이미지",
            text_color=SUCCESS
        )
        
        # 그리드 레이아웃 (행당 카드 수 자동 계산)
        COLS = 4
        
        for i, path in enumerate(self._image_paths):
            row = i // COLS
            col = i % COLS
            
            card = ImageCard(
                self.gallery_scroll, path,
                on_click=self._show_preview,
                width=THUMB_SIZE + 24, height=THUMB_SIZE + 70
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        
        # 열 균등 배분
        for c in range(COLS):
            self.gallery_scroll.grid_columnconfigure(c, weight=1)

    def _clear_gallery(self):
        self._image_paths = []
        self._render_gallery()

    def _open_output_folder(self):
        output_dir = self.app.config.get("output_path", "")
        if output_dir and os.path.isdir(output_dir):
            subprocess.Popen(["explorer", output_dir])
        else:
            self.app.set_status("출력 폴더를 먼저 설정하세요.", "#FF6B6B")

    # ── 이미지 미리보기 ──────────────────────────────────────────────

    def _show_preview(self, image_path: str):
        """클릭한 이미지를 전체 크기로 보여주는 팝업."""
        if self._preview_win and self._preview_win.winfo_exists():
            self._preview_win.destroy()
        
        win = tk.Toplevel(self.parent)
        win.title(os.path.basename(image_path))
        win.configure(bg="#0A1020")
        win.geometry("900x650")
        self._preview_win = win
        
        try:
            img = Image.open(image_path)
            img.thumbnail((860, 560), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            lbl = tk.Label(win, image=photo, bg="#0A1020")
            lbl.image = photo
            lbl.pack(padx=20, pady=20)
        except Exception as e:
            tk.Label(win, text=f"이미지 로드 실패\n{e}",
                     fg="red", bg="#0A1020").pack(pady=40)
        
        name_lbl = tk.Label(
            win, text=image_path,
            fg="#8888AA", bg="#0A1020", font=("Consolas", 10)
        )
        name_lbl.pack()
        
        tk.Button(
            win, text="닫기",
            bg="#0F3460", fg="white", relief="flat", padx=20, pady=6,
            command=win.destroy
        ).pack(pady=12)

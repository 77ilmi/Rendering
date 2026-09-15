"""layout_tab.py — 프랍 배치 방식 설정 탭."""

import tkinter as tk
import customtkinter as ctk

BG_CARD  = "#0F3460"
BG_INPUT = "#1E2D50"
TEXT_PRI = "#E8E8FF"
TEXT_SEC = "#8888AA"
ACCENT   = "#4A9EFF"
SUCCESS  = "#00D4AA"


class LayoutTab:
    def __init__(self, parent, app):
        self.app = app
        self._build(parent)
        self._load_from_config()

    def _build(self, parent):
        parent.configure(fg_color="#16213E")
        
        scroll = ctk.CTkScrollableFrame(parent, fg_color="#16213E", scrollbar_button_color=BG_CARD)
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        # ── 배치 모드 ───────────────────────────────────────────────
        self._section(scroll, "🗺️ 배치 모드")
        
        mode_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        mode_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        self.mode_var = tk.StringVar(value="grid")
        
        modes = [
            ("grid",   "📐 격자 (Grid)",   "균등한 격자 패턴으로 배치"),
            ("random", "🎲 랜덤 (Random)", "지정 범위 내 랜덤 배치"),
            ("circle", "⭕ 원형 (Circle)", "원형/방사형 배치"),
            ("single", "1️⃣ 개별 (Single)", "각 프랍을 원점에 하나씩 배치"),
        ]
        
        for i, (val, label, desc) in enumerate(modes):
            row = ctk.CTkFrame(mode_frame, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            
            ctk.CTkRadioButton(
                row, text=label, variable=self.mode_var, value=val,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEXT_PRI, fg_color=ACCENT, hover_color="#3A8EEF",
                command=self._on_mode_change
            ).pack(side="left")
            
            ctk.CTkLabel(
                row, text=f"  — {desc}",
                font=ctk.CTkFont(size=11), text_color=TEXT_SEC
            ).pack(side="left")
        
        # ── 격자 설정 ───────────────────────────────────────────────
        self._section(scroll, "📐 격자 설정")
        self.grid_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        self.grid_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        g_inner = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        g_inner.pack(fill="x", padx=14, pady=12)
        
        self.grid_cols_var    = tk.IntVar(value=5)
        self.grid_spacing_var = tk.DoubleVar(value=300.0)
        
        self._labeled_slider(g_inner, "열 수 (Columns)",   self.grid_cols_var,    1, 20,  True,  "{:.0f}열")
        self._labeled_slider(g_inner, "간격 (Spacing, cm)", self.grid_spacing_var, 50, 2000, False, "{:.0f} cm")
        
        # ── 랜덤 설정 ───────────────────────────────────────────────
        self._section(scroll, "🎲 랜덤 설정")
        self.random_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        self.random_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        r_inner = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        r_inner.pack(fill="x", padx=14, pady=12)
        
        self.random_area_var = tk.DoubleVar(value=2000.0)
        self._labeled_slider(r_inner, "배치 범위 (cm)", self.random_area_var, 100, 10000, False, "{:.0f} cm")
        
        # ── 원형 설정 ───────────────────────────────────────────────
        self._section(scroll, "⭕ 원형 설정")
        self.circle_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        self.circle_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        c_inner = ctk.CTkFrame(self.circle_frame, fg_color="transparent")
        c_inner.pack(fill="x", padx=14, pady=12)
        
        self.circle_radius_var = tk.DoubleVar(value=1000.0)
        self._labeled_slider(c_inner, "반지름 (cm)", self.circle_radius_var, 100, 5000, False, "{:.0f} cm")
        
        # ── 공통 설정 ───────────────────────────────────────────────
        self._section(scroll, "⚙️ 공통 설정")
        
        common_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        common_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        co_inner = ctk.CTkFrame(common_frame, fg_color="transparent")
        co_inner.pack(fill="x", padx=14, pady=12)
        
        # 지면 Z
        self.ground_z_var = tk.DoubleVar(value=0.0)
        self._labeled_slider(co_inner, "지면 Z 위치 (cm)", self.ground_z_var, -500, 500, False, "{:.0f} cm")
        
        # 랜덤 회전
        self.random_rot_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            co_inner, text="랜덤 회전 (Z축)",
            variable=self.random_rot_var,
            fg_color=ACCENT, hover_color="#3A8EEF",
            text_color=TEXT_PRI
        ).pack(anchor="w", pady=6)
        
        # 스케일 범위
        scale_row = ctk.CTkFrame(co_inner, fg_color="transparent")
        scale_row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(scale_row, text="스케일 범위:", text_color=TEXT_SEC, width=120).pack(side="left")
        
        self.scale_min_var = tk.DoubleVar(value=1.0)
        self.scale_max_var = tk.DoubleVar(value=1.0)
        
        ctk.CTkLabel(scale_row, text="최솟값", text_color=TEXT_SEC, font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
        ctk.CTkEntry(scale_row, textvariable=self.scale_min_var, width=70,
                     fg_color=BG_INPUT, border_color="#334466", text_color=TEXT_PRI).pack(side="left")
        ctk.CTkLabel(scale_row, text="최댓값", text_color=TEXT_SEC, font=ctk.CTkFont(size=11)).pack(side="left", padx=(12, 4))
        ctk.CTkEntry(scale_row, textvariable=self.scale_max_var, width=70,
                     fg_color=BG_INPUT, border_color="#334466", text_color=TEXT_PRI).pack(side="left")
        
        self._on_mode_change()

    def _section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT
        ).pack(anchor="w", padx=8, pady=(16, 4))

    def _labeled_slider(self, parent, label, var, from_, to, integer, fmt):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(row, text=label, text_color=TEXT_SEC, width=180, anchor="w").pack(side="left")
        
        val_label = ctk.CTkLabel(row, text=fmt.format(var.get()),
                                  text_color=ACCENT, width=80)
        val_label.pack(side="right")
        
        def _on_slide(v):
            if integer:
                var.set(int(float(v)))
            else:
                var.set(float(v))
            val_label.configure(text=fmt.format(var.get()))
        
        ctk.CTkSlider(
            row, from_=from_, to=to, variable=var,
            command=_on_slide,
            button_color=ACCENT, button_hover_color="#3A8EEF",
            progress_color=ACCENT
        ).pack(side="left", fill="x", expand=True, padx=8)

    def _on_mode_change(self):
        mode = self.mode_var.get()
        # 각 모드별 설정 프레임 표시/숨김
        # (간단하게 모두 표시 유지하고 관련 설명만 강조)
        pass

    def _load_from_config(self):
        cfg = self.app.config.get("layout", {})
        self.mode_var.set(cfg.get("mode", "grid"))
        self.grid_cols_var.set(int(cfg.get("grid_columns", 5)))
        self.grid_spacing_var.set(float(cfg.get("grid_spacing", 300.0)))
        self.random_area_var.set(float(cfg.get("random_area", 2000.0)))
        self.circle_radius_var.set(float(cfg.get("circle_radius", 1000.0)))
        self.ground_z_var.set(float(cfg.get("ground_z", 0.0)))
        self.random_rot_var.set(bool(cfg.get("random_rotation", True)))
        self.scale_min_var.set(float(cfg.get("random_scale_min", 1.0)))
        self.scale_max_var.set(float(cfg.get("random_scale_max", 1.0)))

    def apply_to_config(self, config: dict):
        config.setdefault("layout", {}).update({
            "mode":              self.mode_var.get(),
            "grid_columns":      self.grid_cols_var.get(),
            "grid_spacing":      self.grid_spacing_var.get(),
            "random_area":       self.random_area_var.get(),
            "circle_radius":     self.circle_radius_var.get(),
            "ground_z":          self.ground_z_var.get(),
            "random_rotation":   self.random_rot_var.get(),
            "random_scale_min":  self.scale_min_var.get(),
            "random_scale_max":  self.scale_max_var.get(),
        })

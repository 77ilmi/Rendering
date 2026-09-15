"""render_tab.py — 렌더링 방식, 해상도, 카메라 설정 탭."""

import tkinter as tk
import customtkinter as ctk

BG_CARD  = "#0F3460"
BG_INPUT = "#1E2D50"
TEXT_PRI = "#E8E8FF"
TEXT_SEC = "#8888AA"
ACCENT   = "#4A9EFF"
SUCCESS  = "#00D4AA"


class RenderTab:
    def __init__(self, parent, app):
        self.app = app
        self._build(parent)
        self._load_from_config()

    def _build(self, parent):
        parent.configure(fg_color="#16213E")
        
        scroll = ctk.CTkScrollableFrame(parent, fg_color="#16213E", scrollbar_button_color=BG_CARD)
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        # ── 렌더링 방식 ──────────────────────────────────────────────
        self._section(scroll, "🎬 렌더링 방식")
        
        method_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        method_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        self.method_var = tk.StringVar(value="hires")
        
        method_row = ctk.CTkFrame(method_frame, fg_color="transparent")
        method_row.pack(fill="x", padx=14, pady=12)
        
        for val, label in [
            ("hires", "⚡ High Resolution Screenshot  (빠름)"),
            ("mrq",   "🎞️ Movie Render Queue  (고품질)"),
        ]:
            ctk.CTkRadioButton(
                method_row, text=label, variable=self.method_var, value=val,
                fg_color=ACCENT, hover_color="#3A8EEF",
                text_color=TEXT_PRI, font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=4)
        
        # ── 배치 옵션 ────────────────────────────────────────────────
        self._section(scroll, "📋 배치 옵션")
        
        batch_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        batch_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        b_inner = ctk.CTkFrame(batch_frame, fg_color="transparent")
        b_inner.pack(fill="x", padx=14, pady=12)
        
        self.per_prop_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            b_inner, text="프랍 개별 렌더링  (각 프랍마다 결과 이미지 1장)",
            variable=self.per_prop_var,
            fg_color=ACCENT, hover_color="#3A8EEF",
            text_color=TEXT_PRI, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=4)
        
        self.group_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            b_inner, text="그룹 렌더링  (모든 프랍을 씬에 배치 후 한 장)",
            variable=self.group_var,
            fg_color=ACCENT, hover_color="#3A8EEF",
            text_color=TEXT_PRI, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=4)
        
        # ── 해상도 ───────────────────────────────────────────────────
        self._section(scroll, "📐 해상도")
        
        res_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        res_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        res_inner = ctk.CTkFrame(res_frame, fg_color="transparent")
        res_inner.pack(fill="x", padx=14, pady=12)
        
        # 프리셋
        presets = [
            ("1280 × 720 (HD)",     1280, 720),
            ("1920 × 1080 (FHD)",   1920, 1080),
            ("2560 × 1440 (QHD)",   2560, 1440),
            ("3840 × 2160 (4K UHD)", 3840, 2160),
        ]
        
        self.width_var  = tk.IntVar(value=1920)
        self.height_var = tk.IntVar(value=1080)
        
        preset_row = ctk.CTkFrame(res_inner, fg_color="transparent")
        preset_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(preset_row, text="프리셋:", text_color=TEXT_SEC, width=70).pack(side="left")
        
        for label, w, h in presets:
            ctk.CTkButton(
                preset_row, text=label, width=140,
                fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI,
                font=ctk.CTkFont(size=11),
                command=lambda _w=w, _h=h: (self.width_var.set(_w), self.height_var.set(_h))
            ).pack(side="left", padx=4)
        
        # 커스텀 입력
        custom_row = ctk.CTkFrame(res_inner, fg_color="transparent")
        custom_row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(custom_row, text="너비:", text_color=TEXT_SEC, width=70).pack(side="left")
        ctk.CTkEntry(custom_row, textvariable=self.width_var, width=80,
                     fg_color=BG_INPUT, border_color="#334466", text_color=TEXT_PRI).pack(side="left")
        ctk.CTkLabel(custom_row, text="높이:", text_color=TEXT_SEC, width=50).pack(side="left", padx=(12, 0))
        ctk.CTkEntry(custom_row, textvariable=self.height_var, width=80,
                     fg_color=BG_INPUT, border_color="#334466", text_color=TEXT_PRI).pack(side="left")
        
        # HiRes 배율
        hires_row = ctk.CTkFrame(res_inner, fg_color="transparent")
        hires_row.pack(fill="x", pady=4)
        ctk.CTkLabel(hires_row, text="HiRes 배율:", text_color=TEXT_SEC, width=90).pack(side="left")
        self.hires_mult_var = tk.IntVar(value=2)
        ctk.CTkOptionMenu(
            hires_row, values=["1", "2", "3", "4"],
            variable=tk.StringVar(value="2"),
            fg_color=BG_INPUT, button_color=ACCENT, text_color=TEXT_PRI,
            command=lambda v: self.hires_mult_var.set(int(v)),
            width=80
        ).pack(side="left", padx=4)
        ctk.CTkLabel(hires_row, text="× (HiRes Screenshot 방식에만 적용)",
                     text_color=TEXT_SEC, font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
        
        # ── 카메라 ───────────────────────────────────────────────────
        self._section(scroll, "📷 카메라")
        
        cam_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        cam_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        cam_inner = ctk.CTkFrame(cam_frame, fg_color="transparent")
        cam_inner.pack(fill="x", padx=14, pady=12)
        
        # 프리셋
        cam_preset_row = ctk.CTkFrame(cam_inner, fg_color="transparent")
        cam_preset_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(cam_preset_row, text="프리셋:", text_color=TEXT_SEC, width=70).pack(side="left")
        
        self.cam_preset_var = tk.StringVar(value="isometric")
        cam_presets = [
            ("정면", "front"), ("측면", "side"),
            ("상단", "top"),  ("아이소", "isometric"), ("원근", "perspective"),
        ]
        for label, val in cam_presets:
            ctk.CTkButton(
                cam_preset_row, text=label, width=65,
                fg_color=BG_INPUT, hover_color=ACCENT, text_color=TEXT_PRI,
                font=ctk.CTkFont(size=11),
                command=lambda v=val: self.cam_preset_var.set(v)
            ).pack(side="left", padx=3)
        
        # 세부 조절
        self.fov_var      = tk.DoubleVar(value=60.0)
        self.dist_var     = tk.DoubleVar(value=1.5)
        self.height_var2  = tk.DoubleVar(value=200.0)
        self.pitch_var    = tk.DoubleVar(value=-45.0)
        self.yaw_var      = tk.DoubleVar(value=45.0)
        
        sliders = [
            ("FOV (°)",       self.fov_var,     10,   120,  False, "{:.0f}°"),
            ("거리 배율",     self.dist_var,    0.5,  5.0,  False, "{:.1f}×"),
            ("높이 오프셋(cm)", self.height_var2, -1000, 2000, False, "{:.0f}cm"),
            ("Pitch (°)",     self.pitch_var,   -89,  0,    False, "{:.0f}°"),
            ("Yaw (°)",       self.yaw_var,     0,    360,  False, "{:.0f}°"),
        ]
        for label, var, from_, to, integer, fmt in sliders:
            self._labeled_slider(cam_inner, label, var, from_, to, integer, fmt)
        
        # ── 라이팅 ───────────────────────────────────────────────────
        self._section(scroll, "💡 라이팅")
        
        light_frame = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10)
        light_frame.pack(fill="x", padx=8, pady=(0, 12))
        
        l_inner = ctk.CTkFrame(light_frame, fg_color="transparent")
        l_inner.pack(fill="x", padx=14, pady=12)
        
        ctk.CTkLabel(l_inner, text="라이팅 설정은 레벨의 기존 라이팅을 사용합니다.\n(DirectionalLight, SkyLight 설정을 레벨에서 직접 조절하세요)",
                     text_color=TEXT_SEC, font=ctk.CTkFont(size=11), justify="left").pack(anchor="w")

    def _section(self, parent, title):
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=8, pady=(16, 4))

    def _labeled_slider(self, parent, label, var, from_, to, integer, fmt):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        
        ctk.CTkLabel(row, text=label, text_color=TEXT_SEC, width=130, anchor="w").pack(side="left")
        
        val_label = ctk.CTkLabel(row, text=fmt.format(var.get()), text_color=ACCENT, width=70)
        val_label.pack(side="right")
        
        def _on_slide(v):
            val = int(float(v)) if integer else float(v)
            var.set(val)
            val_label.configure(text=fmt.format(val))
        
        ctk.CTkSlider(
            row, from_=from_, to=to, variable=var,
            command=_on_slide,
            button_color=ACCENT, button_hover_color="#3A8EEF", progress_color=ACCENT
        ).pack(side="left", fill="x", expand=True, padx=8)

    def _load_from_config(self):
        rc = self.app.config.get("render", {})
        self.method_var.set(rc.get("method", "hires"))
        self.per_prop_var.set(bool(rc.get("per_prop", True)))
        self.group_var.set(bool(rc.get("group", False)))
        self.width_var.set(int(rc.get("resolution_width", 1920)))
        self.height_var.set(int(rc.get("resolution_height", 1080)))
        self.hires_mult_var.set(int(rc.get("hires_multiplier", 2)))
        
        cc = self.app.config.get("camera", {})
        self.cam_preset_var.set(cc.get("preset", "isometric"))
        self.fov_var.set(float(cc.get("fov", 60.0)))
        self.dist_var.set(float(cc.get("distance_multiplier", 1.5)))
        self.height_var2.set(float(cc.get("height_offset", 200.0)))
        self.pitch_var.set(float(cc.get("angle_pitch", -45.0)))
        self.yaw_var.set(float(cc.get("angle_yaw", 45.0)))

    def apply_to_config(self, config: dict):
        config.setdefault("render", {}).update({
            "method":            self.method_var.get(),
            "per_prop":          self.per_prop_var.get(),
            "group":             self.group_var.get(),
            "resolution_width":  self.width_var.get(),
            "resolution_height": self.height_var.get(),
            "hires_multiplier":  self.hires_mult_var.get(),
        })
        config.setdefault("camera", {}).update({
            "preset":              self.cam_preset_var.get(),
            "fov":                 self.fov_var.get(),
            "distance_multiplier": self.dist_var.get(),
            "height_offset":       self.height_var2.get(),
            "angle_pitch":         self.pitch_var.get(),
            "angle_yaw":           self.yaw_var.get(),
        })

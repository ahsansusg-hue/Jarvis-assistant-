import math
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from jarvis_config import JarvisConfig
from jarvis_modes import JarvisModeEngine
from jarvis_ears import JarvisEars
from jarvis_speaker import JarvisSpeaker
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0, 229, 255)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(rgb[0]))),
        max(0, min(255, int(rgb[1]))),
        max(0, min(255, int(rgb[2]))),
    )


def blend_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


class HudPillButton(tk.Canvas):
    """Custom rounded/chamfered dark HUD button without classic Windows 98 borders."""

    def __init__(
        self, parent, text, command, width=104, height=28,
        bg="#0A111F", fg="#94A3B8", border="#1B2A44", active_bg=None, active_fg="#04070D",
        font=("Consolas", 8, "bold")
    ):
        super().__init__(
            parent, width=width, height=height,
            bg=parent["bg"], highlightthickness=0, bd=0, cursor="hand2"
        )
        self.text = text
        self.command = command
        self.pill_w = width
        self.pill_h = height
        self.base_bg = bg
        self.base_fg = fg
        self.base_border = border
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.font = font
        self.is_active = False
        self.hovered = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.redraw()

    def set_style(self, fg=None, border=None, active=None, text=None):
        if fg is not None:
            self.base_fg = fg
        if border is not None:
            self.base_border = border
        if active is not None:
            self.is_active = active
        if text is not None:
            self.text = text
        self.redraw()

    def _on_enter(self, _):
        self.hovered = True
        self.redraw()

    def _on_leave(self, _):
        self.hovered = False
        self.redraw()

    def _on_click(self, _):
        if callable(self.command):
            self.command()

    def _rounded_poly(self, x1, y1, x2, y2, r=7):
        return [
            x1 + r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1
        ]

    def redraw(self):
        self.delete("all")
        w, h = self.pill_w, self.pill_h
        if self.is_active and self.active_bg:
            fill = self.active_bg
            outline = self.active_bg
            txt_col = self.active_fg
        else:
            fill = blend_color(self.base_bg, self.base_border, 0.25) if self.hovered else self.base_bg
            outline = self.base_fg if self.hovered else self.base_border
            txt_col = "#FFFFFF" if self.hovered else self.base_fg

        pts = self._rounded_poly(1, 1, w - 1, h - 1, r=7)
        self.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=1)
        self.create_text(w / 2, h / 2, text=self.text, fill=txt_col, font=self.font)


class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S // HUD & AUTONOMOUS CORE")
        self.root.geometry("1240x790")
        self.root.minsize(1040, 680)
        self.root.configure(bg="#04070D")

        self.config = JarvisConfig()
        self._ensure_extra_defaults()

        self.speaker = JarvisSpeaker()
        self.listener = JarvisEars()
        self.task_engine = TaskEngine()
        self.system = JarvisSystem()
        self.brain = JarvisBrain(
            task_engine=self.task_engine,
            model=self.config.settings.get("ollama_model", "qwen2.5:3b")
        )
        self.modes = JarvisModeEngine(self.config, self.system, self.brain)

        active = self.config.settings.get("active_mode", "Normal")
        self.current_color = self.config.settings["modes"][active]["color"]
        self.target_color = self.current_color
        self.is_speaking = False
        self.is_listening = False
        self.angle = 0.0
        self.pulse_phase = 0.0
        self.arc_build_progress = 0.0
        self.recent_menu_visible = False

        self.sphere_points = self._generate_sphere_points(
            self.config.settings.get("dev_dot_count", 84)
        )

        self._configure_ttk_dark()
        self._build_layout()
        self._bind_shortcuts()
        self._animate()
        self._welcome_sequence()

    def _ensure_extra_defaults(self):
        s = self.config.settings
        s.setdefault("ollama_model", "qwen2.5:3b")
        s.setdefault("show_reticle", True)
        s.setdefault("show_brackets", True)
        s.setdefault("auto_listen_after_reply", False)
        changed = False
        if s.get("modes", {}).get("Gaming", {}).get("color") == "#FF2A6D":
            s["modes"]["Gaming"]["color"] = "#FF7A00"
            changed = True
        if changed:
            self.config.save_settings()

    def _configure_ttk_dark(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background="#070C17", borderwidth=0)
        style.configure(
            "TNotebook.Tab", background="#0C1424", foreground="#94A3B8",
            padding=[12, 6], font=("Consolas", 9, "bold"), borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#14223B")],
            foreground=[("selected", "#00E5FF")]
        )
        style.configure(
            "TCombobox", fieldbackground="#0D1627", background="#14223B",
            foreground="#F1F5F9", arrowcolor="#00E5FF", bordercolor="#1E2F4D"
        )

    def _generate_sphere_points(self, count):
        pts = []
        phi = math.pi * (3.0 - math.sqrt(5.0))
        for i in range(count):
            y = 1 - (i / float(max(1, count - 1))) * 2
            radius = math.sqrt(max(0.0, 1 - y * y))
            theta = phi * i
            pts.append((math.cos(theta) * radius, y, math.sin(theta) * radius))
        return pts

    def _build_layout(self):
        # Top HUD Bar
        self.top_bar = tk.Frame(self.root, bg="#070C16", height=52, padx=14)
        self.top_bar.pack(fill=tk.X, side=tk.TOP)

        self.title_lbl = tk.Label(
            self.top_bar, text="◈ J.A.R.V.I.S // HUD CORE",
            fg=self.current_color, bg="#070C16", font=("Consolas", 12, "bold")
        )
        self.title_lbl.pack(side=tk.LEFT, pady=12)

        mode_frame = tk.Frame(self.top_bar, bg="#070C16")
        mode_frame.pack(side=tk.LEFT, padx=18)
        self.mode_pills = {}
        for m_name in ["Normal", "Gaming", "Productivity", "Batla"]:
            pill = HudPillButton(
                mode_frame, text=m_name.upper(),
                command=lambda m=m_name: self.switch_mode(m),
                width=102, height=28, bg="#0C1424", fg="#94A3B8", border="#1B2B46"
            )
            pill.pack(side=tk.LEFT, padx=3, pady=10)
            self.mode_pills[m_name] = pill

        self.settings_pill = HudPillButton(
            self.top_bar, text="⚙ SETTINGS", command=self.open_settings,
            width=98, height=28, bg="#0C1424", fg="#E2E8F0", border="#223554"
        )
        self.settings_pill.pack(side=tk.RIGHT, padx=3, pady=10)

        self.idea_pill = HudPillButton(
            self.top_bar, text="💡 IDEOLOGY", command=self.trigger_ideology,
            width=98, height=28, bg="#0C1424", fg="#FBBF24", border="#3B3118"
        )
        self.idea_pill.pack(side=tk.RIGHT, padx=3, pady=10)

        self.chat_speak_pill = HudPillButton(
            self.top_bar,
            text=f"VOICE: {self.config.settings.get('chat_speak_mode', 'Speak').upper()}",
            command=self.toggle_chat_speak,
            width=112, height=28, bg="#0C1424", fg="#38BDF8", border="#19344D"
        )
        self.chat_speak_pill.pack(side=tk.RIGHT, padx=3, pady=10)

        # Hairline divider under top bar
        tk.Frame(self.root, bg="#132036", height=1).pack(fill=tk.X)

        # Main Split Body
        body = tk.Frame(self.root, bg="#04070D")
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Left Core Visualizer Panel
        left_panel = tk.Frame(body, bg="#060B14", highlightbackground="#122036", highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.canvas = tk.Canvas(left_panel, bg="#04070D", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Double-Button-1>", self.toggle_recent_tasks_overlay)

        self.hint_lbl = tk.Label(
            left_panel,
            text="Voice switches modes ('Gaming mode')  |  Double-click core: Recent Tasks  |  Right-click: Mic",
            fg="#5B6E8A", bg="#060B14", font=("Consolas", 8)
        )
        self.hint_lbl.pack(side=tk.BOTTOM, pady=6)

        # Right Console & Telemetry Panel
        right_panel = tk.Frame(body, bg="#060B14", width=445, highlightbackground="#122036", highlightthickness=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        right_panel.pack_propagate(False)

        tel_bar = tk.Frame(right_panel, bg="#09101E", pady=7, padx=10)
        tel_bar.pack(fill=tk.X)
        self.status_lbl = tk.Label(
            tel_bar, text="ACTIVE MODE: NORMAL", fg=self.current_color,
            bg="#09101E", font=("Consolas", 9, "bold")
        )
        self.status_lbl.pack(side=tk.LEFT)

        self.diag_pill = HudPillButton(
            tel_bar, text="TELEMETRY", command=self.show_telemetry,
            width=86, height=22, bg="#0E192E", fg="#94A3B8", border="#1E304F",
            font=("Consolas", 8, "bold")
        )
        self.diag_pill.pack(side=tk.RIGHT)

        tk.Frame(right_panel, bg="#122036", height=1).pack(fill=tk.X)

        self.chat_box = tk.Text(
            right_panel, bg="#050911", fg="#E2E8F0", font=("Consolas", 10),
            wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=12, pady=10, state=tk.DISABLED
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        input_wrap = tk.Frame(right_panel, bg="#09101E", padx=8, pady=8)
        input_wrap.pack(fill=tk.X, side=tk.BOTTOM)

        entry_border = tk.Frame(input_wrap, bg="#1B2B46", padx=1, pady=1)
        entry_border.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.entry = tk.Entry(
            entry_border, bg="#0A1220", fg="#F8FAFC", insertbackground=self.current_color,
            relief=tk.FLAT, bd=0, font=("Consolas", 10)
        )
        self.entry.pack(fill=tk.BOTH, expand=True, ipady=6, padx=6)
        self.entry.bind("<Return>", lambda e: self.handle_text_submit())

        self.send_pill = HudPillButton(
            input_wrap, text="SEND", command=self.handle_text_submit,
            width=64, height=28, bg="#0B233D", fg="#38BDF8", border="#1B4975"
        )
        self.send_pill.pack(side=tk.LEFT, padx=(0, 4))

        self.mic_pill = HudPillButton(
            input_wrap, text="MIC", command=self.trigger_voice_listen,
            width=54, height=28, bg="#0D182C", fg="#00E5FF", border="#1B3454"
        )
        self.mic_pill.pack(side=tk.RIGHT)

        self._refresh_mode_pills()

    def _bind_shortcuts(self):
        self.canvas.bind("<Button-3>", lambda e: self.trigger_voice_listen())

    def log(self, sender, msg):
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"[{sender}] {msg}\n\n")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state=tk.DISABLED)

    def speak_async(self, text):
        if self.config.settings.get("chat_speak_mode", "Speak") != "Speak":
            return

        def _run():
            com_init = False
            try:
                import pythoncom
                pythoncom.CoInitialize()
                com_init = True
            except Exception:
                pass

            self.is_speaking = True
            try:
                self.speaker.speak(str(text))
            finally:
                self.is_speaking = False
                if com_init:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass
                if self.config.settings.get("auto_listen_after_reply", False):
                    self.root.after(150, self.trigger_voice_listen)

        threading.Thread(target=_run, daemon=True).start()

    def _welcome_sequence(self):
        intro = self.config.settings.get("intro_tweak", {})
        if intro.get("enabled", True):
            last_work = self.config.memory.get("last_work", "Day 10 HUD Core")
            msg = intro.get("welcome_template", "All systems online, Boss.").format(last_work=last_work)
        else:
            msg = "All systems online and running locally, Boss."
        self.log("JARVIS", msg)
        self.speak_async(msg)

    def switch_mode(self, mode_name):
        res = self.modes.activate_mode(mode_name)
        self.target_color = self.config.settings["modes"][mode_name]["color"]
        self._refresh_mode_pills()
        self.log("SYSTEM", res)
        self.speak_async(f"{mode_name} mode activated.")

    def _refresh_mode_pills(self):
        active = self.config.settings.get("active_mode", "Normal")
        color = self.config.settings["modes"].get(active, {}).get("color", "#00E5FF")
        self.status_lbl.configure(text=f"ACTIVE MODE: {active.upper()}", fg=color)
        for m, pill in self.mode_pills.items():
            if m == active:
                pill.set_style(fg="#04070D", border=color, active=True)
                pill.active_bg = color
                pill.active_fg = "#04070D"
                pill.redraw()
            else:
                pill.set_style(fg="#94A3B8", border="#1B2B46", active=False)

    def toggle_chat_speak(self):
        curr = self.config.settings.get("chat_speak_mode", "Speak")
        nxt = "Chat" if curr == "Speak" else "Speak"
        self.config.settings["chat_speak_mode"] = nxt
        self.config.save_settings()
        self.chat_speak_pill.set_style(text=f"VOICE: {nxt.upper()}")
        self.log("SYSTEM", f"Interaction switched to {nxt} Mode.")

    def toggle_recent_tasks_overlay(self, event=None):
        self.recent_menu_visible = not self.recent_menu_visible
        self.modes.play_fx("macro_run")

    def show_telemetry(self):
        def _worker():
            status = self.system.get_system_status()
            self.root.after(0, lambda: self.log("TELEMETRY", status))
            self.speak_async(status)

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_ideology(self):
        self.log("IDEOLOGY", "Analyzing recent workspace activity for next-step ideas...")

        def _worker():
            idea = self.modes.generate_ideology_idea()
            self.root.after(0, lambda: self.log("JARVIS IDEA", idea))
            self.speak_async(idea)

        threading.Thread(target=_worker, daemon=True).start()

    def _match_voice_mode(self, text):
        lower = text.lower().strip()
        for m in ["normal", "gaming", "productivity", "batla"]:
            if f"{m} mode" in lower or lower == m:
                return m.capitalize()
        return None

    def trigger_voice_listen(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.mic_pill.set_style(fg="#FCA5A5", border="#EF4444")
        self.log("EARS", "Listening...")

        def _worker():
            try:
                text = self.listener.listen_command()
            except Exception as e:
                text = None
                self.root.after(0, lambda: self.log("ERROR", f"Mic error: {e}"))
            finally:
                self.is_listening = False
                self.root.after(0, lambda: self.mic_pill.set_style(fg="#00E5FF", border="#1B3454"))

            if text:
                spoken = str(text).strip()
                matched_mode = self._match_voice_mode(spoken)
                if matched_mode:
                    self.root.after(0, lambda: self.log("YOU (VOICE)", spoken))
                    self.root.after(0, lambda m=matched_mode: self.switch_mode(m))
                else:
                    self.root.after(0, lambda: self._process_user_input(spoken, from_voice=True))

        threading.Thread(target=_worker, daemon=True).start()

    def handle_text_submit(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._process_user_input(text, from_voice=False)

    def _process_user_input(self, text, from_voice=False):
        tag = "YOU (VOICE)" if from_voice else "YOU"
        self.log(tag, text)
        lower = text.lower().strip()

        if lower.startswith("open ") or lower.startswith("launch "):
            app = lower.replace("open ", "", 1).replace("launch ", "", 1).strip()
            res = self.modes.launch_target(app)
            self.log("JARVIS", res)
            self.speak_async(res)
            return

        if "system status" in lower or "telemetry" in lower:
            self.show_telemetry()
            return

        def _think_worker():
            reply = self.modes.process_query(text)
            self.root.after(0, lambda: self.log("JARVIS", reply))
            self.speak_async(reply)

        threading.Thread(target=_think_worker, daemon=True).start()

    # --- ANIMATION LOOP ---
    def _animate(self):
        self.current_color = blend_color(self.current_color, self.target_color, 0.12)
        self.title_lbl.configure(fg=self.current_color)
        self.entry.configure(insertbackground=self.current_color)

        dev_unlocked = self.config.settings.get("developer_mode_unlocked", False)
        core_style = self.config.settings.get("dev_core_style", "arc_reactor")

        if dev_unlocked and core_style == "arc_reactor":
            self.arc_build_progress = min(1.0, self.arc_build_progress + 0.022)
        else:
            self.arc_build_progress = max(0.0, self.arc_build_progress - 0.04)

        self.angle += 0.022 if not self.is_speaking else 0.052
        self.pulse_phase += 0.28 if self.is_speaking else 0.08

        self.canvas.delete("all")
        w = max(200, self.canvas.winfo_width())
        h = max(200, self.canvas.winfo_height())
        cx, cy = w / 2, h / 2

        pulse_amp = self.config.settings.get("dev_pulse_intensity", 1.35) if self.is_speaking else 1.05
        pulse = 1.0 + (pulse_amp - 1.0) * (0.5 + 0.5 * math.sin(self.pulse_phase))
        base_r = min(w, h) * 0.23 * pulse

        self._draw_hud_overlay(cx, cy, min(w, h) * 0.34, w, h)

        if self.arc_build_progress > 0.05:
            self._draw_arc_reactor(cx, cy, base_r * 1.08, self.arc_build_progress)
        else:
            self._draw_constellation_sphere(cx, cy, base_r)

        if self.recent_menu_visible:
            self._draw_recent_tasks_network(cx, cy, base_r)

        self.root.after(30, self._animate)

    def _draw_hud_overlay(self, cx, cy, outer_r, w, h):
        dim_ring = blend_color("#04070D", self.current_color, 0.26)
        bright_ring = blend_color("#04070D", self.current_color, 0.62)

        if self.config.settings.get("show_reticle", True):
            self.canvas.create_oval(
                cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                outline=dim_ring, width=1
            )
            for seg in range(4):
                start_deg = math.degrees(self.angle * 0.7) + seg * 90
                self.canvas.create_arc(
                    cx - outer_r * 0.95, cy - outer_r * 0.95,
                    cx + outer_r * 0.95, cy + outer_r * 0.95,
                    start=start_deg, extent=30, style=tk.ARC,
                    outline=bright_ring, width=2
                )

        if self.config.settings.get("show_brackets", True):
            b = 16
            pad = 20
            for x0, y0, dx, dy in [
                (pad, pad, b, b),
                (w - pad, pad, -b, b),
                (pad, h - pad, b, -b),
                (w - pad, h - pad, -b, -b),
            ]:
                self.canvas.create_line(x0, y0, x0 + dx, y0, fill=dim_ring, width=2)
                self.canvas.create_line(x0, y0, x0, y0 + dy, fill=dim_ring, width=2)

    def _draw_constellation_sphere(self, cx, cy, r):
        projected = []
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        cos_b, sin_b = math.cos(self.angle * 0.5), math.sin(self.angle * 0.5)

        for x, y, z in self.sphere_points:
            xz = x * cos_a - z * sin_a
            zz = x * sin_a + z * cos_a
            yz = y * cos_b - zz * sin_b
            zz2 = y * sin_b + zz * cos_b

            scale = 2.4 / (2.4 - zz2)
            sx = cx + xz * r * scale
            sy = cy + yz * r * scale
            projected.append((sx, sy, zz2))

        line_col = blend_color("#04070D", self.current_color, 0.36)
        n = len(projected)
        max_dist_sq = (r * 0.50) ** 2
        for i in range(n):
            x1, y1, z1 = projected[i]
            if z1 < -0.35:
                continue
            for j in range(i + 1, n):
                x2, y2, z2 = projected[j]
                if z2 < -0.35:
                    continue
                if (x1 - x2) ** 2 + (y1 - y2) ** 2 < max_dist_sq:
                    self.canvas.create_line(x1, y1, x2, y2, fill=line_col, width=1)

        for sx, sy, z in projected:
            depth = (z + 1.0) / 2.0
            dot_col = blend_color("#0A1220", self.current_color, 0.25 + 0.75 * depth)
            rad = 1.6 + 2.4 * depth
            self.canvas.create_oval(sx - rad, sy - rad, sx + rad, sy + rad, fill=dot_col, outline="")

    def _draw_arc_reactor(self, cx, cy, r, p):
        """Multi-ring Arc Reactor with copper coil housings, inner ring, and glowing core."""
        housing_dark = "#1C2433"
        copper = "#C87D4B"
        core_glow = blend_color(self.current_color, "#FFFFFF", 0.65)

        # 1. Outer heavy containment bezel (0.0 - 0.28)
        if p > 0.04:
            s1 = min(1.0, p / 0.28)
            self.canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90, extent=359.9 * s1, style=tk.ARC,
                outline="#475569", width=6
            )
            self.canvas.create_arc(
                cx - r * 0.93, cy - r * 0.93, cx + r * 0.93, cy + r * 0.93,
                start=90, extent=359.9 * s1, style=tk.ARC,
                outline=self.current_color, width=2
            )

        # 2. Copper electromagnetic coil blocks around ring (0.25 - 0.62)
        if p > 0.25:
            count = int(((p - 0.25) / 0.37) * 10)
            for i in range(min(10, count)):
                ang = math.radians(i * 36) + self.angle * 0.35
                mx = cx + math.cos(ang) * (r * 0.78)
                my = cy + math.sin(ang) * (r * 0.78)
                bw, bh = r * 0.14, r * 0.08
                self.canvas.create_rectangle(
                    mx - bw / 2, my - bh / 2, mx + bw / 2, my + bh / 2,
                    fill=housing_dark, outline=copper, width=2
                )
                # Inner copper winding line
                ix1 = cx + math.cos(ang) * (r * 0.62)
                iy1 = cy + math.sin(ang) * (r * 0.62)
                ix2 = cx + math.cos(ang) * (r * 0.72)
                iy2 = cy + math.sin(ang) * (r * 0.72)
                self.canvas.create_line(ix1, iy1, ix2, iy2, fill=copper, width=3)

        # 3. Inner ring & radial stabilizer struts (0.55 - 0.82)
        if p > 0.55:
            s3 = min(1.0, (p - 0.55) / 0.27)
            ir_outer = r * 0.52 * s3
            self.canvas.create_oval(
                cx - ir_outer, cy - ir_outer, cx + ir_outer, cy + ir_outer,
                outline="#64748B", width=3, fill="#080E1A"
            )
            for k in range(5):
                a_strut = math.radians(k * 72 + 18) - self.angle * 0.5
                sx1 = cx + math.cos(a_strut) * (ir_outer * 0.45)
                sy1 = cy + math.sin(a_strut) * (ir_outer * 0.45)
                sx2 = cx + math.cos(a_strut) * ir_outer
                sy2 = cy + math.sin(a_strut) * ir_outer
                self.canvas.create_line(sx1, sy1, sx2, sy2, fill=self.current_color, width=2)

        # 4. Central energy core (0.78 - 1.0)
        if p > 0.78:
            s4 = min(1.0, (p - 0.78) / 0.22)
            cr = r * 0.24 * s4
            self.canvas.create_oval(
                cx - cr * 1.25, cy - cr * 1.25, cx + cr * 1.25, cy + cr * 1.25,
                outline=self.current_color, width=2
            )
            self.canvas.create_oval(
                cx - cr, cy - cr, cx + cr, cy + cr,
                fill=blend_color(self.current_color, core_glow, 0.55), outline="#FFFFFF", width=2
            )
            self.canvas.create_text(
                cx, cy + r + 22, text="ARC REACTOR // DEVELOPER OVERRIDE",
                fill=self.current_color, font=("Consolas", 8, "bold")
            )

    def _draw_recent_tasks_network(self, cx, cy, r):
        recent = self.config.memory.get("recent_activities", [])[:3]
        if not recent:
            recent = ["No recent tasks logged yet."]

        offsets = [
            (-r * 1.4, -r * 0.8),
            (r * 1.4, -r * 0.7),
            (-r * 1.2, r * 0.9),
        ]
        for idx, item in enumerate(recent):
            ox, oy = offsets[idx % len(offsets)]
            bx, by = cx + ox, cy + oy
            self.canvas.create_line(cx, cy, bx, by, fill=self.current_color, width=2, dash=(4, 2))
            self.canvas.create_oval(bx - 4, by - 4, bx + 4, by + 4, fill=self.current_color, outline="")

            card_w, card_h = 198, 42
            self.canvas.create_rectangle(
                bx - card_w / 2, by - card_h / 2, bx + card_w / 2, by + card_h / 2,
                fill="#0A1220", outline=self.current_color, width=1
            )
            short_txt = item if len(item) <= 28 else item[:25] + "..."
            self.canvas.create_text(bx, by, text=short_txt, fill="#F1F5F9", font=("Consolas", 8))

    # --- SETTINGS & CUSTOMIZATION WINDOW ---
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("J.A.R.V.I.S // SETTINGS & VIBE CUSTOMIZER")
        win.geometry("650x680")
        win.configure(bg="#070C17")

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # TAB 1: Modes & Game .exe Picker
        tab_modes = tk.Frame(nb, bg="#070C17", padx=14, pady=14)
        nb.add(tab_modes, text="Modes & Game .EXE")

        mode_var = tk.StringVar(value=self.config.settings.get("active_mode", "Normal"))
        tk.Label(tab_modes, text="Select Mode to Configure:", fg="#E2E8F0", bg="#070C17", font=("Consolas", 9, "bold")).pack(anchor="w")
        mode_menu = ttk.Combobox(tab_modes, textvariable=mode_var, values=["Normal", "Gaming", "Productivity", "Batla"], state="readonly")
        mode_menu.pack(fill=tk.X, pady=(4, 10))

        color_var = tk.StringVar()
        apps_var = tk.StringVar()
        game_var = tk.StringVar()
        batla_var = tk.StringVar(value=self.config.settings.get("batla_quote", "JA CHAT SEY KOUD JA"))
        unload_vram_var = tk.BooleanVar(value=True)

        def load_mode_fields(*_):
            m = mode_var.get()
            cfg = self.config.settings["modes"][m]
            color_var.set(cfg.get("color", "#00E5FF"))
            apps_var.set(", ".join(cfg.get("apps", [])))
            game_var.set(cfg.get("current_game", ""))
            unload_vram_var.set(cfg.get("unload_vram", True))

        mode_menu.bind("<<ComboboxSelected>>", load_mode_fields)
        load_mode_fields()

        tk.Label(tab_modes, text="Mode Accent Color (Hex):", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        tk.Entry(tab_modes, textvariable=color_var, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=(2, 8))

        # Gaming Executable Row + BROWSE button
        tk.Label(tab_modes, text="Gaming Mode Executable (.exe) or Game Name:", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        game_row = tk.Frame(tab_modes, bg="#070C17")
        game_row.pack(fill=tk.X, pady=(2, 8))

        tk.Entry(game_row, textvariable=game_var, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(
            side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 8)
        )

        def browse_game_exe():
            path = filedialog.askopenfilename(
                parent=win,
                title="Select Game Executable",
                filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
            )
            if path:
                game_var.set(path)

        HudPillButton(
            game_row, text="BROWSE .EXE", command=browse_game_exe,
            width=105, height=28, bg="#0D1B30", fg="#00E5FF", border="#1F3D66"
        ).pack(side=tk.RIGHT)

        tk.Checkbutton(
            tab_modes, text="Auto-flush Ollama VRAM when entering Gaming Mode",
            variable=unload_vram_var, bg="#070C17", fg="#E2E8F0", selectcolor="#0D1627"
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(tab_modes, text="Extra Apps for This Mode (comma-separated):", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        tk.Entry(tab_modes, textvariable=apps_var, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=(2, 8))

        tk.Label(tab_modes, text="Batla Mode Unlock Quote:", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        tk.Entry(tab_modes, textvariable=batla_var, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=(2, 10))

        def save_modes_tab():
            m = mode_var.get()
            self.config.settings["modes"][m]["color"] = color_var.get().strip() or "#00E5FF"
            self.config.settings["modes"][m]["apps"] = [a.strip() for a in apps_var.get().split(",") if a.strip()]
            self.config.settings["modes"][m]["current_game"] = game_var.get().strip()
            self.config.settings["modes"][m]["unload_vram"] = unload_vram_var.get()
            self.config.settings["batla_quote"] = batla_var.get().strip()
            self.config.save_settings()
            self.target_color = self.config.settings["modes"][self.config.settings["active_mode"]]["color"]
            self._refresh_mode_pills()
            messagebox.showinfo("Saved", f"{m} Mode configuration saved!", parent=win)

        HudPillButton(
            tab_modes, text="SAVE MODE SETTINGS", command=save_modes_tab,
            width=220, height=32, bg="#0C2440", fg="#38BDF8", border="#1E4E82"
        ).pack(anchor="w", pady=6)

        # TAB 2: Vibe, Voice & HUD Tweaks
        tab_vibe = tk.Frame(nb, bg="#070C17", padx=14, pady=14)
        nb.add(tab_vibe, text="Vibe & HUD Tweaks")

        sfx_var = tk.BooleanVar(value=self.config.settings.get("sound_effects", True))
        reticle_var = tk.BooleanVar(value=self.config.settings.get("show_reticle", True))
        brackets_var = tk.BooleanVar(value=self.config.settings.get("show_brackets", True))
        auto_mic_var = tk.BooleanVar(value=self.config.settings.get("auto_listen_after_reply", False))

        for txt, var in [
            ("Enable Futuristic Sound FX", sfx_var),
            ("Show Outer Rotating HUD Reticle Rings", reticle_var),
            ("Show Corner Tactical Brackets", brackets_var),
            ("Auto-Listen on Mic After JARVIS Replies", auto_mic_var),
        ]:
            tk.Checkbutton(
                tab_vibe, text=txt, variable=var,
                bg="#070C17", fg="#E2E8F0", selectcolor="#0D1627"
            ).pack(anchor="w", pady=3)

        model_var = tk.StringVar(value=self.config.settings.get("ollama_model", "qwen2.5:3b"))
        tk.Label(tab_vibe, text="Ollama Model Tag:", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w", pady=(10, 2))
        tk.Entry(tab_vibe, textvariable=model_var, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5)

        intro_en = tk.BooleanVar(value=self.config.settings["intro_tweak"]["enabled"])
        tk.Checkbutton(
            tab_vibe, text="Enable Introductory Tweak & Permanent Memory",
            variable=intro_en, bg="#070C17", fg="#E2E8F0", selectcolor="#0D1627"
        ).pack(anchor="w", pady=(10, 2))

        persona_var = tk.StringVar(value=self.config.settings["intro_tweak"]["persona_tone"])
        tk.Label(tab_vibe, text="Persona / Vibe Directive:", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        tk.Entry(tab_vibe, textvariable=persona_var, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=(2, 8))

        ideo_en = tk.BooleanVar(value=self.config.settings["ideology"]["enabled"])
        tk.Checkbutton(
            tab_vibe, text="Enable Ideology (Context-Aware Idea Suggestions)",
            variable=ideo_en, bg="#070C17", fg="#E2E8F0", selectcolor="#0D1627"
        ).pack(anchor="w", pady=4)

        def save_vibe_tab():
            s = self.config.settings
            s["sound_effects"] = sfx_var.get()
            s["show_reticle"] = reticle_var.get()
            s["show_brackets"] = brackets_var.get()
            s["auto_listen_after_reply"] = auto_mic_var.get()
            chosen_model = model_var.get().strip() or "qwen2.5:3b"
            s["ollama_model"] = chosen_model
            self.brain.model = chosen_model
            s["intro_tweak"]["enabled"] = intro_en.get()
            s["intro_tweak"]["persona_tone"] = persona_var.get().strip()
            s["ideology"]["enabled"] = ideo_en.get()
            self.config.save_settings()
            messagebox.showinfo("Saved", "Vibe & HUD settings applied!", parent=win)

        HudPillButton(
            tab_vibe, text="SAVE VIBE SETTINGS", command=save_vibe_tab,
            width=200, height=32, bg="#0C2440", fg="#38BDF8", border="#1E4E82"
        ).pack(anchor="w", pady=10)

        # TAB 3: Custom Keyword Macros & Memory
        tab_kw = tk.Frame(nb, bg="#070C17", padx=14, pady=14)
        nb.add(tab_kw, text="Keywords & Memory")

        tk.Label(tab_kw, text="Keyword Phrase (e.g. set up workplace):", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        kw_trig = tk.StringVar()
        tk.Entry(tab_kw, textvariable=kw_trig, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=(2, 6))

        tk.Label(tab_kw, text="Targets / Apps (comma-separated):", fg="#94A3B8", bg="#070C17", font=("Consolas", 9)).pack(anchor="w")
        kw_apps = tk.StringVar()
        tk.Entry(tab_kw, textvariable=kw_apps, bg="#0D1627", fg="#F8FAFC", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=(2, 8))

        kw_listbox = tk.Listbox(
            tab_kw, bg="#0A1220", fg="#E2E8F0", selectbackground="#183153",
            relief=tk.FLAT, height=7, font=("Consolas", 9)
        )
        kw_listbox.pack(fill=tk.X, pady=4)

        def refresh_kw_list():
            kw_listbox.delete(0, tk.END)
            for k, v in self.config.settings.get("custom_keywords", {}).items():
                kw_listbox.insert(tk.END, f"{k}  ->  {', '.join(v)}")

        refresh_kw_list()

        def add_kw():
            t = kw_trig.get().strip().lower()
            a = [x.strip() for x in kw_apps.get().split(",") if x.strip()]
            if t and a:
                self.config.settings.setdefault("custom_keywords", {})[t] = a
                self.config.save_settings()
                kw_trig.set("")
                kw_apps.set("")
                refresh_kw_list()

        def remove_selected_kw():
            sel = kw_listbox.curselection()
            if not sel:
                return
            line = kw_listbox.get(sel[0])
            key = line.split("  ->  ", 1)[0]
            self.config.settings.get("custom_keywords", {}).pop(key, None)
            self.config.save_settings()
            refresh_kw_list()

        kw_btns = tk.Frame(tab_kw, bg="#070C17")
        kw_btns.pack(fill=tk.X, pady=6)
        HudPillButton(kw_btns, text="+ ADD MACRO", command=add_kw, width=120, height=28, bg="#0C2440", fg="#38BDF8", border="#1E4E82").pack(side=tk.LEFT, padx=(0, 8))
        HudPillButton(kw_btns, text="REMOVE SELECTED", command=remove_selected_kw, width=145, height=28, bg="#261018", fg="#FDA4AF", border="#5C1D33").pack(side=tk.LEFT)

        # TAB 4: Secret Developer Mode
        tab_dev = tk.Frame(nb, bg="#070C17", padx=14, pady=14)
        nb.add(tab_dev, text="Developer Mode")

        tk.Label(tab_dev, text="Developer Access Code (Default: STARK-DEV):", fg="#E2E8F0", bg="#070C17", font=("Consolas", 9, "bold")).pack(anchor="w")
        code_var = tk.StringVar()
        tk.Entry(tab_dev, textvariable=code_var, show="*", bg="#0D1627", fg="#00E5FF", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=6)

        dev_controls = tk.Frame(tab_dev, bg="#070C17")

        def render_dev_controls():
            for w in dev_controls.winfo_children():
                w.destroy()
            if not self.config.settings.get("developer_mode_unlocked", False):
                tk.Label(dev_controls, text="🔒 Developer GUI Customizer Locked.", fg="#64748B", bg="#070C17").pack(anchor="w", pady=10)
                return

            tk.Label(dev_controls, text="🔓 DEVELOPER MODE UNLOCKED", fg="#00FF9D", bg="#070C17", font=("Consolas", 9, "bold")).pack(anchor="w", pady=(6, 8))
            core_var = tk.StringVar(value=self.config.settings.get("dev_core_style", "arc_reactor"))
            tk.Radiobutton(dev_controls, text="Multi-Layer Arc Reactor Core", variable=core_var, value="arc_reactor", bg="#070C17", fg="white", selectcolor="#0D1627").pack(anchor="w")
            tk.Radiobutton(dev_controls, text="3D Connecting-Dots Constellation Sphere", variable=core_var, value="constellation", bg="#070C17", fg="white", selectcolor="#0D1627").pack(anchor="w")

            dots_var = tk.IntVar(value=self.config.settings.get("dev_dot_count", 84))
            tk.Label(dev_controls, text="Constellation Node Count:", fg="#94A3B8", bg="#070C17").pack(anchor="w", pady=(8, 2))
            tk.Scale(dev_controls, from_=30, to=150, orient=tk.HORIZONTAL, variable=dots_var, bg="#070C17", fg="white", highlightthickness=0).pack(fill=tk.X)

            def apply_dev():
                self.config.settings["dev_core_style"] = core_var.get()
                self.config.settings["dev_dot_count"] = dots_var.get()
                self.sphere_points = self._generate_sphere_points(dots_var.get())
                self.config.save_settings()
                self.modes.play_fx("arc_assemble")

            HudPillButton(
                dev_controls, text="APPLY CORE TWEAKS", command=apply_dev,
                width=180, height=30, bg="#0B2E22", fg="#00FF9D", border="#1B664B"
            ).pack(anchor="w", pady=12)

        def unlock_dev():
            secret = self.config.settings.get("developer_secret_code", "STARK-DEV")
            if code_var.get().strip() == secret:
                self.config.settings["developer_mode_unlocked"] = True
                self.config.save_settings()
                self.modes.play_fx("arc_assemble")
                render_dev_controls()
            else:
                messagebox.showerror("Access Denied", "Invalid Developer Code.", parent=win)

        HudPillButton(
            tab_dev, text="UNLOCK DEVELOPER MODE", command=unlock_dev,
            width=190, height=30, bg="#0D1B30", fg="#00E5FF", border="#1F3D66"
        ).pack(anchor="w")
        dev_controls.pack(fill=tk.BOTH, expand=True, pady=8)
        render_dev_controls()


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from jarvis_config import JarvisConfig
from jarvis_modes import JarvisModeEngine
from jarvis_ears import JarvisEars
from jarvis_speaker import JarvisSpeaker
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
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


class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S // HUD & AUTONOMOUS CORE")
        self.root.geometry("1220x780")
        self.root.minsize(1020, 680)
        self.root.configure(bg="#04070D")

        self.config = JarvisConfig()
        self.speaker = JarvisSpeaker()
        self.listener = JarvisEars()
        self.task_engine = TaskEngine()
        self.system = JarvisSystem()
        self.brain = JarvisBrain(task_engine=self.task_engine, model="qwen2.5:3b")
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

        self._build_layout()
        self._bind_shortcuts()
        self._animate()
        self._welcome_sequence()

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
        self.top_bar = tk.Frame(self.root, bg="#080E1A", height=54, padx=16)
        self.top_bar.pack(fill=tk.X, side=tk.TOP)

        self.title_lbl = tk.Label(
            self.top_bar, text="◈ J.A.R.V.I.S // HUD CORE",
            fg=self.current_color, bg="#080E1A", font=("Consolas", 13, "bold")
        )
        self.title_lbl.pack(side=tk.LEFT, pady=12)

        mode_frame = tk.Frame(self.top_bar, bg="#080E1A")
        mode_frame.pack(side=tk.LEFT, padx=20)
        self.mode_buttons = {}
        for m_name in ["Normal", "Gaming", "Productivity", "Batla"]:
            btn = tk.Button(
                mode_frame, text=m_name.upper(),
                command=lambda m=m_name: self.switch_mode(m),
                bg="#0F1728", fg="#94A3B8", activebackground="#18253F",
                relief=tk.FLAT, font=("Consolas", 9, "bold"), padx=10, pady=4, cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=4)
            self.mode_buttons[m_name] = btn

        self.settings_btn = tk.Button(
            self.top_bar, text="⚙ SETTINGS", command=self.open_settings,
            bg="#0F1728", fg="#E2E8F0", relief=tk.FLAT, font=("Consolas", 9, "bold"),
            padx=10, pady=4, cursor="hand2"
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=4)

        self.idea_btn = tk.Button(
            self.top_bar, text="💡 IDEOLOGY", command=self.trigger_ideology,
            bg="#0F1728", fg="#FBBF24", relief=tk.FLAT, font=("Consolas", 9, "bold"),
            padx=10, pady=4, cursor="hand2"
        )
        self.idea_btn.pack(side=tk.RIGHT, padx=4)

        self.chat_speak_btn = tk.Button(
            self.top_bar,
            text=f"MODE: {self.config.settings.get('chat_speak_mode', 'Speak').upper()}",
            command=self.toggle_chat_speak,
            bg="#0F1728", fg="#38BDF8", relief=tk.FLAT, font=("Consolas", 9, "bold"),
            padx=10, pady=4, cursor="hand2"
        )
        self.chat_speak_btn.pack(side=tk.RIGHT, padx=4)

        body = tk.Frame(self.root, bg="#04070D")
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        left_panel = tk.Frame(body, bg="#060B14", highlightbackground="#132036", highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.canvas = tk.Canvas(left_panel, bg="#04070D", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Double-Button-1>", self.toggle_recent_tasks_overlay)

        self.hint_lbl = tk.Label(
            left_panel,
            text="Voice switches modes (e.g. 'Gaming mode')  |  Double-click core: Recent Tasks  |  Right-click: Mic",
            fg="#64748B", bg="#060B14", font=("Consolas", 9)
        )
        self.hint_lbl.pack(side=tk.BOTTOM, pady=6)

        right_panel = tk.Frame(body, bg="#060B14", width=440, highlightbackground="#132036", highlightthickness=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_panel.pack_propagate(False)

        tel_bar = tk.Frame(right_panel, bg="#0A1220", pady=6, padx=10)
        tel_bar.pack(fill=tk.X)
        self.status_lbl = tk.Label(
            tel_bar, text="ACTIVE MODE: NORMAL", fg=self.current_color,
            bg="#0A1220", font=("Consolas", 10, "bold")
        )
        self.status_lbl.pack(side=tk.LEFT)

        self.diag_btn = tk.Button(
            tel_bar, text="TELEMETRY", command=self.show_telemetry,
            bg="#121E33", fg="#94A3B8", relief=tk.FLAT, font=("Consolas", 8, "bold"),
            padx=8, pady=2, cursor="hand2"
        )
        self.diag_btn.pack(side=tk.RIGHT)

        self.chat_box = tk.Text(
            right_panel, bg="#050911", fg="#E2E8F0", font=("Consolas", 10),
            wrap=tk.WORD, relief=tk.FLAT, padx=12, pady=10, state=tk.DISABLED
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        input_bar = tk.Frame(right_panel, bg="#0A1220", padx=8, pady=8)
        input_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.entry = tk.Entry(
            input_bar, bg="#0F192B", fg="#F8FAFC", insertbackground="#00E5FF",
            relief=tk.FLAT, font=("Consolas", 10)
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 6))
        self.entry.bind("<Return>", lambda e: self.handle_text_submit())

        self.mic_btn = tk.Button(
            input_bar, text="🎤", command=self.trigger_voice_listen,
            bg="#121E33", fg="#00E5FF", relief=tk.FLAT, font=("Segoe UI Emoji", 10),
            padx=8, pady=3, cursor="hand2"
        )
        self.mic_btn.pack(side=tk.RIGHT, padx=(4, 0))

        send_btn = tk.Button(
            input_bar, text="SEND", command=self.handle_text_submit,
            bg="#0284C7", fg="white", relief=tk.FLAT, font=("Consolas", 9, "bold"),
            padx=10, pady=5, cursor="hand2"
        )
        send_btn.pack(side=tk.RIGHT)

        self._refresh_mode_buttons()

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
            com_initialized = False
            try:
                import pythoncom
                pythoncom.CoInitialize()
                com_initialized = True
            except Exception:
                pass

            self.is_speaking = True
            try:
                self.speaker.speak(str(text))
            finally:
                self.is_speaking = False
                if com_initialized:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        threading.Thread(target=_run, daemon=True).start()
       
    def _welcome_sequence(self):
        intro = self.config.settings.get("intro_tweak", {})
        if intro.get("enabled", True):
            last_work = self.config.memory.get("last_work", "Local JARVIS Engine")
            msg = intro.get("welcome_template", "All systems online, Boss.").format(last_work=last_work)
        else:
            msg = "All systems online and running locally, Boss."
        self.log("JARVIS", msg)
        self.speak_async(msg)

    def switch_mode(self, mode_name):
        res = self.modes.activate_mode(mode_name)
        self.target_color = self.config.settings["modes"][mode_name]["color"]
        self._refresh_mode_buttons()
        self.log("SYSTEM", res)
        self.speak_async(f"{mode_name} mode activated.")

    def _refresh_mode_buttons(self):
        active = self.config.settings.get("active_mode", "Normal")
        color = self.config.settings["modes"].get(active, {}).get("color", "#00E5FF")
        self.status_lbl.configure(text=f"ACTIVE MODE: {active.upper()}", fg=color)
        for m, btn in self.mode_buttons.items():
            if m == active:
                btn.configure(bg=color, fg="#04070D")
            else:
                btn.configure(bg="#0F1728", fg="#94A3B8")

    def toggle_chat_speak(self):
        curr = self.config.settings.get("chat_speak_mode", "Speak")
        nxt = "Chat" if curr == "Speak" else "Speak"
        self.config.settings["chat_speak_mode"] = nxt
        self.config.save_settings()
        self.chat_speak_btn.configure(text=f"MODE: {nxt.upper()}")
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
        self.mic_btn.configure(bg="#EF4444", fg="white")
        self.log("EARS", "Listening...")

        def _worker():
            try:
                text = self.listener.listen_command()
            except Exception as e:
                text = None
                self.root.after(0, lambda: self.log("ERROR", f"Mic error: {e}"))
            finally:
                self.is_listening = False
                self.root.after(0, lambda: self.mic_btn.configure(bg="#121E33", fg="#00E5FF"))

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
            res = self.system.open_app(app)
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

    def _animate(self):
        self.current_color = blend_color(self.current_color, self.target_color, 0.12)
        self.title_lbl.configure(fg=self.current_color)
        self.entry.configure(insertbackground=self.current_color)

        dev_unlocked = self.config.settings.get("developer_mode_unlocked", False)
        core_style = self.config.settings.get("dev_core_style", "arc_reactor")

        if dev_unlocked and core_style == "arc_reactor":
            self.arc_build_progress = min(1.0, self.arc_build_progress + 0.025)
        else:
            self.arc_build_progress = max(0.0, self.arc_build_progress - 0.04)

        self.angle += 0.024 if not self.is_speaking else 0.055
        self.pulse_phase += 0.28 if self.is_speaking else 0.08

        self.canvas.delete("all")
        w = max(200, self.canvas.winfo_width())
        h = max(200, self.canvas.winfo_height())
        cx, cy = w / 2, h / 2

        pulse_amp = self.config.settings.get("dev_pulse_intensity", 1.35) if self.is_speaking else 1.06
        pulse = 1.0 + (pulse_amp - 1.0) * (0.5 + 0.5 * math.sin(self.pulse_phase))
        base_r = min(w, h) * 0.23 * pulse

        self._draw_hud_reticle(cx, cy, min(w, h) * 0.34)

        if self.arc_build_progress > 0.05:
            self._draw_arc_reactor(cx, cy, base_r, self.arc_build_progress)
        else:
            self._draw_constellation_sphere(cx, cy, base_r)

        if self.recent_menu_visible:
            self._draw_recent_tasks_network(cx, cy, base_r)

        self.root.after(30, self._animate)

    def _draw_hud_reticle(self, cx, cy, outer_r):
        dim_ring = blend_color("#04070D", self.current_color, 0.28)
        bright_ring = blend_color("#04070D", self.current_color, 0.58)

        self.canvas.create_oval(
            cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
            outline=dim_ring, width=1
        )
        for seg in range(4):
            start_deg = math.degrees(self.angle * 0.7) + seg * 90
            self.canvas.create_arc(
                cx - outer_r * 0.94, cy - outer_r * 0.94,
                cx + outer_r * 0.94, cy + outer_r * 0.94,
                start=start_deg, extent=32, style=tk.ARC,
                outline=bright_ring, width=2
            )

        b = 18
        pad = 22
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
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
        if p > 0.05:
            s1 = min(1.0, p / 0.35)
            self.canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90, extent=359.9 * s1, style=tk.ARC,
                outline=self.current_color, width=3
            )

        if p > 0.30:
            coils = int(((p - 0.30) / 0.40) * 10)
            for i in range(min(10, coils)):
                ang = math.radians(i * 36) + self.angle * 0.6
                x1, y1 = cx + math.cos(ang) * (r * 0.52), cy + math.sin(ang) * (r * 0.52)
                x2, y2 = cx + math.cos(ang) * (r * 0.92), cy + math.sin(ang) * (r * 0.92)
                self.canvas.create_line(x1, y1, x2, y2, fill=self.current_color, width=5)

        if p > 0.65:
            s3 = min(1.0, (p - 0.65) / 0.35)
            ir = r * 0.42 * s3
            glow = blend_color(self.current_color, "#FFFFFF", 0.55)
            self.canvas.create_oval(
                cx - ir, cy - ir, cx + ir, cy + ir,
                outline=glow, width=3, fill=blend_color("#04070D", self.current_color, 0.25)
            )
            self.canvas.create_text(
                cx, cy + r + 24, text="ARC REACTOR CORE // DEVELOPER MODE",
                fill=self.current_color, font=("Consolas", 9, "bold")
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

            card_w, card_h = 196, 44
            self.canvas.create_rectangle(
                bx - card_w / 2, by - card_h / 2, bx + card_w / 2, by + card_h / 2,
                fill="#0A1220", outline=self.current_color, width=1
            )
            short_txt = item if len(item) <= 28 else item[:25] + "..."
            self.canvas.create_text(
                bx, by, text=short_txt, fill="#F1F5F9", font=("Consolas", 8)
            )

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("JARVIS Settings & Developer Tweaks")
        win.geometry("620x640")
        win.configure(bg="#080E1A")

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_modes = tk.Frame(nb, bg="#080E1A", padx=12, pady=12)
        nb.add(tab_modes, text="Modes & Apps")

        mode_var = tk.StringVar(value=self.config.settings.get("active_mode", "Normal"))
        tk.Label(tab_modes, text="Configure Mode:", fg="#E2E8F0", bg="#080E1A", font=("Consolas", 10, "bold")).pack(anchor="w")
        mode_menu = ttk.Combobox(tab_modes, textvariable=mode_var, values=["Normal", "Gaming", "Productivity", "Batla"], state="readonly")
        mode_menu.pack(fill=tk.X, pady=4)

        color_var = tk.StringVar()
        apps_var = tk.StringVar()
        game_var = tk.StringVar()
        batla_var = tk.StringVar(value=self.config.settings.get("batla_quote", "JA CHAT SEY KOUD JA"))

        def load_mode_fields(*_):
            m = mode_var.get()
            cfg = self.config.settings["modes"][m]
            color_var.set(cfg.get("color", "#00E5FF"))
            apps_var.set(", ".join(cfg.get("apps", [])))
            game_var.set(cfg.get("current_game", ""))

        mode_menu.bind("<<ComboboxSelected>>", load_mode_fields)
        load_mode_fields()

        for lbl_txt, var in [
            ("Mode Accent Color (Hex):", color_var),
            ("Auto-Launch Apps (comma-separated):", apps_var),
            ("Gaming Mode Active Game:", game_var),
            ("Batla Mode Unlock Quote:", batla_var),
        ]:
            tk.Label(tab_modes, text=lbl_txt, fg="#94A3B8", bg="#080E1A", font=("Consolas", 9)).pack(anchor="w", pady=(8, 2))
            tk.Entry(tab_modes, textvariable=var, bg="#0F192B", fg="white", relief=tk.FLAT).pack(fill=tk.X, ipady=4)

        sfx_var = tk.BooleanVar(value=self.config.settings.get("sound_effects", True))
        tk.Checkbutton(
            tab_modes, text="Enable Futuristic Sound Effects", variable=sfx_var,
            bg="#080E1A", fg="#E2E8F0", selectcolor="#0F192B"
        ).pack(anchor="w", pady=10)

        def save_modes_tab():
            m = mode_var.get()
            self.config.settings["modes"][m]["color"] = color_var.get().strip() or "#00E5FF"
            self.config.settings["modes"][m]["apps"] = [a.strip() for a in apps_var.get().split(",") if a.strip()]
            if m == "Gaming":
                self.config.settings["modes"][m]["current_game"] = game_var.get().strip()
            self.config.settings["batla_quote"] = batla_var.get().strip()
            self.config.settings["sound_effects"] = sfx_var.get()
            self.config.save_settings()
            self.target_color = self.config.settings["modes"][self.config.settings["active_mode"]]["color"]
            self._refresh_mode_buttons()
            messagebox.showinfo("Saved", f"{m} Mode settings updated!", parent=win)

        tk.Button(tab_modes, text="SAVE MODE SETTINGS", command=save_modes_tab, bg="#0284C7", fg="white", relief=tk.FLAT, pady=6).pack(fill=tk.X, pady=10)

        tab_ai = tk.Frame(nb, bg="#080E1A", padx=12, pady=12)
        nb.add(tab_ai, text="Memory & Keywords")

        intro_en = tk.BooleanVar(value=self.config.settings["intro_tweak"]["enabled"])
        tk.Checkbutton(tab_ai, text="Enable Introductory Tweak & Permanent Memory", variable=intro_en, bg="#080E1A", fg="#E2E8F0", selectcolor="#0F192B").pack(anchor="w")

        persona_var = tk.StringVar(value=self.config.settings["intro_tweak"]["persona_tone"])
        tk.Label(tab_ai, text="AI Personality / Tone:", fg="#94A3B8", bg="#080E1A").pack(anchor="w", pady=(6, 2))
        tk.Entry(tab_ai, textvariable=persona_var, bg="#0F192B", fg="white", relief=tk.FLAT).pack(fill=tk.X, ipady=4)

        ideo_en = tk.BooleanVar(value=self.config.settings["ideology"]["enabled"])
        tk.Checkbutton(tab_ai, text="Enable Ideology (Context-Aware Idea Suggestions)", variable=ideo_en, bg="#080E1A", fg="#E2E8F0", selectcolor="#0F192B").pack(anchor="w", pady=(10, 4))

        tk.Label(tab_ai, text="Add Custom Keyword Macro (e.g., set up workplace):", fg="#E2E8F0", bg="#080E1A", font=("Consolas", 9, "bold")).pack(anchor="w", pady=(10, 2))
        kw_trigger_var = tk.StringVar()
        kw_apps_var = tk.StringVar()
        tk.Entry(tab_ai, textvariable=kw_trigger_var, bg="#0F192B", fg="white", relief=tk.FLAT).pack(fill=tk.X, ipady=4, pady=2)
        tk.Label(tab_ai, text="Apps to Launch (comma-separated, e.g., code, chrome):", fg="#94A3B8", bg="#080E1A").pack(anchor="w")
        tk.Entry(tab_ai, textvariable=kw_apps_var, bg="#0F192B", fg="white", relief=tk.FLAT).pack(fill=tk.X, ipady=4, pady=2)

        def save_ai_tab():
            self.config.settings["intro_tweak"]["enabled"] = intro_en.get()
            self.config.settings["intro_tweak"]["persona_tone"] = persona_var.get().strip()
            self.config.settings["ideology"]["enabled"] = ideo_en.get()
            trig = kw_trigger_var.get().strip().lower()
            apps = [a.strip() for a in kw_apps_var.get().split(",") if a.strip()]
            if trig and apps:
                self.config.settings["custom_keywords"][trig] = apps
            self.config.save_settings()
            messagebox.showinfo("Saved", "Memory, Ideology & Keyword Macros saved!", parent=win)

        tk.Button(tab_ai, text="SAVE MEMORY & KEYWORDS", command=save_ai_tab, bg="#0284C7", fg="white", relief=tk.FLAT, pady=6).pack(fill=tk.X, pady=12)

        tab_dev = tk.Frame(nb, bg="#080E1A", padx=12, pady=12)
        nb.add(tab_dev, text="Developer Mode")

        tk.Label(tab_dev, text="Enter Developer Access Code (Default: STARK-DEV):", fg="#E2E8F0", bg="#080E1A", font=("Consolas", 10, "bold")).pack(anchor="w")
        code_var = tk.StringVar()
        tk.Entry(tab_dev, textvariable=code_var, show="*", bg="#0F192B", fg="#00E5FF", relief=tk.FLAT).pack(fill=tk.X, ipady=5, pady=6)

        dev_controls = tk.Frame(tab_dev, bg="#080E1A")

        def render_dev_controls():
            for w in dev_controls.winfo_children():
                w.destroy()
            if not self.config.settings.get("developer_mode_unlocked", False):
                tk.Label(dev_controls, text="🔒 Developer GUI Customizer Locked.", fg="#64748B", bg="#080E1A").pack(anchor="w", pady=10)
                return

            tk.Label(dev_controls, text="🔓 DEVELOPER MODE ACTIVE — ARC REACTOR UNLOCKED", fg="#00FF9D", bg="#080E1A", font=("Consolas", 9, "bold")).pack(anchor="w", pady=(6, 10))
            core_var = tk.StringVar(value=self.config.settings.get("dev_core_style", "arc_reactor"))
            tk.Radiobutton(dev_controls, text="Arc Reactor Core (Piece-by-Piece Assembly)", variable=core_var, value="arc_reactor", bg="#080E1A", fg="white", selectcolor="#0F192B").pack(anchor="w")
            tk.Radiobutton(dev_controls, text="3D Connecting-Dots Constellation Sphere", variable=core_var, value="constellation", bg="#080E1A", fg="white", selectcolor="#0F192B").pack(anchor="w")

            dots_var = tk.IntVar(value=self.config.settings.get("dev_dot_count", 84))
            tk.Label(dev_controls, text="Sphere Node Count:", fg="#94A3B8", bg="#080E1A").pack(anchor="w", pady=(8, 2))
            tk.Scale(dev_controls, from_=30, to=140, orient=tk.HORIZONTAL, variable=dots_var, bg="#080E1A", fg="white", highlightthickness=0).pack(fill=tk.X)

            def apply_dev():
                self.config.settings["dev_core_style"] = core_var.get()
                self.config.settings["dev_dot_count"] = dots_var.get()
                self.sphere_points = self._generate_sphere_points(dots_var.get())
                self.config.save_settings()
                self.modes.play_fx("arc_assemble")

            tk.Button(dev_controls, text="APPLY DEVELOPER GUI TWEAKS", command=apply_dev, bg="#00FF9D", fg="#04070D", font=("Consolas", 9, "bold"), relief=tk.FLAT, pady=6).pack(fill=tk.X, pady=12)

        def unlock_dev():
            secret = self.config.settings.get("developer_secret_code", "STARK-DEV")
            if code_var.get().strip() == secret:
                self.config.settings["developer_mode_unlocked"] = True
                self.config.save_settings()
                self.modes.play_fx("arc_assemble")
                render_dev_controls()
            else:
                messagebox.showerror("Access Denied", "Invalid Developer Code.", parent=win)

        tk.Button(tab_dev, text="UNLOCK DEVELOPER MODE", command=unlock_dev, bg="#162238", fg="#00E5FF", relief=tk.FLAT, pady=5).pack(fill=tk.X)
        dev_controls.pack(fill=tk.BOTH, expand=True, pady=8)
        render_dev_controls()


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
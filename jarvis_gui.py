import ctypes
import json
import math
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from jarvis_config import JarvisConfig
from jarvis_modes import JarvisModeEngine
from jarvis_ears import JarvisEars
from jarvis_speaker import JarvisSpeaker
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain


def apply_dark_title_bar(window):
    """Forces dark title bar on Windows 10/11 via DWM."""
    if sys.platform != "win32":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        value = ctypes.c_int(1)
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Win 11 / Win 10 20H1+), fallback 19
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 19, ctypes.byref(value), ctypes.sizeof(value)
            )
    except Exception:
        pass


def hex_to_rgb(hex_color):
    hex_color = (hex_color or "#00E5FF").lstrip("#")
    if len(hex_color) != 6:
        return (0, 229, 255)
    try:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 229, 255)


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


def rotate_3d(x, y, z, ax, ay, az):
    ca, sa = math.cos(ax), math.sin(ax)
    y1 = y * ca - z * sa
    z1 = y * sa + z * ca
    x1 = x

    cb, sb = math.cos(ay), math.sin(ay)
    x2 = x1 * cb + z1 * sb
    z2 = -x1 * sb + z1 * cb
    y2 = y1

    cc, sc = math.cos(az), math.sin(az)
    x3 = x2 * cc - y2 * sc
    y3 = x2 * sc + y2 * cc
    z3 = z2
    return x3, y3, z3


class HudPillButton(tk.Canvas):
    """Modern sleek rounded button — works safely inside any tk container."""

    def __init__(
        self, parent, text, command, width=104, height=30,
        bg="#0F192B", fg="#CBD5E1", border="#1E3150",
        active_bg=None, active_fg="#05080F", font=("Segoe UI", 8, "bold"),
        parent_bg=None
    ):
        if parent_bg is None:
            try:
                parent_bg = parent.cget("bg")
            except Exception:
                parent_bg = "#080D18"

        super().__init__(
            parent, width=width, height=height,
            bg=parent_bg, highlightthickness=0, bd=0, cursor="hand2"
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

    def set_style(self, fg=None, border=None, active=None, text=None, active_bg=None):
        if fg is not None:
            self.base_fg = fg
        if border is not None:
            self.base_border = border
        if active is not None:
            self.is_active = active
        if text is not None:
            self.text = text
        if active_bg is not None:
            self.active_bg = active_bg
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

    def _rounded_poly(self, x1, y1, x2, y2, r=10):
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
            fill = blend_color(self.base_bg, self.base_border, 0.30) if self.hovered else self.base_bg
            outline = self.base_fg if self.hovered else self.base_border
            txt_col = "#FFFFFF" if self.hovered else self.base_fg

        pts = self._rounded_poly(1, 1, w - 1, h - 1, r=10)
        self.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=1)
        self.create_text(w / 2, h / 2, text=self.text, fill=txt_col, font=self.font)


class ModernToggleRow(tk.Frame):
    """2026-style toggle switch row — replaces classic boxy checkbuttons."""

    def __init__(self, parent, label_text, initial=True, accent="#00E5FF", on_change=None):
        bg = parent.cget("bg")
        super().__init__(parent, bg=bg, pady=5)
        self.state_val = bool(initial)
        self.accent = accent
        self.on_change = on_change

        lbl = tk.Label(self, text=label_text, bg=bg, fg="#E2E8F0", font=("Segoe UI", 9))
        lbl.pack(side=tk.LEFT)

        self.sw = tk.Canvas(self, width=42, height=22, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.sw.pack(side=tk.RIGHT)
        self.sw.bind("<Button-1>", self.toggle)
        lbl.bind("<Button-1>", self.toggle)
        self.redraw()

    def get(self):
        return self.state_val

    def set(self, val):
        self.state_val = bool(val)
        self.redraw()

    def toggle(self, _=None):
        self.state_val = not self.state_val
        self.redraw()
        if callable(self.on_change):
            self.on_change(self.state_val)

    def redraw(self):
        self.sw.delete("all")
        track = self.accent if self.state_val else "#18243A"
        knob = "#05080F" if self.state_val else "#94A3B8"
        self.sw.create_oval(1, 1, 21, 21, fill=track, outline="")
        self.sw.create_oval(21, 1, 41, 21, fill=track, outline="")
        self.sw.create_rectangle(11, 1, 31, 21, fill=track, outline="")
        kx = 22 if self.state_val else 4
        self.sw.create_oval(kx, 4, kx + 14, 18, fill=knob, outline="")


class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S")
        self.root.geometry("1260x800")
        self.root.minsize(1040, 680)
        self.root.configure(bg="#060911")
        apply_dark_title_bar(self.root)

        self.config = JarvisConfig()
        self._ensure_defaults()

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
        self.speech_phase = 0.0
        self.arc_build_progress = 0.0
        self.explode_cycle = 0.0
        self.recent_menu_visible = False
        self.settings_win = None

        self.sphere_points = self._generate_sphere_points(
            self.config.settings.get("dev_dot_count", 84)
        )

        self._build_layout()
        self._bind_shortcuts()
        self._animate()
        self._welcome_sequence()

    def _ensure_defaults(self):
        s = self.config.settings
        s.setdefault("address_as", "Boss")
        s.setdefault("ollama_model", "qwen2.5:3b")
        s.setdefault("show_reticle", True)
        s.setdefault("show_brackets", True)
        s.setdefault("auto_listen_after_reply", False)
        s.setdefault("dev_explode_amount", 0.45)
        if s.get("modes", {}).get("Gaming", {}).get("color") == "#FF2A6D":
            s["modes"]["Gaming"]["color"] = "#FF7A00"
            self.config.save_settings()

    def _address(self):
        return (self.config.settings.get("address_as") or "Boss").strip()

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
        self.top_bar = tk.Frame(self.root, bg="#080D18", height=54, padx=16)
        self.top_bar.pack(fill=tk.X, side=tk.TOP)

        self.title_lbl = tk.Label(
            self.top_bar, text=f"◈ J.A.R.V.I.S  //  {self._address().upper()}",
            fg=self.current_color, bg="#080D18", font=("Segoe UI", 11, "bold")
        )
        self.title_lbl.pack(side=tk.LEFT, pady=12)

        mode_frame = tk.Frame(self.top_bar, bg="#080D18")
        mode_frame.pack(side=tk.LEFT, padx=18)
        self.mode_pills = {}
        for m_name in ["Normal", "Gaming", "Productivity", "Batla"]:
            pill = HudPillButton(
                mode_frame, text=m_name.upper(),
                command=lambda m=m_name: self.switch_mode(m),
                width=102, height=28, bg="#0E1728", fg="#9FB0C7", border="#182740",
                font=("Segoe UI", 8, "bold")
            )
            pill.pack(side=tk.LEFT, padx=3, pady=10)
            self.mode_pills[m_name] = pill

        self.settings_pill = HudPillButton(
            self.top_bar, text="SETTINGS", command=self.open_settings,
            width=92, height=28, bg="#0E1728", fg="#E6EDF7", border="#203352",
            font=("Segoe UI", 8, "bold")
        )
        self.settings_pill.pack(side=tk.RIGHT, padx=3, pady=10)

        self.idea_pill = HudPillButton(
            self.top_bar, text="IDEOLOGY", command=self.trigger_ideology,
            width=92, height=28, bg="#0E1728", fg="#FBBF24", border="#3B3016",
            font=("Segoe UI", 8, "bold")
        )
        self.idea_pill.pack(side=tk.RIGHT, padx=3, pady=10)

        self.chat_speak_pill = HudPillButton(
            self.top_bar,
            text=f"VOICE: {self.config.settings.get('chat_speak_mode', 'Speak').upper()}",
            command=self.toggle_chat_speak,
            width=110, height=28, bg="#0E1728", fg="#38BDF8", border="#18324C",
            font=("Segoe UI", 8, "bold")
        )
        self.chat_speak_pill.pack(side=tk.RIGHT, padx=3, pady=10)

        body = tk.Frame(self.root, bg="#060911")
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        left_panel = tk.Frame(body, bg="#080D18", bd=0)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.canvas = tk.Canvas(left_panel, bg="#060911", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Double-Button-1>", self.toggle_recent_tasks_overlay)

        self.hint_lbl = tk.Label(
            left_panel,
            text="Say a mode ('Gaming mode')  ·  Double-click core for recent tasks  ·  Right-click to speak",
            fg="#5B6E8A", bg="#080D18", font=("Segoe UI", 8)
        )
        self.hint_lbl.pack(side=tk.BOTTOM, pady=7)

        right_panel = tk.Frame(body, bg="#080D18", width=445, bd=0)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_panel.pack_propagate(False)

        tel_bar = tk.Frame(right_panel, bg="#0B1220", pady=8, padx=12)
        tel_bar.pack(fill=tk.X)
        self.status_lbl = tk.Label(
            tel_bar, text=f"MODE: {self.config.settings.get('active_mode', 'Normal').upper()}",
            fg=self.current_color, bg="#0B1220", font=("Segoe UI", 9, "bold")
        )
        self.status_lbl.pack(side=tk.LEFT)

        self.diag_pill = HudPillButton(
            tel_bar, text="TELEMETRY", command=self.show_telemetry,
            width=86, height=22, bg="#101A2E", fg="#9FB0C7", border="#1D2F4E",
            font=("Segoe UI", 8, "bold")
        )
        self.diag_pill.pack(side=tk.RIGHT)

        self.chat_box = tk.Text(
            right_panel, bg="#070B14", fg="#E6EDF7", font=("Segoe UI", 10),
            wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=12, pady=10, state=tk.DISABLED
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        input_wrap = tk.Frame(right_panel, bg="#0B1220", padx=8, pady=8)
        input_wrap.pack(fill=tk.X, side=tk.BOTTOM)

        self.entry = tk.Entry(
            input_wrap, bg="#0E1728", fg="#F8FAFC", insertbackground=self.current_color,
            relief=tk.FLAT, bd=0, font=("Segoe UI", 10)
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(4, 8))
        self.entry.bind("<Return>", lambda e: self.handle_text_submit())

        self.send_pill = HudPillButton(
            input_wrap, text="SEND", command=self.handle_text_submit,
            width=64, height=28, bg="#0D2440", fg="#38BDF8", border="#1C4B7D",
            font=("Segoe UI", 8, "bold")
        )
        self.send_pill.pack(side=tk.LEFT, padx=(0, 4))

        self.mic_pill = HudPillButton(
            input_wrap, text="MIC", command=self.trigger_voice_listen,
            width=54, height=28, bg="#0E1A30", fg="#00E5FF", border="#1C375A",
            font=("Segoe UI", 8, "bold")
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
        addr = self._address()
        if intro.get("enabled", True):
            last_work = self.config.memory.get("last_work", "Day 10 HUD & 3D Core")
            tmpl = intro.get("welcome_template", "Good to see you, {address}. Last time we were into: {last_work}.")
            try:
                msg = tmpl.format(address=addr, last_work=last_work)
            except Exception:
                msg = f"Good to see you, {addr}."
        else:
            msg = f"I'm here, {addr}."
        self.log("JARVIS", msg)
        self.speak_async(msg)

    def switch_mode(self, mode_name):
        res = self.modes.activate_mode(mode_name)
        self.target_color = self.config.settings["modes"][mode_name]["color"]
        self._refresh_mode_pills()
        self.log("JARVIS", res)
        self.speak_async(f"Switching to {mode_name}, {self._address()}.")

    def _refresh_mode_pills(self):
        active = self.config.settings.get("active_mode", "Normal")
        color = self.config.settings["modes"].get(active, {}).get("color", "#00E5FF")
        self.status_lbl.configure(text=f"MODE: {active.upper()}", fg=color)
        for m, pill in self.mode_pills.items():
            if m == active:
                pill.set_style(fg="#05080F", border=color, active=True, active_bg=color)
            else:
                pill.set_style(fg="#9FB0C7", border="#182740", active=False)

    def toggle_chat_speak(self):
        curr = self.config.settings.get("chat_speak_mode", "Speak")
        nxt = "Chat" if curr == "Speak" else "Speak"
        self.config.settings["chat_speak_mode"] = nxt
        self.config.save_settings()
        self.chat_speak_pill.set_style(text=f"VOICE: {nxt.upper()}")
        self.log("JARVIS", f"Alright {self._address()}, {nxt.lower()} mode is active.")

    def toggle_recent_tasks_overlay(self, event=None):
        self.recent_menu_visible = not self.recent_menu_visible
        self.modes.play_fx("macro_run")

    def _read_tasks_from_engine(self):
        for method_name in ["list_tasks", "get_tasks", "show_tasks", "all_tasks"]:
            fn = getattr(self.task_engine, method_name, None)
            if callable(fn):
                try:
                    out = fn()
                    if isinstance(out, str) and out.strip():
                        return out.strip()
                    if isinstance(out, (list, tuple)):
                        if not out:
                            return f"Nothing sitting on your task list right now, {self._address()}."
                        lines = []
                        for idx, item in enumerate(out, 1):
                            if isinstance(item, dict):
                                title = item.get("title") or item.get("task") or item.get("name") or str(item)
                                done = item.get("done") or item.get("completed") or (item.get("status") == "done")
                                lines.append(f"{idx}. {'[x]' if done else '[ ]'} {title}")
                            else:
                                lines.append(f"{idx}. {item}")
                        return "\n".join(lines)
                except Exception:
                    pass

        for attr_name in ["tasks", "items", "_tasks"]:
            raw = getattr(self.task_engine, attr_name, None)
            if isinstance(raw, list):
                if not raw:
                    return f"No tasks lined up right now, {self._address()}."
                lines = []
                for idx, item in enumerate(raw, 1):
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("task") or str(item)
                        done = bool(item.get("done") or item.get("completed"))
                        lines.append(f"{idx}. {'[x]' if done else '[ ]'} {title}")
                    else:
                        lines.append(f"{idx}. {item}")
                return "\n".join(lines)

        if os.path.exists("tasks.json"):
            try:
                with open("tasks.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = data.get("tasks", data) if isinstance(data, dict) else data
                if isinstance(items, list) and items:
                    lines = []
                    for idx, item in enumerate(items, 1):
                        if isinstance(item, dict):
                            t = item.get("title") or item.get("task") or str(item)
                            done = bool(item.get("done") or item.get("completed"))
                            lines.append(f"{idx}. {'[x]' if done else '[ ]'} {t}")
                        else:
                            lines.append(f"{idx}. {item}")
                    return "\n".join(lines)
                return f"Your task list is clear right now, {self._address()}."
            except Exception:
                pass

        return f"I didn't see any saved tasks yet, {self._address()}."

    def _handle_task_command(self, lower, raw_text):
        if any(k in lower for k in [
            "my tasks", "tell me my tasks", "list tasks", "show tasks",
            "what are my tasks", "read tasks", "pending tasks", "check tasks"
        ]):
            return self._read_tasks_from_engine()

        for prefix in ["add task ", "new task ", "create task ", "remind me to "]:
            if prefix in lower:
                idx = lower.index(prefix) + len(prefix)
                title = raw_text[idx:].strip()
                if not title:
                    return f"What should I put down for you, {self._address()}?"
                for fn_name in ["add_task", "create_task", "add"]:
                    fn = getattr(self.task_engine, fn_name, None)
                    if callable(fn):
                        res = fn(title)
                        return str(res) if res else f"Added '{title}' to your tasks."
                return f"Got it, added '{title}'."

        for prefix in ["complete task ", "finish task ", "mark task ", "done with "]:
            if prefix in lower:
                idx = lower.index(prefix) + len(prefix)
                target = raw_text[idx:].replace("as completed", "").replace("as done", "").strip()
                for fn_name in ["complete_task", "finish_task", "mark_done"]:
                    fn = getattr(self.task_engine, fn_name, None)
                    if callable(fn):
                        res = fn(target)
                        return str(res) if res else f"Marked '{target}' done."

        return None

    def show_telemetry(self):
        def _worker():
            status = self.system.get_system_status()
            self.root.after(0, lambda: self.log("TELEMETRY", status))
            self.speak_async(status)

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_ideology(self):
        self.log("JARVIS", f"Looking over what you've been on, {self._address()}...")

        def _worker():
            idea = self.modes.generate_ideology_idea()
            self.root.after(0, lambda: self.log("IDEA", idea))
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
        self.log("MIC", "Listening...")

        def _worker():
            try:
                text = self.listener.listen_command()
            except Exception as e:
                text = None
                self.root.after(0, lambda: self.log("JARVIS", f"Mic had an issue: {e}"))
            finally:
                self.is_listening = False
                self.root.after(0, lambda: self.mic_pill.set_style(fg="#00E5FF", border="#1C375A"))

            if text:
                spoken = str(text).strip()
                matched_mode = self._match_voice_mode(spoken)
                if matched_mode:
                    self.root.after(0, lambda: self.log(f"{self._address().upper()} (VOICE)", spoken))
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
        who = self._address().upper()
        tag = f"{who} (VOICE)" if from_voice else who
        self.log(tag, text)
        lower = text.lower().strip()

        task_reply = self._handle_task_command(lower, text)
        if task_reply is not None:
            self.log("JARVIS", task_reply)
            self.speak_async(task_reply)
            return

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

    # --- RHYTHMIC SPEECH PULSATION ENGINE ---
    def _speech_rhythm_value(self):
        """
        Produces a lively syllable/cadence wave (0.0 to 1.0) while JARVIS speaks,
        so the core visibly beats and breathes with speech rhythm.
        """
        if not self.is_speaking:
            return 0.0
        cadence = 0.5 + 0.5 * math.sin(self.speech_phase * 2.3)
        syllable = abs(math.sin(self.speech_phase * 6.4)) ** 1.6
        envelope = 0.35 + 0.65 * (0.45 * cadence + 0.55 * syllable)
        return max(0.0, min(1.0, envelope))

    def _animate(self):
        self.current_color = blend_color(self.current_color, self.target_color, 0.12)
        self.title_lbl.configure(fg=self.current_color, text=f"◈ J.A.R.V.I.S  //  {self._address().upper()}")
        self.entry.configure(insertbackground=self.current_color)

        dev_unlocked = self.config.settings.get("developer_mode_unlocked", False)
        core_style = self.config.settings.get("dev_core_style", "arc_reactor")

        if dev_unlocked and core_style == "arc_reactor":
            self.arc_build_progress = min(1.0, self.arc_build_progress + 0.035)
        else:
            self.arc_build_progress = max(0.0, self.arc_build_progress - 0.05)

        rhythm = self._speech_rhythm_value()

        self.angle += 0.020 + 0.048 * rhythm
        self.pulse_phase += 0.08 + 0.32 * rhythm
        self.speech_phase += 0.16 if self.is_speaking else 0.02
        self.explode_cycle = 0.5 - 0.5 * math.cos(self.angle * 0.85)

        self.canvas.delete("all")
        w = max(200, self.canvas.winfo_width())
        h = max(200, self.canvas.winfo_height())
        cx, cy = w / 2, h / 2

        idle_breath = 0.5 + 0.5 * math.sin(self.pulse_phase)
        if self.is_speaking:
            # Strong rhythmic beat with every syllable wave
            pulse_scale = 0.96 + 0.24 * rhythm
        else:
            pulse_scale = 0.99 + 0.03 * idle_breath

        base_r = min(w, h) * 0.23 * pulse_scale

        self._draw_hud_overlay(cx, cy, min(w, h) * 0.34, w, h, rhythm)

        if self.arc_build_progress > 0.05:
            self._draw_3d_arc_reactor(cx, cy, base_r * 1.12, self.arc_build_progress, rhythm)
        else:
            self._draw_constellation_sphere(cx, cy, base_r, rhythm)

        if self.recent_menu_visible:
            self._draw_recent_tasks_network(cx, cy, base_r)

        self.root.after(25, self._animate)

    def _draw_hud_overlay(self, cx, cy, outer_r, w, h, rhythm):
        dim_ring = blend_color("#060911", self.current_color, 0.24 + 0.32 * rhythm)
        bright_ring = blend_color("#060911", self.current_color, 0.58 + 0.42 * rhythm)

        if self.config.settings.get("show_reticle", True):
            r_ring = outer_r * (1.0 + 0.06 * rhythm)
            self.canvas.create_oval(
                cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring,
                outline=dim_ring, width=1 + (2.0 * rhythm)
            )
            # Expanding shockwave pulse ring during speech
            if rhythm > 0.05:
                wave_r = outer_r * (0.85 + 0.30 * rhythm)
                wave_col = blend_color("#060911", self.current_color, 0.75 * rhythm)
                self.canvas.create_oval(
                    cx - wave_r, cy - wave_r, cx + wave_r, cy + wave_r,
                    outline=wave_col, width=2
                )

            for seg in range(4):
                start_deg = math.degrees(self.angle * 0.7) + seg * 90
                self.canvas.create_arc(
                    cx - r_ring * 0.95, cy - r_ring * 0.95,
                    cx + r_ring * 0.95, cy + r_ring * 0.95,
                    start=start_deg, extent=30 + 18 * rhythm, style=tk.ARC,
                    outline=bright_ring, width=2 + (2.0 * rhythm)
                )

        if self.config.settings.get("show_brackets", True):
            b = 16
            pad = 22
            for x0, y0, dx, dy in [
                (pad, pad, b, b),
                (w - pad, pad, -b, b),
                (pad, h - pad, b, -b),
                (w - pad, h - pad, -b, -b),
            ]:
                self.canvas.create_line(x0, y0, x0 + dx, y0, fill=dim_ring, width=2)
                self.canvas.create_line(x0, y0, x0, y0 + dy, fill=dim_ring, width=2)

    def _draw_constellation_sphere(self, cx, cy, r, rhythm):
        projected = []
        for x, y, z in self.sphere_points:
            xr, yr, zr = rotate_3d(x, y, z, self.angle * 0.5, self.angle, 0.0)
            scale = 2.4 / (2.4 - zr)
            sx = cx + xr * r * scale
            sy = cy + yr * r * scale
            projected.append((sx, sy, zr))

        line_col = blend_color("#060911", self.current_color, 0.34 + 0.45 * rhythm)
        n = len(projected)
        max_dist_sq = (r * (0.50 + 0.08 * rhythm)) ** 2
        for i in range(n):
            x1, y1, z1 = projected[i]
            if z1 < -0.35:
                continue
            for j in range(i + 1, n):
                x2, y2, z2 = projected[j]
                if z2 < -0.35:
                    continue
                if (x1 - x2) ** 2 + (y1 - y2) ** 2 < max_dist_sq:
                    self.canvas.create_line(x1, y1, x2, y2, fill=line_col, width=1 + rhythm)

        for sx, sy, z in projected:
            depth = (z + 1.0) / 2.0
            dot_col = blend_color("#0A1220", self.current_color, 0.25 + 0.75 * depth)
            if rhythm > 0:
                dot_col = blend_color(dot_col, "#FFFFFF", 0.55 * rhythm)
            rad = (1.6 + 2.4 * depth) * (1.0 + 0.55 * rhythm)
            self.canvas.create_oval(sx - rad, sy - rad, sx + rad, sy + rad, fill=dot_col, outline="")

    def _proj_3d(self, cx, cy, r, x, y, z, tilt_x=0.52, yaw=0.0):
        xr, yr, zr = rotate_3d(x, y, z, tilt_x, yaw, 0.0)
        fov = 3.2
        persp = fov / max(0.8, fov - zr)
        return cx + xr * r * persp, cy + yr * r * persp, zr

    def _draw_3d_arc_reactor(self, cx, cy, r, assembly_p, rhythm):
        tilt_x = 0.58 + 0.14 * math.sin(self.angle * 0.6)
        yaw = self.angle * 0.85
        explode_cfg = float(self.config.settings.get("dev_explode_amount", 0.45))
        # Rhythm nudges the coils and core outward in sync with speech
        sep = (1.0 - assembly_p) * 0.65 + self.explode_cycle * explode_cfg + 0.14 * rhythm

        segs = 24
        ring_rad = 0.95 + sep * 0.12
        for i in range(segs):
            a0 = (2 * math.pi * i) / segs
            a1 = (2 * math.pi * (i + 1)) / segs
            x0, y0, _ = self._proj_3d(cx, cy, r, math.cos(a0) * ring_rad, math.sin(a0) * ring_rad, -0.06 * sep, tilt_x, yaw)
            x1, y1, _ = self._proj_3d(cx, cy, r, math.cos(a1) * ring_rad, math.sin(a1) * ring_rad, -0.06 * sep, tilt_x, yaw)
            fx0, fy0, fz0 = self._proj_3d(cx, cy, r, math.cos(a0) * ring_rad, math.sin(a0) * ring_rad, 0.06 * sep, tilt_x, yaw)
            fx1, fy1, fz1 = self._proj_3d(cx, cy, r, math.cos(a1) * ring_rad, math.sin(a1) * ring_rad, 0.06 * sep, tilt_x, yaw)

            depth = ((fz0 + fz1) * 0.5 + 1.0) * 0.5
            metal_col = blend_color("#1E293B", "#94A3B8", depth)
            self.canvas.create_line(x0, y0, x1, y1, fill="#0F172A", width=5)
            self.canvas.create_line(fx0, fy0, fx1, fy1, fill=metal_col, width=5)

        coil_count = 10
        coils_3d = []
        for i in range(coil_count):
            ang = (2 * math.pi * i) / coil_count
            radial_dist = 0.72 + sep * 0.34
            z_offset = (0.14 if i % 2 == 0 else -0.14) * (1.0 + sep * 1.4)

            bx = math.cos(ang) * radial_dist
            by = math.sin(ang) * radial_dist
            perp_x, perp_y = -math.sin(ang) * 0.09, math.cos(ang) * 0.09
            rad_x, rad_y = math.cos(ang) * 0.11, math.sin(ang) * 0.11
            dz = 0.07

            corners = [
                (bx - perp_x - rad_x, by - perp_y - rad_y, z_offset - dz),
                (bx + perp_x - rad_x, by + perp_y - rad_y, z_offset - dz),
                (bx + perp_x + rad_x, by + perp_y + rad_y, z_offset - dz),
                (bx - perp_x + rad_x, by - perp_y + rad_y, z_offset - dz),
                (bx - perp_x - rad_x, by - perp_y - rad_y, z_offset + dz),
                (bx + perp_x - rad_x, by + perp_y - rad_y, z_offset + dz),
                (bx + perp_x + rad_x, by + perp_y + rad_y, z_offset + dz),
                (bx - perp_x + rad_x, by - perp_y + rad_y, z_offset + dz),
            ]
            proj_c = [self._proj_3d(cx, cy, r, px, py, pz, tilt_x, yaw) for (px, py, pz) in corners]
            avg_z = sum(pt[2] for pt in proj_c) / len(proj_c)
            coils_3d.append((avg_z, proj_c))

        coils_3d.sort(key=lambda item: item[0])
        for avg_z, pc in coils_3d:
            depth = (avg_z + 1.0) * 0.5
            copper_fill = blend_color("#5C2D16", "#E08E55", depth)
            edge_col = blend_color("#273549", self.current_color, 0.35 + 0.5 * depth + 0.35 * rhythm)
            front_poly = [coord for pt in pc[4:8] for coord in (pt[0], pt[1])]
            self.canvas.create_polygon(front_poly, fill=copper_fill, outline=edge_col, width=1 + rhythm)
            for k in range(4):
                self.canvas.create_line(pc[k][0], pc[k][1], pc[k + 4][0], pc[k + 4][1], fill=edge_col, width=1)

        inner_z = 0.05 + sep * 0.25
        inner_r = 0.46 * (1.0 + 0.08 * rhythm)
        inner_pts = []
        for s in range(24):
            a = (2 * math.pi * s) / 24
            inner_pts.append(self._proj_3d(cx, cy, r, math.cos(a) * inner_r, math.sin(a) * inner_r, inner_z, tilt_x, yaw))
        for s in range(24):
            p0 = inner_pts[s]
            p1 = inner_pts[(s + 1) % 24]
            self.canvas.create_line(p0[0], p0[1], p1[0], p1[1], fill=self.current_color, width=2 + 1.5 * rhythm)

        for f in range(6):
            a = (2 * math.pi * f) / 6 + self.angle * 0.4
            sx0, sy0, _ = self._proj_3d(cx, cy, r, math.cos(a) * 0.22, math.sin(a) * 0.22, inner_z, tilt_x, yaw)
            sx1, sy1, _ = self._proj_3d(cx, cy, r, math.cos(a) * inner_r, math.sin(a) * inner_r, inner_z, tilt_x, yaw)
            self.canvas.create_line(sx0, sy0, sx1, sy1, fill="#CBD5E1", width=2)

        core_z = 0.08 + sep * 0.38
        ccx, ccy, _ = self._proj_3d(cx, cy, r, 0.0, 0.0, core_z, tilt_x, yaw)
        core_rad = r * 0.16 * (1.0 + 0.38 * rhythm)
        halo_rad = core_rad * (1.45 + 0.55 * rhythm)
        glow_col = blend_color(self.current_color, "#FFFFFF", min(0.95, 0.55 + 0.4 * rhythm))
        self.canvas.create_oval(
            ccx - halo_rad, ccy - halo_rad,
            ccx + halo_rad, ccy + halo_rad,
            outline=glow_col, width=2 + 2.0 * rhythm
        )
        self.canvas.create_oval(
            ccx - core_rad, ccy - core_rad,
            ccx + core_rad, ccy + core_rad,
            fill=glow_col, outline="#FFFFFF", width=2
        )
        self.canvas.create_text(
            cx, cy + r + 24, text="3D REACTOR ASSEMBLY",
            fill=self.current_color, font=("Segoe UI", 8, "bold")
        )

    def _draw_recent_tasks_network(self, cx, cy, r):
        recent = self.config.memory.get("recent_activities", [])[:3]
        if not recent:
            recent = ["No recent activity logged yet."]

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

            card_w, card_h = 200, 42
            self.canvas.create_rectangle(
                bx - card_w / 2, by - card_h / 2, bx + card_w / 2, by + card_h / 2,
                fill="#0A1220", outline=self.current_color, width=1
            )
            short_txt = item if len(item) <= 28 else item[:25] + "..."
            self.canvas.create_text(bx, by, text=short_txt, fill="#F1F5F9", font=("Segoe UI", 8))

    def open_settings(self):
        if self.settings_win is not None and self.settings_win.winfo_exists():
            self.settings_win.lift()
            return

        bg_main = "#080D18"
        bg_card = "#0E1728"
        win = tk.Toplevel(self.root)
        self.settings_win = win
        win.title("Settings")
        win.geometry("680x700")
        win.configure(bg=bg_main)
        apply_dark_title_bar(win)

        nav_bar = tk.Frame(win, bg="#060A13", padx=16, pady=12)
        nav_bar.pack(fill=tk.X)

        content_area = tk.Frame(win, bg=bg_main, padx=22, pady=16)
        content_area.pack(fill=tk.BOTH, expand=True)

        pages = {}
        nav_pills = {}

        def show_page(page_key):
            for k, frame in pages.items():
                frame.pack_forget()
                nav_pills[k].set_style(fg="#94A3B8", border="#182740", active=False)
            pages[page_key].pack(fill=tk.BOTH, expand=True)
            nav_pills[page_key].set_style(fg="#05080F", border=self.current_color, active=True, active_bg=self.current_color)

        for key, label in [
            ("personal", "PERSONAL"),
            ("modes", "MODE SETTINGS"),
            ("keywords", "KEYWORDS"),
            ("developer", "DEVELOPER"),
        ]:
            pill = HudPillButton(
                nav_bar, text=label, command=lambda k=key: show_page(k),
                width=136, height=30, bg=bg_card, fg="#94A3B8", border="#182740",
                font=("Segoe UI", 8, "bold"), parent_bg="#060A13"
            )
            pill.pack(side=tk.LEFT, padx=(0, 8))
            nav_pills[key] = pill
            pages[key] = tk.Frame(content_area, bg=bg_main)

        def styled_label(parent, text, top_pad=10):
            tk.Label(parent, text=text, bg=bg_main, fg="#CBD5E1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(top_pad, 4))

        def styled_entry(parent, var, show=None):
            e = tk.Entry(
                parent, textvariable=var, show=show or "", bg=bg_card, fg="#F8FAFC",
                insertbackground=self.current_color, relief=tk.FLAT, bd=0, font=("Segoe UI", 10)
            )
            e.pack(fill=tk.X, ipady=7, padx=1)
            return e

        p_me = pages["personal"]
        styled_label(p_me, "How may I address you?", top_pad=0)
        addr_var = tk.StringVar(value=self._address())
        styled_entry(p_me, addr_var)

        styled_label(p_me, "How should I talk and act with you?")
        persona_var = tk.StringVar(value=self.config.settings["intro_tweak"].get("persona_tone", ""))
        styled_entry(p_me, persona_var)

        styled_label(p_me, "Local Model Tag:")
        model_var = tk.StringVar(value=self.config.settings.get("ollama_model", "qwen2.5:3b"))
        styled_entry(p_me, model_var)

        tk.Frame(p_me, bg=bg_main, height=10).pack()
        t_intro = ModernToggleRow(p_me, "Remember & greet with last session context", self.config.settings["intro_tweak"].get("enabled", True), self.current_color)
        t_intro.pack(fill=tk.X)
        t_ideo = ModernToggleRow(p_me, "Proactive next-step ideas (Ideology)", self.config.settings["ideology"].get("enabled", True), self.current_color)
        t_ideo.pack(fill=tk.X)
        t_sfx = ModernToggleRow(p_me, "Sound cues on mode & action events", self.config.settings.get("sound_effects", True), self.current_color)
        t_sfx.pack(fill=tk.X)
        t_ret = ModernToggleRow(p_me, "Outer HUD reticle ring", self.config.settings.get("show_reticle", True), self.current_color)
        t_ret.pack(fill=tk.X)
        t_brk = ModernToggleRow(p_me, "Corner frame brackets", self.config.settings.get("show_brackets", True), self.current_color)
        t_brk.pack(fill=tk.X)
        t_mic = ModernToggleRow(p_me, "Listen again automatically after speaking", self.config.settings.get("auto_listen_after_reply", False), self.current_color)
        t_mic.pack(fill=tk.X)

        def save_personal():
            s = self.config.settings
            s["address_as"] = addr_var.get().strip() or "Boss"
            s["intro_tweak"]["persona_tone"] = persona_var.get().strip()
            s["intro_tweak"]["enabled"] = t_intro.get()
            s["ideology"]["enabled"] = t_ideo.get()
            s["sound_effects"] = t_sfx.get()
            s["show_reticle"] = t_ret.get()
            s["show_brackets"] = t_brk.get()
            s["auto_listen_after_reply"] = t_mic.get()
            chosen_m = model_var.get().strip() or "qwen2.5:3b"
            s["ollama_model"] = chosen_m
            self.brain.model = chosen_m
            self.config.save_settings()
            self._refresh_mode_pills()
            messagebox.showinfo("Saved", f"Got it, {self._address()}. Preferences saved.", parent=win)

        HudPillButton(
            p_me, text="SAVE PREFERENCES", command=save_personal,
            width=185, height=34, bg="#0D2440", fg="#38BDF8", border="#1C4B7D",
            font=("Segoe UI", 8, "bold"), parent_bg=bg_main
        ).pack(anchor="w", pady=(16, 0))

        p_modes = pages["modes"]
        styled_label(p_modes, "Select Mode to Edit (editing here does NOT switch your active mode):", top_pad=0)

        mode_selector_row = tk.Frame(p_modes, bg=bg_main)
        mode_selector_row.pack(fill=tk.X, pady=(2, 12))

        selected_edit_mode = {"name": self.config.settings.get("active_mode", "Normal")}
        sub_mode_pills = {}

        color_var = tk.StringVar()
        apps_var = tk.StringVar()
        game_exe_var = tk.StringVar()
        batla_quote_var = tk.StringVar(value=self.config.settings.get("batla_quote", "JA CHAT SEY KOUD JA"))

        gaming_card = tk.Frame(p_modes, bg=bg_main)
        styled_label(gaming_card, "Game Executable (.exe) for Gaming Mode:", top_pad=0)
        exe_row = tk.Frame(gaming_card, bg=bg_main)
        exe_row.pack(fill=tk.X, pady=(0, 8))
        tk.Entry(
            exe_row, textvariable=game_exe_var, bg=bg_card, fg="#F8FAFC",
            insertbackground="#FF7A00", relief=tk.FLAT, bd=0, font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=7, padx=(0, 8))

        def pick_exe():
            p = filedialog.askopenfilename(
                parent=win,
                title="Select Game Executable",
                filetypes=[("Executable (*.exe)", "*.exe"), ("All Files", "*.*")]
            )
            if p:
                game_exe_var.set(p)

        HudPillButton(
            exe_row, text="BROWSE .EXE", command=pick_exe,
            width=110, height=30, bg="#0E1B30", fg="#00E5FF", border="#1F3D66",
            font=("Segoe UI", 8, "bold"), parent_bg=bg_main
        ).pack(side=tk.RIGHT)

        t_vram = ModernToggleRow(gaming_card, "Free GPU VRAM when entering Gaming Mode", True, "#FF7A00")
        t_vram.pack(fill=tk.X, pady=(0, 6))

        batla_card = tk.Frame(p_modes, bg=bg_main)
        styled_label(batla_card, "Batla Mode Unlock Phrase:", top_pad=0)
        styled_entry(batla_card, batla_quote_var)

        shared_card = tk.Frame(p_modes, bg=bg_main)
        shared_card.pack(fill=tk.X)
        styled_label(shared_card, "Mode Accent Color (Hex):", top_pad=4)
        styled_entry(shared_card, color_var)
        styled_label(shared_card, "Apps to Launch in This Mode (comma-separated):")
        styled_entry(shared_card, apps_var)

        def load_mode_into_form(m_name):
            selected_edit_mode["name"] = m_name
            cfg = self.config.settings["modes"][m_name]
            m_col = cfg.get("color", "#00E5FF")

            for name, p in sub_mode_pills.items():
                if name == m_name:
                    p.set_style(fg="#05080F", border=m_col, active=True, active_bg=m_col)
                else:
                    p.set_style(fg="#94A3B8", border="#182740", active=False)

            color_var.set(m_col)
            apps_var.set(", ".join(cfg.get("apps", [])))

            gaming_card.pack_forget()
            batla_card.pack_forget()
            if m_name == "Gaming":
                gaming_card.pack(fill=tk.X, before=shared_card, pady=(0, 6))
                game_exe_var.set(cfg.get("current_game", ""))
                t_vram.set(cfg.get("unload_vram", True))
            elif m_name == "Batla":
                batla_card.pack(fill=tk.X, before=shared_card, pady=(0, 6))
                batla_quote_var.set(self.config.settings.get("batla_quote", "JA CHAT SEY KOUD JA"))

        for m_name in ["Normal", "Gaming", "Productivity", "Batla"]:
            sp = HudPillButton(
                mode_selector_row, text=m_name.upper(),
                command=lambda n=m_name: load_mode_into_form(n),
                width=125, height=30, bg=bg_card, fg="#94A3B8", border="#182740",
                font=("Segoe UI", 8, "bold"), parent_bg=bg_main
            )
            sp.pack(side=tk.LEFT, padx=(0, 8))
            sub_mode_pills[m_name] = sp

        load_mode_into_form(selected_edit_mode["name"])

        def save_mode_only():
            m = selected_edit_mode["name"]
            m_cfg = self.config.settings["modes"][m]
            m_cfg["color"] = color_var.get().strip() or "#00E5FF"
            m_cfg["apps"] = [a.strip() for a in apps_var.get().split(",") if a.strip()]
            if m == "Gaming":
                m_cfg["current_game"] = game_exe_var.get().strip()
                m_cfg["unload_vram"] = t_vram.get()
            elif m == "Batla":
                self.config.settings["batla_quote"] = batla_quote_var.get().strip() or "JA CHAT SEY KOUD JA"

            self.config.save_settings()
            if self.config.settings.get("active_mode") == m:
                self.target_color = m_cfg["color"]
                self._refresh_mode_pills()
            load_mode_into_form(m)
            messagebox.showinfo("Saved", f"Saved {m} mode settings.", parent=win)

        HudPillButton(
            p_modes, text="SAVE MODE SETTINGS", command=save_mode_only,
            width=185, height=34, bg="#0D2440", fg="#38BDF8", border="#1C4B7D",
            font=("Segoe UI", 8, "bold"), parent_bg=bg_main
        ).pack(anchor="w", pady=(16, 0))

        p_kw = pages["keywords"]
        styled_label(p_kw, "Trigger Phrase:", top_pad=0)
        kw_trig = tk.StringVar()
        styled_entry(p_kw, kw_trig)

        styled_label(p_kw, "Apps / Paths (comma-separated):")
        kw_apps = tk.StringVar()
        styled_entry(p_kw, kw_apps)

        kw_listbox = tk.Listbox(
            p_kw, bg=bg_card, fg="#E6EDF7", selectbackground="#183153",
            relief=tk.FLAT, bd=0, height=9, font=("Segoe UI", 9)
        )
        kw_listbox.pack(fill=tk.X, pady=(12, 8))

        def refresh_kw():
            kw_listbox.delete(0, tk.END)
            for k, v in self.config.settings.get("custom_keywords", {}).items():
                kw_listbox.insert(tk.END, f"{k}  ->  {', '.join(v)}")

        refresh_kw()

        def add_kw():
            t = kw_trig.get().strip().lower()
            a = [x.strip() for x in kw_apps.get().split(",") if x.strip()]
            if t and a:
                self.config.settings.setdefault("custom_keywords", {})[t] = a
                self.config.save_settings()
                kw_trig.set("")
                kw_apps.set("")
                refresh_kw()

        def del_kw():
            sel = kw_listbox.curselection()
            if not sel:
                return
            key = kw_listbox.get(sel[0]).split("  ->  ", 1)[0]
            self.config.settings.get("custom_keywords", {}).pop(key, None)
            self.config.save_settings()
            refresh_kw()

        kw_bar = tk.Frame(p_kw, bg=bg_main)
        kw_bar.pack(fill=tk.X, pady=6)
        HudPillButton(kw_bar, text="+ ADD MACRO", command=add_kw, width=125, height=30, bg="#0D2440", fg="#38BDF8", border="#1C4B7D", font=("Segoe UI", 8, "bold"), parent_bg=bg_main).pack(side=tk.LEFT, padx=(0, 8))
        HudPillButton(kw_bar, text="REMOVE", command=del_kw, width=110, height=30, bg="#261018", fg="#FDA4AF", border="#5C1D33", font=("Segoe UI", 8, "bold"), parent_bg=bg_main).pack(side=tk.LEFT)

        p_dev = pages["developer"]
        styled_label(p_dev, "Developer Access Code:", top_pad=0)
        code_var = tk.StringVar()
        styled_entry(p_dev, code_var, show="*")

        dev_box = tk.Frame(p_dev, bg=bg_main)

        def render_dev():
            for w in dev_box.winfo_children():
                w.destroy()
            if not self.config.settings.get("developer_mode_unlocked", False):
                tk.Label(dev_box, text="Locked. Enter code to access 3D reactor controls.", bg=bg_main, fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=10)
                return

            tk.Label(dev_box, text="DEVELOPER OVERRIDE ACTIVE", bg=bg_main, fg="#00FF9D", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 10))
            core_var = tk.StringVar(value=self.config.settings.get("dev_core_style", "arc_reactor"))

            core_row = tk.Frame(dev_box, bg=bg_main)
            core_row.pack(fill=tk.X, pady=(0, 10))
            p_arc = HudPillButton(core_row, text="3D ARC REACTOR", command=lambda: set_core("arc_reactor"), width=155, height=30, bg=bg_card, fg="#94A3B8", border="#182740", font=("Segoe UI", 8, "bold"), parent_bg=bg_main)
            p_arc.pack(side=tk.LEFT, padx=(0, 8))
            p_sph = HudPillButton(core_row, text="3D NODE SPHERE", command=lambda: set_core("constellation"), width=155, height=30, bg=bg_card, fg="#94A3B8", border="#182740", font=("Segoe UI", 8, "bold"), parent_bg=bg_main)
            p_sph.pack(side=tk.LEFT)

            def set_core(val):
                core_var.set(val)
                p_arc.set_style(fg="#05080F" if val == "arc_reactor" else "#94A3B8", border="#00FF9D" if val == "arc_reactor" else "#182740", active=(val == "arc_reactor"), active_bg="#00FF9D")
                p_sph.set_style(fg="#05080F" if val == "constellation" else "#94A3B8", border="#00FF9D" if val == "constellation" else "#182740", active=(val == "constellation"), active_bg="#00FF9D")

            set_core(core_var.get())

            styled_label(dev_box, "3D Part Separation Travel (0.0 to 1.0):")
            explode_var = tk.DoubleVar(value=self.config.settings.get("dev_explode_amount", 0.45))
            tk.Scale(
                dev_box, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, variable=explode_var,
                bg=bg_main, fg="#E2E8F0", troughcolor=bg_card, highlightthickness=0, bd=0, activebackground="#00FF9D"
            ).pack(fill=tk.X)

            styled_label(dev_box, "Sphere Node Count (30 to 150):")
            dots_var = tk.IntVar(value=self.config.settings.get("dev_dot_count", 84))
            tk.Scale(
                dev_box, from_=30, to=150, orient=tk.HORIZONTAL, variable=dots_var,
                bg=bg_main, fg="#E2E8F0", troughcolor=bg_card, highlightthickness=0, bd=0, activebackground="#00FF9D"
            ).pack(fill=tk.X)

            def apply_dev():
                self.config.settings["dev_core_style"] = core_var.get()
                self.config.settings["dev_explode_amount"] = round(float(explode_var.get()), 2)
                self.config.settings["dev_dot_count"] = int(dots_var.get())
                self.sphere_points = self._generate_sphere_points(int(dots_var.get()))
                self.config.save_settings()
                self.modes.play_fx("arc_assemble")

            HudPillButton(
                dev_box, text="APPLY CORE TWEAKS", command=apply_dev,
                width=185, height=32, bg="#0B2E22", fg="#00FF9D", border="#1B664B",
                font=("Segoe UI", 8, "bold"), parent_bg=bg_main
            ).pack(anchor="w", pady=(14, 0))

        def unlock_dev():
            secret = self.config.settings.get("developer_secret_code", "STARK-DEV")
            if code_var.get().strip() == secret:
                self.config.settings["developer_mode_unlocked"] = True
                self.config.save_settings()
                self.modes.play_fx("arc_assemble")
                render_dev()
            else:
                messagebox.showerror("Denied", "Incorrect code.", parent=win)

        HudPillButton(
            p_dev, text="UNLOCK", command=unlock_dev,
            width=120, height=30, bg="#0E1B30", fg="#00E5FF", border="#1F3D66",
            font=("Segoe UI", 8, "bold"), parent_bg=bg_main
        ).pack(anchor="w", pady=(10, 0))
        dev_box.pack(fill=tk.BOTH, expand=True, pady=10)
        render_dev()

        start_tab = "modes" if self.config.settings.get("active_mode") == "Gaming" else "personal"
        show_page(start_tab)


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
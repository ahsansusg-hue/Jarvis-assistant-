import os
import subprocess
import threading
import time

try:
    import winsound
except ImportError:
    winsound = None


class JarvisModeEngine:
    def __init__(self, config, system, brain):
        self.config = config
        self.system = system
        self.brain = brain

    def launch_target(self, target):
        target = (target or "").strip().strip('"')
        if not target:
            return ""
        if os.path.isfile(target) and target.lower().endswith(".exe"):
            try:
                cwd = os.path.dirname(target) or None
                subprocess.Popen([target], cwd=cwd, shell=False)
                return f"Launched {os.path.basename(target)}"
            except Exception as e:
                return f"Failed to launch {os.path.basename(target)}: {e}"
        return self.system.open_app(target)

    def play_fx(self, fx_type="mode_switch"):
        if not self.config.settings.get("sound_effects", True) or winsound is None:
            return

        def _worker():
            try:
                if fx_type == "mode_switch":
                    seq = [(420, 45), (680, 50), (1040, 75)]
                elif fx_type == "arc_assemble":
                    seq = [(260, 40), (390, 40), (520, 45), (780, 55), (1240, 90)]
                elif fx_type == "batla_lock":
                    seq = [(310, 80), (210, 120)]
                else:
                    seq = [(580, 40), (880, 60)]

                for freq, dur in seq:
                    winsound.Beep(freq, dur)
                    if fx_type == "arc_assemble":
                        time.sleep(0.02)
            except Exception:
                try:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def activate_mode(self, mode_name):
        modes = self.config.settings.get("modes", {})
        matched = None
        for key in modes:
            if key.lower() == mode_name.lower():
                matched = key
                break

        if not matched:
            return f"Mode '{mode_name}' not found, Boss."

        self.config.settings["active_mode"] = matched
        self.config.save_settings()
        mode_cfg = modes[matched]

        self.play_fx("arc_assemble" if matched == "Developer" else "mode_switch")
        actions_taken = [f"{matched} Mode engaged"]

        if matched == "Gaming":
            if mode_cfg.get("unload_vram", True) and hasattr(self.brain, "unload_model"):
                actions_taken.append(self.brain.unload_model())
            game = mode_cfg.get("current_game", "").strip()
            if game:
                actions_taken.append(self.launch_target(game))

        for app in mode_cfg.get("apps", []):
            if app.strip():
                actions_taken.append(self.launch_target(app.strip()))

        self.config.record_activity(f"Switched to {matched} Mode")
        return " | ".join(actions_taken)

    def check_custom_keyword(self, user_text):
        lower = user_text.lower().strip()
        keywords = self.config.settings.get("custom_keywords", {})
        for trigger, apps in keywords.items():
            if trigger.lower() in lower:
                self.play_fx("macro_run")
                launched = [self.launch_target(app) for app in apps if app.strip()]
                self.config.record_activity(f"Triggered keyword '{trigger}'")
                if launched:
                    return f"Executing '{trigger}': " + ", ".join(launched)
                return f"Keyword '{trigger}' triggered, Boss (no apps assigned yet)."
        return None

    def is_complex_query(self, text):
        words = text.strip().split()
        complex_markers = [
            "why", "how", "explain", "code", "error", "debug", "build",
            "algorithm", "difference", "compare", "design", "optimize", "write"
        ]
        lower = text.lower()
        return len(words) >= 6 or any(m in lower for m in complex_markers)

    def process_query(self, user_text):
        macro_res = self.check_custom_keyword(user_text)
        if macro_res:
            return macro_res

        active_mode = self.config.settings.get("active_mode", "Normal")
        mode_cfg = self.config.settings["modes"].get(active_mode, {})

        if active_mode == "Batla":
            required_quote = self.config.settings.get("batla_quote", "JA CHAT SEY KOUD JA").strip()
            if self.is_complex_query(user_text) and required_quote.lower() not in user_text.lower():
                self.play_fx("batla_lock")
                return (
                    f"Acha ji? Baray complex sawal poochay ja rahay hain! "
                    f"Pehle magic words bolo ('{required_quote}'), phir milega asli jawab!"
                )
            cleaned = user_text.replace(required_quote, "").replace(required_quote.lower(), "").strip()
            user_text = cleaned or user_text

        context_notes = []
        if self.config.settings.get("intro_tweak", {}).get("enabled", True):
            tone = self.config.settings["intro_tweak"].get("persona_tone", "")
            if tone:
                context_notes.append(f"Persona: {tone}.")

        if self.config.settings.get("ideology", {}).get("enabled", True):
            last_work = self.config.memory.get("last_work", "")
            if last_work:
                context_notes.append(f"User's current/recent focus: {last_work}.")

        modifier = mode_cfg.get("prompt_modifier", "")
        if modifier:
            context_notes.append(f"Mode instruction ({active_mode}): {modifier}")

        enriched_prompt = f"[System Context: {' '.join(context_notes)}]\nUser: {user_text}"
        self.config.record_activity(user_text[:65])
        return self.brain.think(enriched_prompt)

    def generate_ideology_idea(self):
        last_work = self.config.memory.get("last_work", "Python & JARVIS development")
        recent = ", ".join(self.config.memory.get("recent_activities", [])[:3])
        prompt = (
            f"Based on my recent work ({last_work}; recent history: {recent}), "
            f"suggest ONE sharp, high-impact next step or feature idea in 2 concise sentences."
        )
        return self.brain.think(prompt)
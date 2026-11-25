import json
import os
from datetime import datetime

SETTINGS_FILE = "jarvis_settings.json"
MEMORY_FILE = "jarvis_memory.json"

DEFAULT_SETTINGS = {
    "address_as": "Boss",
    "active_mode": "Normal",
    "chat_speak_mode": "Speak",
    "sound_effects": True,
    "show_reticle": True,
    "show_brackets": True,
    "auto_listen_after_reply": False,
    "ollama_model": "qwen2.5:3b",
    "developer_mode_unlocked": False,
    "developer_secret_code": "DEV_BLOCK",
    "dev_ui_theme": "default_sphere",
    "dev_dot_count": 84,
    "dev_pulse_intensity": 1.35,
    "dev_explode_amount": 0.65,
    "batla_quote": "JA CHAT SEY KOUD JA",
    "intro_tweak": {
        "enabled": True,
        "persona_tone": "Sharp, grounded, witty companion with real engineering instincts",
        "welcome_template": "Good to have you back, {address}. Last time we were on: {last_work}.",
    },
    "ideology": {
        "enabled": True,
        "proactive_ideas": True,
    },
    "modes": {
        "Normal": {
            "color": "#00E5FF",
            "apps": [],
            "prompt_modifier": "Be direct, sharp, and natural like a trusted human partner.",
        },
        "Gaming": {
            "color": "#FF7A00",
            "apps": [],
            "current_game": "",
            "unload_vram": True,
            "prompt_modifier": "Keep replies quick and punchy so the user stays in the game.",
        },
        "Productivity": {
            "color": "#00FF9D",
            "apps": ["code"],
            "prompt_modifier": "Stay structured, practical, and focused on getting real work done fast.",
        },
        "Batla": {
            "color": "#B829FF",
            "apps": [],
            "prompt_modifier": "Playful, dramatic gatekeeper energy.",
        },
    },
    "custom_keywords": {
        "set up workplace": ["code"],
    },
}

DEFAULT_MEMORY = {
    "last_work": "Custom Developer UI/UX Themes",
    "recent_activities": [
        "Added 4 interactive Developer UI/UX HUD themes",
        "Secured Developer Mode with custom access key",
        "Connected task engine to voice and text commands",
    ],
    "notes": [],
}


class JarvisConfig:
    def __init__(self):
        self.settings = self._load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        # Always enforce the updated developer secret key
        self.settings["developer_secret_code"] = "DEV_BLOCK"
        self.memory = self._load_json(MEMORY_FILE, DEFAULT_MEMORY)

    def _load_json(self, path, defaults):
        if not os.path.exists(path):
            self._save_json(path, defaults)
            return json.loads(json.dumps(defaults))
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = json.loads(json.dumps(defaults))
            self._deep_update(merged, data)
            return merged
        except Exception:
            return json.loads(json.dumps(defaults))

    def _deep_update(self, base, override):
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def _save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save_settings(self):
        self._save_json(SETTINGS_FILE, self.settings)

    def save_memory(self):
        self._save_json(MEMORY_FILE, self.memory)

    def record_activity(self, summary):
        summary = (summary or "").strip()
        if not summary:
            return
        self.memory["last_work"] = summary
        stamp = datetime.now().strftime("%H:%M")
        entry = f"[{stamp}] {summary}"
        recent = self.memory.setdefault("recent_activities", [])
        recent.insert(0, entry)
        self.memory["recent_activities"] = recent[:15]
        self.save_memory()
import json
import os
from datetime import datetime

SETTINGS_FILE = "jarvis_settings.json"
MEMORY_FILE = "jarvis_memory.json"

DEFAULT_SETTINGS = {
    "active_mode": "Normal",
    "chat_speak_mode": "Speak",  # "Speak" or "Chat"
    "sound_effects": True,
    "developer_mode_unlocked": False,
    "developer_secret_code": "STARK-DEV",
    "dev_core_style": "arc_reactor",  # "arc_reactor" or "constellation"
    "dev_dot_count": 84,
    "dev_pulse_intensity": 1.35,
    "batla_quote": "JA CHAT SEY KOUD JA",
    "intro_tweak": {
        "enabled": True,
        "persona_tone": "Sharp, witty, loyal engineering companion",
        "welcome_template": "Welcome back, Boss. Last session we worked on: {last_work}.",
    },
    "ideology": {
        "enabled": True,
        "proactive_ideas": True,
    },
    "modes": {
        "Normal": {
            "color": "#00E5FF",
            "apps": [],
            "prompt_modifier": "Respond clearly, concisely, and helpfully.",
        },
        "Gaming": {
            "color": "#FF7A00",
            "apps": [],
            "current_game": "",
            "unload_vram": True,
            "prompt_modifier": "Keep responses ultra-brief so the user can focus on gaming.",
        },
        "Productivity": {
            "color": "#00FF9D",
            "apps": ["code"],
            "prompt_modifier": "Maximize precision, structure, and actionable engineering depth for productivity tasks.",
        },
        "Batla": {
            "color": "#B829FF",
            "apps": [],
            "prompt_modifier": "Playful cursed gatekeeper mode.",
        },
    },
    "custom_keywords": {
        "set up workplace": ["code"],
    },
}

DEFAULT_MEMORY = {
    "last_work": "Day 10 Desktop Interface & Mode Engine",
    "recent_activities": [
        "Migrated brain to local Ollama qwen2.5:3b",
        "Built live NVIDIA T1200 VRAM & CPU telemetry",
        "Designed Day 10 HUD & modular Mode engine",
    ],
    "notes": [],
}


class JarvisConfig:
    def __init__(self):
        self.settings = self._load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
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
        summary = summary.strip()
        if not summary:
            return
        self.memory["last_work"] = summary
        stamp = datetime.now().strftime("%H:%M")
        entry = f"[{stamp}] {summary}"
        recent = self.memory.setdefault("recent_activities", [])
        recent.insert(0, entry)
        self.memory["recent_activities"] = recent[:12]
        self.save_memory()
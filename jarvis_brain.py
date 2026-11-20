import json
import urllib.error
import urllib.request


class JarvisBrain:
    """100% local LLM brain powered by Ollama (zero API keys, zero cloud quotas)."""

    def __init__(
        self,
        task_engine=None,
        model: str = "qwen2.5:3b",
        host: str = "http://localhost:11434",
        timeout: int = 45,
    ):
        self.task_engine = task_engine
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.is_active = self._check_connection()

    def _check_connection(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    print(f"[BRAIN] Local Ollama online ({self.model}).")
                    return True
        except Exception as e:
            print(f"[!] Ollama unreachable at {self.host}: {e}")
        return False

    def think(self, prompt: str) -> str:
        """Generates a response locally via Ollama."""
        if not prompt or not prompt.strip():
            return "Say that again, Boss."

        if not self.is_active and not self._check_connection():
            return "Local Ollama engine is offline, Boss. Check that the Ollama service is running."

        system_instruction = (
            "You are JARVIS, a sharp, local AI assistant built by Ahsan Iqbal. "
            "Address the user strictly as 'Boss'. "
            "Keep replies concise, direct, and punchy (1–2 sentences unless asked for detail)."
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": 0.6,
            },
        }

        try:
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data.get("response", "").strip()
                return reply if reply else "No response generated, Boss."

        except urllib.error.URLError as e:
            self.is_active = False
            print(f"[!] Ollama connection error: {e}")
            return "Lost connection to local Ollama, Boss."
        except Exception as e:
            print(f"[!] Local brain error: {e}")
            return "Hit a snag processing that locally, Boss."
    
    def unload_model(self) -> str:
        """Immediately flushes the model from GPU VRAM so you can game at full FPS."""
        payload = {
            "model": self.model,
            "keep_alive": 0,
        }
        try:
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
            return "Model unloaded. All 4 gigabytes of VRAM are yours, Boss. Have fun!"
        except Exception:
            return "VRAM is already clear, Boss."        
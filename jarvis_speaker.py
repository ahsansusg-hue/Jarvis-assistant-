import win32com.client


class JarvisSpeaker:
    """Direct Windows SAPI5 Speech Engine (Zero dependency bugs, 100% reliable)."""

    def __init__(self, rate: int = 150, volume: int = 100):
        try:
            # Directly interface with Windows native SAPI voice server
            self.speaker = win32com.client.Dispatch("SAPI.SPVoice")
            self.speaker.Rate = 0  # Speed (-10 to 10)
            self.speaker.Volume = volume  # Volume (0 to 100)
            self.is_active = True
            print("[SPEAKER] Direct Windows SAPI voice engine online.")
        except Exception as e:
            self.is_active = False
            print(f"[!] Direct speaker init error: {e}")

    def speak(self, text: str):
        """Speaks text out loud synchronously using Windows SAPI."""
        if not self.is_active or not text:
            return
            
        try:
            print(f"JARVIS (Voice): {text}")
            # Speak synchronously (1 = SVSFDefault, 2 = SVSFlagsAsync)
            self.speaker.Speak(text, 1)
        except Exception as e:
            print(f"[!] Speech synthesis error: {e}")
import os
import time
from google import genai
from google.genai import types

class JarvisBrain:
    """Handles conversational AI and persona integration for JARVIS using the modern Google GenAI SDK."""
    
    def __init__(self):
        """Initializes the modern Gemini client with the custom JARVIS persona and safety configurations."""
        # Securely pull API key from environment variables
        api_key: str = os.environ.get("GEMINI_API_KEY", "")
        
        self.system_instruction = (
            "You are JARVIS, a hyper-intelligent, hyper-efficient, loyal, and witty AI assistant "
            "created by Ahsan. You always address the user as 'Boss'. Your tone is razor-sharp, "
            "technically precise, slightly sarcastic, and unfailingly loyal. You manage system operations, "
            "coding tasks, and keep things running smoothly."
        )
        
        try:
            self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
            self.config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
            )
            self.model_name = "gemini-3.5-flash"
            
            self.chat = self.client.chats.create(model=self.model_name, config=self.config)
            self.is_active = True
            
        except Exception as e:
            self.is_active = False
            self.init_error = str(e)

    def think(self, user_input: str) -> str:
        """Sends user input to Gemini with automatic exponential backoff retry logic for 503 high-demand errors."""
        if not self.is_active:
            return f"Neural link offline, Boss. API initialization error: {getattr(self, 'init_error', 'Unknown')}"
        
        max_retries = 3
        delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = self.chat.send_message(user_input)
                if response and response.text:
                    return response.text.strip()
                return "Circuit nominal, Boss, but received an empty response packet."
            except Exception as e:
                error_str = str(e)
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= 2
                        continue
                return f"Circuit overload, Boss. Failed to parse query: {e}"
        
        return "Circuit timeout, Boss. Server nodes are currently saturated."
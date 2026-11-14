import os
import time
from google import genai
from google.genai import types
from jarvis_system import JarvisSystem
from jarvis_core import TaskEngine


class JarvisBrain:
    """Handles conversational AI, persona, and real OS/Task execution for JARVIS."""

    def __init__(self, task_engine: TaskEngine):
        self.task_engine = task_engine

        # Replace with your Gemini API key
        api_key: str = "YOUR_ACTUAL_API_KEY_HERE"

        self.system_instruction = (
            "You are JARVIS, a hyper-intelligent, hyper-efficient, loyal, and witty AI assistant "
            "created by Ahsan. You always address the user as 'Boss'. Your tone is razor-sharp, "
            "technically precise, slightly sarcastic, and unfailingly loyal. "
            "CRITICAL RULE: Never pretend or roleplay opening an app, checking system status, or managing tasks. "
            "Whenever the Boss asks to open/launch an app, check system stats, or add/view tasks—even casually "
            "inside a long conversational message—you MUST call the corresponding Python tool first, "
            "then report the real outcome in your signature witty persona."
        )

        try:
            self.client = genai.Client(api_key=api_key)

            # Define clean tool wrappers around your actual classes
            def open_application(app_name: str) -> str:
                """Opens or launches an application or game on the computer (e.g., 'gta', 'windhawk', 'chrome', 'vs code')."""
                return str(JarvisSystem.open_app(app_name))

            def check_system_status() -> str:
                """Fetches real-time system status, CPU, RAM, or battery diagnostics."""
                return str(JarvisSystem.get_system_status())

            def manage_tasks(action: str, task_description: str = "") -> str:
                """Manages the Boss's to-do list.
                Args:
                    action: Either 'add' to create a new task, or 'list' to view current tasks.
                    task_description: The task text to add (required when action is 'add').
                """
                if action == "add" and task_description:
                    if hasattr(self.task_engine, "add_task"):
                        return str(self.task_engine.add_task(task_description))
                if hasattr(self.task_engine, "list_tasks"):
                    return str(self.task_engine.list_tasks())
                if hasattr(self.task_engine, "tasks"):
                    return str(self.task_engine.tasks)
                return "Task operation completed."

            self.config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
                tools=[open_application, check_system_status, manage_tasks],
            )

            self.model_name = "gemini-3.5-flash"
            self.chat = self.client.chats.create(model=self.model_name, config=self.config)
            self.is_active = True

        except Exception as e:
            self.is_active = False
            self.init_error = str(e)

    def think(self, user_input: str) -> str:
        """Sends user input to Gemini, automatically executing any triggered OS or task tools."""
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
import os
import subprocess

class JarvisSystem:
    @staticmethod
    def open_app(app_name):
        """Opens system applications on Windows."""
        app_name = app_name.lower()
        try:
            if "code" in app_name:
                os.system("code")
                return "Opening VS Code..."
            elif "notepad" in app_name:
                os.system("notepad")
                return "Opening Notepad..."
            elif "calc" in app_name:
                os.system("calc")
                return "Opening Calculator..."
            else:
                return f"Unknown app: {app_name}"
        except Exception as e:
            return f"Error launching app: {e}"

    @staticmethod
    def get_system_status():
        """Returns mock system status."""
        return "System nominal. All core engines operational, Boss."
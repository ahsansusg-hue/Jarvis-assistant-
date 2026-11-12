import os
import subprocess
import webbrowser

class JarvisSystem:
    @staticmethod
    def open_app(app_name):
        """Launches any app, batch file, or website completely asynchronously (non-blocking)."""
        app_name = app_name.strip()
        app_lower = app_name.lower()
        
        try:
            # 1. Custom Alias for GTA V Legacy
            if "gta" in app_lower or "grand theft auto" in app_lower:
                gta_path = r"D:\Games\Grand Theft Auto V Legacy\PlayGTAV.bat"
                if os.path.exists(gta_path):
                    # Launch using subprocess specifying the working directory so relative paths inside the batch file work correctly
                    subprocess.Popen(
                        [gta_path], 
                        cwd=r"D:\Games\Grand Theft Auto V Legacy", 
                        shell=True
                    )
                    return "Launching Grand Theft Auto V Legacy, Boss!"
                else:
                    return f"System Warning: GTA V batch file not found at '{gta_path}'."
                
            # 2. Built-in Utilities (using start / detached execution so they don't block)
            elif "notepad" in app_lower:
                subprocess.Popen("notepad", shell=True)
                return "Opening Notepad in the background, Boss."
            elif "calc" in app_lower or "calculator" in app_lower:
                subprocess.Popen("calc", shell=True)
                return "Opening Calculator."
            elif "code" in app_lower or "vs code" in app_lower:
                subprocess.Popen("code", shell=True)
                return "Launching Visual Studio Code."
            elif "paint" in app_lower:
                subprocess.Popen("mspaint", shell=True)
                return "Opening MS Paint."
            elif "cmd" in app_lower or "terminal" in app_lower:
                subprocess.Popen("start cmd", shell=True)
                return "Spinning up a new command prompt."
            
            # 3. Web Shortcuts
            elif "youtube" in app_lower:
                webbrowser.open("https://www.youtube.com")
                return "Opening YouTube."
            elif "github" in app_lower:
                webbrowser.open("https://github.com")
                return "Opening GitHub."
            
            # 4. Universal Non-Blocking Launcher for Any App/Path
            else:
                if os.path.exists(app_name):
                    subprocess.Popen(f'start "" "{app_name}"', shell=True)
                    return f"Successfully launched target path: '{app_name}'."
                
                # Non-blocking background execution for general commands
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                return f"Dispatched launch sequence for '{app_name}'."
                
        except Exception as e:
            return f"Safeguard active: Could not launch '{app_name}'. Error: {e}"

    @staticmethod
    def get_system_status():
        """Returns system status diagnostics."""
        return "System nominal. All core engines operational, Boss."
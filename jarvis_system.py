import os
import glob
import webbrowser

class JarvisSystem:
    @staticmethod
    def _find_shortcut(app_name):
        """Dynamically searches Windows Start Menu shortcuts for any app name."""
        app_name_lower = app_name.lower()
        
        # Standard Windows Start Menu shortcut directories
        search_paths = [
            os.path.expandvars(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\**\*.lnk"),
            os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\**\*.lnk")
        ]
        
        for pattern in search_paths:
            for shortcut in glob.glob(pattern, recursive=True):
                filename = os.path.basename(shortcut).lower()
                # If the app name matches part of the shortcut filename (e.g., 'windhawk' matches 'Windhawk.lnk')
                if app_name_lower in filename:
                    return shortcut
        return None

    @staticmethod
    def open_app(app_name):
        """Universal, unlagable launcher that dynamically resolves any app on the PC."""
        app_name = app_name.strip()
        app_lower = app_name.lower()
        
        try:
            # 1. Custom Alias for GTA V Legacy (Admin Binary Execution)
            if "gta" in app_lower or "grand theft auto" in app_lower:
                exe_path = r"D:\Games\Grand Theft Auto V Legacy\PlayGTAV.exe"
                working_dir = r"D:\Games\Grand Theft Auto V Legacy"
                
                if os.path.exists(exe_path):
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", exe_path, "-nobattleye", working_dir, 1
                    )
                    return "Launching Grand Theft Auto V Legacy as Administrator, Boss!"
                else:
                    return f"System Warning: Executable not found at '{exe_path}'."
            
            # 2. Web Shortcuts
            elif "youtube" in app_lower:
                webbrowser.open("https://www.youtube.com")
                return "Opening YouTube."
            elif "github" in app_lower:
                webbrowser.open("https://github.com")
                return "Opening GitHub."
            
            # 3. Dynamic Universal Resolver (Searches Start Menu for ANY app)
            else:
                # If a direct file path or command was provided
                if os.path.exists(app_name):
                    os.startfile(app_name)
                    return f"Successfully launched target path: '{app_name}'."
                
                # Search Start Menu shortcuts dynamically
                shortcut_path = JarvisSystem._find_shortcut(app_name)
                if shortcut_path:
                    os.startfile(shortcut_path)
                    return f"Dispatched launch sequence for '{app_name}', Boss."
                
                # Fallback to direct system call (for registered commands like notepad, calc, code)
                os.startfile(app_name)
                return f"Dispatched launch sequence for '{app_name}'."
                
        except FileNotFoundError:
            return f"Notice: Target '{app_name}' could not be located on the system, Boss."
        except Exception as e:
            return f"Safeguard active: Could not launch '{app_name}'. Error: {e}"

    @staticmethod
    def get_system_status():
        """Returns system status diagnostics."""
        return "System nominal. All core engines operational, Boss."
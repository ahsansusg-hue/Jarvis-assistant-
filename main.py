from jarvis_system import JarvisSystem

def main():
    print("--- JARVIS System Test ---")
    jarvis_sys = JarvisSystem()
    
    # Test system status
    print(jarvis_sys.get_system_status())
    
    # Test opening notepad (fast check)
    print(jarvis_sys.open_app("notepad"))

if __name__ == "__main__":
    main()
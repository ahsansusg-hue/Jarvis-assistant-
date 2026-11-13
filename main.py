import sys
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain

def main():
    task_engine = TaskEngine()
    brain = JarvisBrain()
    
    print("========================================")
    print("   JARVIS v2.0 - AI Conversational Core ")
    print("========================================")
    print(JarvisSystem.get_system_status())
    print("\nType naturally (e.g., 'open gta', 'launch windhawk', or chat with JARVIS). Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("Boss > ").strip()
            if not user_input:
                continue
                
            lower_input = user_input.lower()
            
            if lower_input in ["exit", "quit", "shutdown"]:
                print("JARVIS: Powering down systems. Have a good one, Boss.")
                break
                
            # Quick command intercepts for system control
            elif "open " in lower_input or "launch " in lower_input:
                # Extract app name after open/launch
                app_target = lower_input.replace("open ", "").replace("launch ", "")
                result = JarvisSystem.open_app(app_target)
                print(f"JARVIS: {result}\n")
                
            elif "task" in lower_input or "todo" in lower_input:
                print("JARVIS: Task management protocols active. Use your menu or ask me to list tasks.")
                # You can expand task intents here easily!
                
            else:
                # Route everything else through the Gemini AI brain with full persona
                ai_response = brain.think(user_input)
                print(f"JARVIS: {ai_response}\n")
                
        except KeyboardInterrupt:
            print("\nJARVIS: Emergency interrupt detected. Standing by, Boss.")
            sys.exit(0)

if __name__ == "__main__":
    main()
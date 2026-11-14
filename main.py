import sys
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain


def main():
    task_engine = TaskEngine()
    brain = JarvisBrain(task_engine=task_engine)

    print("========================================")
    print("   JARVIS v2.0 - AI Conversational Core ")
    print("========================================")
    print(JarvisSystem.get_system_status())
    print("\nType naturally (e.g., 'just chilling, launch gta' or 'remind me to push git'). Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("Boss > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "shutdown"]:
                print("JARVIS: Powering down systems. Have a good one, Boss.")
                break

            # Route everything through Gemini AI Brain (handles both chat and tool execution)
            ai_response = brain.think(user_input)
            print(f"JARVIS: {ai_response}\n")

        except KeyboardInterrupt:
            print("\nJARVIS: Emergency interrupt detected. Standing by, Boss.")
            sys.exit(0)


if __name__ == "__main__":
    main()
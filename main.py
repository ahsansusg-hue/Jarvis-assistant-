import sys
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain
from jarvis_ears import JarvisEars


def main():
    task_engine = TaskEngine()
    brain = JarvisBrain(task_engine=task_engine)
    ears = JarvisEars()

    print("========================================")
    print("   JARVIS v2.0 - Voice Command Core     ")
    print("========================================")
    print(JarvisSystem.get_system_status())
    print("\nJARVIS Voice Core online. Speak your commands hands-free (Ctrl+C to quit).\n")

    while True:
        try:
            # Continuously listens via voice until a valid command is captured
            user_input = ears.listen_command()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "shutdown"]:
                print("JARVIS: Powering down systems. Have a good one, Boss.")
                break

            print(f"Boss > {user_input}")

            # Local Fast-Path Execution (Instant, Free, Zero Quota Waste)
            lower = user_input.lower()
            if "launch " in lower or "open " in lower:
                app_name = lower.replace("launch ", "").replace("open ", "").strip()
                result = JarvisSystem.open_app(app_name)
                print(f"JARVIS: {result}\n")
                continue

            # Route through Gemini AI Brain for conversational queries
            ai_response = brain.think(user_input)
            print(f"JARVIS: {ai_response}\n")

        except KeyboardInterrupt:
            print("\nJARVIS: Emergency interrupt detected. Standing by, Boss.")
            sys.exit(0)


if __name__ == "__main__":
    main()
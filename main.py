import sys
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain
from jarvis_ears import JarvisEars
from jarvis_speaker import JarvisSpeaker


def main():
    task_engine = TaskEngine()
    brain = JarvisBrain(task_engine=task_engine)
    ears = JarvisEars()
    speaker = JarvisSpeaker()

    startup_msg = "Systems nominal. All core engines operational, Boss."
    print("========================================")
    print("   JARVIS v2.0 - Voice & Speech Core    ")
    print("========================================")
    print(JarvisSystem.get_system_status())
    speaker.speak(startup_msg)

    print("\nJARVIS Voice Core online. Speak your commands hands-free (Ctrl+C to quit).\n")

    while True:
        try:
            user_input = ears.listen_command()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "shutdown"]:
                farewell = "Powering down systems. Have a good one, Boss."
                print(f"JARVIS: {farewell}")
                speaker.speak(farewell)
                break

            print(f"Boss > {user_input}")

            # Local Fast-Path Execution (Instant, Free, Zero Quota Waste)
            lower = user_input.lower()

            # 1. App Launcher Fast-Path
            if "launch " in lower or "open " in lower:
                app_name = lower.replace("launch ", "").replace("open ", "").strip()
                result = JarvisSystem.open_app(app_name)
                response_text = f"Opening {app_name}, Boss."
                print(f"JARVIS: {result}\n")
                speaker.speak(response_text)
                continue

            # 2. Voice Task Adder Fast-Path
            if lower.startswith(("add task ", "new task ", "remind me to ")):
                task_title = (
                    lower.replace("add task ", "", 1)
                    .replace("new task ", "", 1)
                    .replace("remind me to ", "", 1)
                    .strip()
                )
                if task_title:
                    result = task_engine.add_task(task_title)
                    print(f"JARVIS: {result}\n")
                    speaker.speak(result)
                else:
                    msg = "What would you like me to add to the list, Boss?"
                    print(f"JARVIS: {msg}\n")
                    speaker.speak(msg)
                continue

            # 3. Read Tasks Fast-Path
            if "list tasks" in lower or "my tasks" in lower or "read tasks" in lower:
                raw_tasks = task_engine.list_tasks()
                
                # Format cleanly if TaskEngine returns a raw list of dicts
                if isinstance(raw_tasks, list):
                    pending = [t for t in raw_tasks if t.get("status") == "pending"]
                    if not pending:
                        result = "Your task list is completely clear, Boss."
                    else:
                        items = ", ".join([f"Task {t['id']}: {t['title']}" for t in pending])
                        result = f"You have {len(pending)} pending tasks, Boss. {items}."
                else:
                    result = str(raw_tasks)

                print(f"JARVIS: {result}\n")
                speaker.speak(result)
                continue
            # 4. Complete Task Fast-Path
            if any(phrase in lower for phrase in ["complete task ", "finish task ", "mark task ", "done with "]):
                target = lower
                for phrase in ["complete task ", "finish task ", "mark task ", "done with ", " as completed", " as done"]:
                    target = target.replace(phrase, "")
                target = target.strip()

                if target:
                    result = task_engine.complete_task(target)
                else:
                    result = "Which task number or name should I mark as completed, Boss?"

                print(f"JARVIS: {result}\n")
                speaker.speak(result)
                continue

        except KeyboardInterrupt:
            interrupt_msg = "Emergency interrupt detected. Standing by, Boss."
            print(f"\nJARVIS: {interrupt_msg}")
            speaker.speak(interrupt_msg)
            sys.exit(0)


if __name__ == "__main__":
    main()
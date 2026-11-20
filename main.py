import time
from jarvis_ears import JarvisEars
from jarvis_speaker import JarvisSpeaker
from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem
from jarvis_brain import JarvisBrain


def main():
    print("==========================================")
    print("   JARVIS LOCAL SYSTEM — INITIALIZING     ")
    print("==========================================")

    speaker = JarvisSpeaker()
    listener = JarvisEars()
    task_engine = TaskEngine()
    system = JarvisSystem()
    brain = JarvisBrain(task_engine=task_engine, model="qwen2.5:3b")

    startup_msg = "All systems online and running locally, Boss."
    print(f"JARVIS: {startup_msg}\n")
    speaker.speak(startup_msg)

    while True:
        try:
            text = listener.listen_command()
            if not text:
                continue

            text = str(text).strip()
            if not text:
                continue

            print(f"You: {text}")
            lower = text.lower()

            # --- FAST-PATH 0: Shutdown / Exit ---
            if any(phrase in lower for phrase in ["shut down", "shutdown", "go to sleep", "exit jarvis", "goodbye jarvis"]):
                bye_msg = "Powering down local core. Catch you later, Boss."
                print(f"JARVIS: {bye_msg}\n")
                speaker.speak(bye_msg)
                break

            # --- FAST-PATH 1: Gaming Mode (Instant VRAM Flush) ---
            if any(phrase in lower for phrase in ["gaming mode", "unload model", "free vram", "clear vram"]):
                result = brain.unload_model() if hasattr(brain, "unload_model") else "VRAM flush unavailable, Boss."
                print(f"JARVIS: {result}\n")
                speaker.speak(result)
                continue

            # --- FAST-PATH 2: System Status ---
            if any(phrase in lower for phrase in ["system status", "status report", "check system"]):
                result = system.get_system_status()
                print(f"JARVIS: {result}\n")
                speaker.speak(str(result))
                continue

            # --- FAST-PATH 3: Open App ---
            if lower.startswith("open ") or "launch " in lower:
                app_name = lower
                for prefix in ["jarvis ", "please ", "can you ", "launch ", "open "]:
                    app_name = app_name.replace(prefix, "")
                app_name = app_name.strip()

                if app_name:
                    result = system.open_app(app_name)
                else:
                    result = "Which app should I open, Boss?"

                print(f"JARVIS: {result}\n")
                speaker.speak(str(result))
                continue

            # --- FAST-PATH 4: Add Task ---
            if any(phrase in lower for phrase in ["add task ", "new task ", "remind me to "]):
                title = lower
                for phrase in ["add task ", "new task ", "remind me to "]:
                    title = title.replace(phrase, "")
                title = title.strip()

                if title:
                    result = task_engine.add_task(title)
                else:
                    result = "What task would you like me to add, Boss?"

                print(f"JARVIS: {result}\n")
                speaker.speak(str(result))
                continue

            # --- FAST-PATH 5: Read / List Tasks ---
            if any(phrase in lower for phrase in ["list tasks", "read tasks", "my tasks", "what are my tasks", "show tasks"]):
                result = task_engine.list_tasks()
                print(f"JARVIS: {result}\n")
                speaker.speak(str(result))
                continue

            # --- FAST-PATH 6: Complete Task ---
            if any(phrase in lower for phrase in ["complete task ", "finish task ", "mark task ", "done with "]):
                target = lower
                for phrase in ["complete task ", "finish task ", "mark task ", "done with ", " as completed", " as done"]:
                    target = target.replace(phrase, "")
                target = target.strip()

                if target:
                    result = task_engine.complete_task(target)
                else:
                    result = "Which task should I mark as completed, Boss?"

                print(f"JARVIS: {result}\n")
                speaker.speak(str(result))
                continue

            # --- LOCAL LLM FALLBACK: General Reasoning via Ollama ---
            reply = brain.think(text)
            print(f"JARVIS: {reply}\n")
            speaker.speak(str(reply))

        except KeyboardInterrupt:
            print("\n[SYSTEM] Shutting down...")
            break
        except Exception as e:
            print(f"[!] Runtime error: {e}")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
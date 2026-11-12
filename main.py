from jarvis_core import TaskEngine
from jarvis_system import JarvisSystem

def main():
    task_engine = TaskEngine()
    jarvis_sys = JarvisSystem()

    print("========================================")
    print("   JARVIS v1.0 - AI System Online       ")
    print("========================================")
    print(jarvis_sys.get_system_status())

    while True:
        print("\n--- Command Menu ---")
        print("1. View Tasks")
        print("2. Add Task")
        print("3. Complete Task")
        print("4. Delete Task")
        print("5. Open App (VS Code, Notepad, Calc)")
        print("6. Exit")

        choice = input("\nEnter your command (1-6): ").strip()

        if choice == "1":
            tasks = task_engine.list_tasks()
            if not tasks:
                print("\nNo tasks found. Your queue is clean, Boss.")
            else:
                print("\nCurrent Tasks:")
                for task in tasks:
                    print(f"[{task['id']}] {task['title']} - Status: [{task['status']}]")

        elif choice == "2":
            title = input("Enter task description: ").strip()
            if title:
                print(task_engine.add_task(title))
            else:
                print("Task title cannot be empty.")

        elif choice == "3":
            try:
                task_id = int(input("Enter Task ID to complete: ").strip())
                print(task_engine.complete_task(task_id))
            except ValueError:
                print("Please enter a valid numeric ID.")

        elif choice == "4":
            try:
                task_id = int(input("Enter Task ID to delete: ").strip())
                print(task_engine.delete_task(task_id))
            except ValueError:
                print("Please enter a valid numeric ID.")

        elif choice == "5":
            app_name = input("Which app would you like to open? (code/notepad/calc/youtube/github): ").strip()
            print(jarvis_sys.open_app(app_name))

        elif choice == "6":
            print("\nShutting down systems. Goodbye, Boss.")
            break
        else:
            print("Invalid option. Please choose between 1 and 6.")

if __name__ == "__main__":
    main()
from jarvis_core import TaskEngine

def main():
    print("--- JARVIS Daily Task Manager ---")
    jarvis = TaskEngine()

    # Add a test task for Day 1
    message = jarvis.add_task("Learn Git workflow and build Jarvis core")
    print(message)

    # Display all tasks
    print("\nCurrent Tasks:")
    for task in jarvis.list_tasks():
        print(f"[{task['id']}] {task['title']} - Status: {task['status']}")

if __name__ == "__main__":
    main()
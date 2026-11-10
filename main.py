from jarvis_core import TaskEngine

def main():
    print("--- JARVIS Daily Task Manager ---")
    jarvis = TaskEngine()

    # 1. Show existing tasks
    print("\nCurrent Tasks:")
    for task in jarvis.list_tasks():
        print(f"[{task['id']}] {task['title']} - Status: {task['status']}")

    # 2. Test completing the first task (ID: 1)
    print("\n[Testing Complete]")
    print(jarvis.complete_task(1))

    # 3. Test adding a temporary task and deleting it
    print("\n[Testing Add & Delete]")
    print(jarvis.add_task("Temporary task to test deletion"))
    
    # Show tasks before deletion
    for task in jarvis.list_tasks():
        print(f"[{task['id']}] {task['title']} - Status: {task['status']}")

    # Delete the temporary task (assuming it's ID 2)
    print(jarvis.delete_task(2))

    # 4. Final task list review
    print("\nFinal Task List:")
    for task in jarvis.list_tasks():
        print(f"[{task['id']}] {task['title']} - Status: {task['status']}")

if __name__ == "__main__":
    main()
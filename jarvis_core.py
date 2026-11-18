import json
import os

class TaskEngine:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks = self.load_tasks()

    def load_tasks(self):
        """Loads tasks from a JSON file if it exists, otherwise returns an empty list."""
        if os.path.exists(self.filename):
            with open(self.filename, "r") as file:
                return json.load(file)
        return []

    def save_tasks(self):
        """Saves current tasks to the JSON file."""
        with open(self.filename, "w") as file:
            json.dump(self.tasks, file, indent=4)

    def add_task(self, title):
        """Adds a new task and saves it instantly."""
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "status": "pending"
        }
        self.tasks.append(task)
        self.save_tasks()
        return f"Task '{title}' added successfully!"

    def list_tasks(self):
        """Returns all current tasks."""
        return self.tasks

    def complete_task(self, task_id):
        """Marks a specific task as completed by its ID."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                self.save_tasks()
                return f"Task {task_id} marked as completed!"
        return f"Task ID {task_id} not found."

    def delete_task(self, task_id):
        """Deletes a specific task by its ID."""
        for task in self.tasks:
            if task["id"] == task_id:
                self.tasks.remove(task)
                self.save_tasks()
                return f"Task {task_id} deleted successfully!"
        return f"Task ID {task_id} not found."
    def complete_task(self, identifier: str) -> str:
        word_to_num = {
            "one": "1", "two": "2", "to": "2", "too": "2",
            "three": "3", "four": "4", "for": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
        }
        clean_id = word_to_num.get(identifier.lower().strip(), identifier.lower().strip())

        for task in self.tasks:
            # Match either by Task ID or by a keyword inside the title
            if str(task.get("id")) == clean_id or clean_id in task.get("title", "").lower():
                if task.get("status") == "completed":
                    return f"Task {task['id']}, {task['title']}, is already marked completed, Boss."
                task["status"] = "completed"
                self.save_tasks()
                return f"Marked task {task['id']}, {task['title']}, as completed, Boss."

        return f"I couldn't find a task matching '{identifier}', Boss."
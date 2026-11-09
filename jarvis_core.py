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
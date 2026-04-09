from datetime import timedelta
import uuid


# Task
class Task:
    def __init__(self, name, difficulty_score, category):
        self.name = name
        self.difficulty_score = difficulty_score
        self.category = category  # heavy / light / admin


# Assignment 
class VolunteerAssignment:
    def __init__(self, user_id, shift_id, role, deadline):
        self.user_id = user_id
        self.shift_id = shift_id
        self.role = role
        self.status = "assigned"
        self.deadline = deadline
        self.hours = 0
    
    def complete_assignment(self):
        self.status = "completed"

# Shift
class Shift:
    def __init__(self, start_date, end_date):
        self.id = str(uuid.uuid4())
        self.start_date = start_date
        self.end_date = end_date
        self.tasks = []
        self.assignments = []
        self.status = "scheduled"

    def add_task(self, task_name, difficulity_score, category):
        task = Task(task_name, difficulity_score, category)
        self.tasks.append(task)


# Ledger (Mandatory Hours)
class ServiceLedger:
    def __init__(self):
        self.records = {}

    def add_user(self, user_id, required_hours):
        self.records[user_id] = {
            "required": required_hours,
            "completed": 0
        }

    def update_user(self, user_id, required_hours):
        self.records[user_id]["required"] += required_hours

    def log_hours(self, user_id, hours):
        if user_id in self.records:
            self.records[user_id]["completed"] += hours

    def is_compliant(self, user_id):
        r = self.records.get(user_id)
        return r and r["completed"] >= r["required"]

    def __repr__(self):
        if not self.records:
            return "ServiceLedger(empty)"

        lines = ["ServiceLedger:"]
        for user_id, data in self.records.items():
            required = data["required"]
            completed = data["completed"]
            status = "compliant" if completed >= required else "not compliant"

            lines.append(
                f"  User {user_id}: {completed}/{required} hours ({status})"
            )

        return "\n".join(lines)

class SwapRequest:
    def __init__(self, requester_id, target_id, shift_id):
        self.request_id = str(uuid.uuid4())
        self.requester_id = requester_id
        self.target_id = target_id
        self.shift_id = shift_id
        self.status = "pending"  # pending, approved, rejected


from datetime import datetime, timedelta
from member import Member
import uuid


# Task
class Task:
    def __init__(self, name, difficulty_score, category):
        self.name = name
        self.difficulty_score = difficulty_score
        self.category = category  # heavy / light / admin


# Assignment 
class VolunteerAssignment:
    def __init__(self, user_id, shift_id, role):
        self.user_id = user_id
        self.shift_id = shift_id
        self.role = role
        self.status = "assigned"
        self.hours = 0


# Shift
class Shift:
    def __init__(self, date):
        self.shift_id = str(uuid.uuid4())
        self.date = date
        self.tasks = []
        self.assignments = []
        self.status = "scheduled"

    def add_task(self, task):
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

# Volunteer System
class VolunteerSystem:
    def __init__(self):
        self.member_contribution = {} # {member_id: (total_volunteer_hours,total_heavy_hours)}
        self.shifts = []
        self.swap_requests = []
        self.ledger = ServiceLedger()

    def add_member(self, member_id, required_hours=10):
        self.ledger.add_user(member_id, required_hours)
        self.member_contribution[member_id] = {
            "total_hours": 0,
            "heavy_hours": 0
        }

    def update_ledger(self, member_id, required_hours=10):
        self.ledger.update_user(member_id, required_hours)

    def add_task_to_shift(self, task, shift_id):
        found_shift = None
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                found_shift = shift

        if found_shift:
            found_shift.add_task(task)
            return True

        return False

    def assign_members_to_shift(self, shift_id, member_ids):
        found_shift = None

        for shift in self.shifts:
            if shift.shift_id == shift_id:
                found_shift = shift
                break

        if not found_shift:
            return  

        shift = found_shift

        # TODO: should we remove this and just add the contribution 0 0  not ledger
        for mid in member_ids:
            if mid not in self.member_contribution:
                self.add_member(mid)
    
        # Sort members by least heavy work
        sorted_members = sorted(
            member_ids,
            key=lambda mid: self.member_contribution[mid]["heavy_hours"]
        )
    
        heavy_tasks = [t for t in shift.tasks if t.category == "heavy"]
    
        assignments = []
    
        # Assign heavy tasks first
        for i in range(len(heavy_tasks)):
            if i < len(sorted_members):
                assignments.append(
                    VolunteerAssignment(sorted_members[i], shift.shift_id, "heavy")
                )
    
        # Remaining members → light tasks
        for mid in sorted_members[len(heavy_tasks):]:
            assignments.append(
                VolunteerAssignment(mid, shift.shift_id, "light")
            )
    
        shift.assignments = assignments
    

    def complete_shift(self, shift):
        for assignment in shift.assignments:
            assignment.status = "completed"
            assignment.hours = 2  # example
    
            # Update totals
            self.member_contribution[assignment.user_id]["total_hours"] += assignment.hours
    
            if assignment.role == "heavy":
                self.member_contribution[assignment.user_id]["heavy_hours"] += 1
    
            # Update ledger
            self.ledger.log_hours(assignment.user_id, assignment.hours)
    
        shift.status = "completed"

    def get_member_history(self, user_id):
        history = []

        for shift in self.shifts:
            for a in shift.assignments:
                if a.user_id == user_id:
                    history.append({
                        "shift": shift.shift_id,
                        "date": shift.date,
                        "role": a.role,
                        "status": a.status
                    })

        return history

    def check_weather(self, shift_id, weather):
        found_shift = None
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                found_shift = shift
                break
        if not found_shift:
            return

        shift = found_shift
        if weather in ["heavy_rain", "extreme_heat"]:
            shift.status = "reschduled"

            shift.date = shift.date + timedelta(days=1) 
            return 

 
    def request_swap(self, requester_id, target_id, shift_id):    
        shift = next((s for s in self.shifts if s.shift_id == shift_id), None)

        if not shift:
            return None
    
        # Check requester is assigned to the shift
        requester_assigned = any(a.user_id == requester_id for a in shift.assignments)
        if not requester_assigned:
            print("Requister not assigned")
            return None
    
        swap = SwapRequest(requester_id, target_id, shift_id)
        self.swap_requests.append(swap)
    
        return swap   

    def approve_swap(self, request_id):
        swap = next((r for r in self.swap_requests if r.request_id == request_id), None)
        if not swap or swap.status != "pending":
            return False
    
        shift = next((s for s in self.shifts if s.shift_id == swap.shift_id), None)
        if not shift:
            return False
    
        # Find assignment of requester
        assignment = next((a for a in shift.assignments if a.user_id == swap.requester_id), None)
        if not assignment:
            return False
    
        # Perform swap (replace user)
        assignment.user_id = swap.target_id
    
        swap.status = "approved"
        return True

    def reject_swap(self, request_id):
        swap = next((r for r in self.swap_requests if r.request_id == request_id), None)
        if not swap:
            return False
    
        swap.status = "rejected"
        return True
    
    def add_task(self, shift_id, task_name,difficulty_score, category):
        task = Task(task_name, difficulty_score, category)
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                shift.tasks.append(task)
                return True
        return False

    def create_shift(self, date):
        shift = Shift(date)
        self.shifts.append(shift)
        return shift

# TEST SCENARIO
if __name__ == "__main__":
    system = VolunteerSystem()

    # Create members
    m1 = Member("M1", "Alice")
    m2 = Member("M2", "Bob")
    m3 = Member("M3", "Charlie")

    system.add_member(m1)
    system.add_member(m2)
    system.add_member(m3)

    # Create tasks
    t1 = Task("Turn Compost", 9, "heavy")
    t2 = Task("Move Soil", 8, "heavy")
    t3 = Task("Water Plants", 3, "light")

    # Create shift
    shift = Shift(datetime.now())
    shift.add_task(t1)
    shift.add_task(t2)
    shift.add_task(t3)

    system.shifts.append(shift)

    print("\n--- Assign Members ---")
    system.assign_members_to_shift(shift, ["M1", "M2", "M3"])

    for a in shift.assignments:
        print(vars(a))

    print("\n--- Complete Shift ---")
    system.complete_shift(shift)

    for m in system.members.values():
        print(m.name, "hours:", m.total_volunteer_hours,
              "| heavy:", m.heavy_task_count,
              "| light:", m.light_task_count)

    print("\n--- Ledger ---")
    print(system.ledger.records)

    print("\n--- History (Alice) ---")
    history = system.get_member_history("M1")
    for h in history:
        print(h)

    print("\n--- Next Shift (Balance Test) ---")
    shift2 = Shift(datetime.now() + timedelta(days=1))
    shift2.add_task(t1)
    shift2.add_task(t3)

    system.shifts.append(shift2)

    system.assign_members_to_shift(shift2, ["M1", "M2", "M3"])

    for a in shift2.assignments:
        print(vars(a))

    print("\n--- Weather Cancellation ---")
    system.check_weather(shift2, "heavy_rain")
    print("Shift2 status:", shift2.status)

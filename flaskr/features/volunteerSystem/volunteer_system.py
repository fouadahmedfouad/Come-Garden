from datetime import timedelta
import uuid


from features.volunteerSystem.volunteer_system_info import (
    Task,
    VolunteerAssignment,
    Shift,
    ServiceLedger,
    SwapRequest
)

# Volunteer System
class VolunteerSystem:
    def __init__(self):
        self.member_contribution = {} # {member_id: (total_volunteer_hours,total_heavy_hours)}
        self.shifts = {}
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
    
    def add_shift(self, user, date):
        # admin
        shift = Shift(date)
        self.shifts[shift.id] = shift
        user.shifts_ids.append(shift.id)
        return shift


    def add_task(self, user, shift_id, task_name,difficulty_score, category):
        # admin

        task = Task(task_name, difficulty_score, category)
        shift = self.shifts.get(shift_id)

        if shift:
            shift.tasks.append(task)
            return True
        return False
    
    def add_task_to_shift(self,user, task, shift_id):
        shift = self.shifts.get(shift_id)
        
        if shift:
            shift.add_task(task)
            return True

        return False

    def assign_members_to_shift(self, user , shift_id, members):
        shift = self.shifts.get(shift_id)

        if not shift:
            return None

        for m in members:
            m.shifts_ids.append(shift_id)



        for m in members:
            if m.id not in self.member_contribution:
                self.member_contribution[m.id] = {
                    "total_hours": 0,
                    "heavy_hours": 0
                }

        # Sort members by least heavy work
        sorted_members = sorted(
            members,
            key=lambda m: self.member_contribution[m.id]["heavy_hours"]
        )
    
        heavy_tasks = [t for t in shift.tasks if t.category == "heavy"]
    
        assignments = []
    
        # Assign heavy tasks first
        for i in range(len(heavy_tasks)):
            if i < len(sorted_members):
                assignments.append(
                    VolunteerAssignment(sorted_members[i].id, shift.id, "heavy")
                )
    
        # Remaining members → light tasks
        for m in sorted_members[len(heavy_tasks):]:
            assignments.append(
                VolunteerAssignment(m.id, shift.id, "light")
            )
    
        shift.assignments = assignments
        return assignments 

    def complete_shift(self, user, shift_id):
        # admin 
        shift = self.shifts.get(shift_id)
        if not shift:
            return None

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
        return shift

    def check_weather(self,user, shift_id, weather):
        #admin
        shift = self.shifts.get(shift_id)

        if not shift:
            return 

        if weather in ["heavy_rain", "extreme_heat"]:
            shift.status = "reschduled"

            shift.date = shift.date + timedelta(days=1) 
            return shift 

    def get_member_history(self, user_id):
        history = []

        for shift in self.shifts:
            for a in shift.assignments:
                if a.user_id == user_id:
                    history.append({
                        "shift": shift.id,
                        "date": shift.date,
                        "role": a.role,
                        "status": a.status
                    })

        return history




    def request_swap(self, user, target, shift_id):    
        shift = self.shifts.get(shift_id)

        if not shift:
            return None
    
        # Check requester is assigned to the shift
        requester_assigned = any(a.user_id == user.id for a in shift.assignments)
        if not requester_assigned:
            print("Requister not assigned")
            return None
    
        swap = SwapRequest(user.id, target.id, shift_id)
        self.swap_requests.append(swap) 
        target.swaps_req_ids.append(swap.request_id)

        return swap   



    def approve_swap(self, user, request_id):
        swap = next((r for r in self.swap_requests if r.request_id == request_id), None)

        if not swap or swap.status != "pending":
            return False

        shift = self.shifts.get(swap.shift_id) 
        if not shift:
            return False
    
        # Find assignment of requester
        assignment = next((a for a in shift.assignments if a.user_id == swap.requester_id), None)
        if not assignment:
            return False
    
        # Perform swap (replace user)
        assignment.user_id = swap.target_id
        user.swaps_req_ids.remove(request_id)
    
        swap.status = "approved"
        return True

    def reject_swap(self, request_id):
        swap = next((r for r in self.swap_requests if r.request_id == request_id), None)
        if not swap:
            return False
    
        swap.status = "rejected"
        return True
   

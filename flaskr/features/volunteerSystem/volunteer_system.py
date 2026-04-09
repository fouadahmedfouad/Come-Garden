from datetime import datetime, timedelta
import uuid


from features.volunteerSystem.volunteer_system_info import (
    Task,
    VolunteerAssignment,
    Shift,
    ServiceLedger,
    SwapRequest
)

class VolunteerSystem:
    def __init__(self):
        self.member_contribution = {} 
        self.shifts = {}
        self.ledger = ServiceLedger()

    def add_member(self, member_id, required_hours=10):
        self.ledger.add_user(member_id, required_hours)
        self.member_contribution[member_id] = {
            "total_hours": 0,
            "heavy_hours": 0
        }

    def add_shift(self, user, start_date, duration_days):
        # admin
        start_date = start_date.date()
        end_date = start_date + timedelta(days=duration_days)
        shift = Shift(start_date, end_date)

        self.shifts[shift.id] = shift
        user.shifts.append(shift)
        return shift

    def assign(self, user, shift, members):
        # admin

        if not shift:
            return None

        # Ensure all members have a contribution record
        for member in members:
            self.member_contribution.setdefault(member.id, {
                "total_hours": 0,
                "heavy_hours": 0
            })

        # Sort members by least heavy work
        sorted_members = sorted(
            members,
            key=lambda m: self.member_contribution[m.id]["heavy_hours"]
        )

        # Separate heavy and light tasks
        heavy_tasks = [t for t in shift.tasks if t.category == "heavy"]
        light_tasks_count = len(shift.tasks) - len(heavy_tasks)

        assignments = []

        # Assign heavy tasks
        for member, task in zip(sorted_members, heavy_tasks):
            assignment = VolunteerAssignment(member.id, shift.id, task.name, shift.end_date)
            assignments.append(assignment)

            member.tasks.append(assignment)

        # Assign remaining members to light tasks
        remaining_members = sorted_members[len(heavy_tasks):]
        for member in remaining_members[:light_tasks_count]:
            assignment = VolunteerAssignment(member.id, shift.id, task.name, shift.end_date)
            assignments.append(assignment)
            member.tasks.append(assignment)

        shift.assignments = assignments
        return assignments    

    def complete_shift(self, user, shift):
        """
        Complete a shift immediately (admin-triggered).
        Marks all assignments as completed and updates member contributions.
        """
        if not shift:
            return None

        for assignment in shift.assignments:
            if getattr(assignment, "status", None) != "completed":
                assignment.status = "completed"
                # assume 2 hours per assignment
                assignment.hours = getattr(assignment, "hours", 2)

                # Update totals
                self.member_contribution[assignment.user_id]["total_hours"] += assignment.hours
                if assignment.role == "heavy":
                    self.member_contribution[assignment.user_id]["heavy_hours"] += 1

                # Update ledger
                self.ledger.log_hours(assignment.user_id, assignment.hours)

        shift.status = "completed"
        return shift


    def audit_all_shifts(self, user):
        """
        Daily audit: checks all shifts against end_date + grace_days.
        Reports incomplete assignments without completing them.
        """
        today = datetime.now().date()
        all_reports = []

        for shift in self.shifts:
            end_date = shift.end_date

            if today >= end_date:
                incomplete_assignments = [
                    a for a in shift.assignments if getattr(a, "status", None) != "completed"
                ]
                if incomplete_assignments:
                    report = {
                        "shift_id": shift.id,
                        "incomplete_assignments": [
                            {"user_id": a.user_id, "role": a.role} for a in incomplete_assignments
                        ]
                    }
                    all_reports.append(report)
                    shift.status = "incomplete"
                else:
                    shift.status = "completed"

        if all_reports:
            print("Incomplete Assignments Report:", all_reports)
        # self.notify_admin(all_reports) 


    def check_weather(self,user, shift, weather):
        #admin
        """current: Delay one day if the weather of today is not good """

        if not shift:
            return 

        if weather in ["heavy_rain", "extreme_heat"]:
            shift.status = "reschduled"

            shift.start_date = shift.start_date + timedelta(days=1) 
            return shift 

    def get_member_history(self, user_id):
        history = []

        for shift in self.shifts:
            for a in shift.assignments:
                if a.user_id == user_id:
                    history.append({
                        "shift": shift.id,
                        "date": shift.start_date,
                        "role": a.role,
                        "status": a.status
                    })

        return history


    def update_ledger(self, member_id, required_hours=10):
        self.ledger.update_user(member_id, required_hours)
    


    def request_swap(self, user, target, assignment):    

        # find the shift
        shift = self.shifts.get(assignment.shift_id)

        if not shift:
            return None
    
        # Check requester is assigned to the shift
        requester_assigned = any(a.user_id == user.id for a in shift.assignments)
        if not requester_assigned:
            print("Requister not assigned")
            return None
    
        swap = SwapRequest(user.id, target.id, shift.id)

        user.sent_swap_reqs.append(swap) 
        target.swap_reqs.append(swap)

        return swap   



    def approve_swap(self, user, request):
        shift = self.shifts.get(request.shift_id)

        if not shift:
            return False
    
        # Find assignment of requester
        assignment = next((a for a in shift.assignments if a.user_id == request.requester_id), None)
        if not assignment:
            return False
    
        # Perform swap (replace user)
        assignment.user_id = request.target_id

        request.status = "approved"
        return True

    def reject_swap(self, user, request):
        if not request:
            return False
    
        request.status = "rejected"
        return True
   

from datetime import datetime, timedelta
import uuid
from datetime import datetime, timedelta

from features.volunteerSystem.volunteer_system_exceptions import *
from features.volunteerSystem.volunteer_system_results import *
from features.volunteerSystem.volunteer_system_info import *
from features.volunteerSystem.volunteer_system_events import *

class VolunteerSystem:
    def __init__(self, weather_service=None):
        self.member_contribution = {}
        self.shifts = {}
        self.ledger = ServiceLedger()
        self.weather_service = weather_service or WeatherService()

        self.events = []

    def _emit_event(self, event):
        self.events.append(event)
        self._handle_event(event)

        # furture monitoring
        # self.monitor.log(
        #     action=event.type,
        #     user_id=event.user_id,
        #     metadata=event.data
        # )

    def _handle_event(self, event):

        #  Weather anomaly tracking
        if event.type == "shift_created" and event.data.get("rescheduled"):
            print(f"[Info] Shift {event.data['shift_id']} rescheduled due to {event.data['weather']}")

        # Fairness monitoring
        if event.type == "members_assigned":
            if event.data["count"] == 0:
                print("[Alert] No members assigned to shift")

        # Contribution tracking anomaly
        if event.type == "shift_completed":
            shift = self.shifts.get(event.data["shift_id"])
            if shift and not shift.assignments:
                print("[Alert] Shift completed with no assignments")

        # Swap monitoring
        if event.type == "swap_requested":
            print(f"[Info] Swap requested from {event.user_id} → {event.data['target_id']}")

        # Abuse detection
        if event.type == "swap_requested":
            ## may detect a too many swaps from some member
            pass 

    def add_member(self, member_id, required_hours=10) -> OperationResult:
        try:
            if not member_id:
                raise InvalidUserError(member_id)

            self.ledger.add_user(member_id, required_hours)
            self.member_contribution[member_id] = {
                "total_hours": 0,
                "heavy_hours": 0
            }

            self._emit_event(
                MemberAdded(member_id, required_hours)
            )
            return OperationResult(success=True)

        except VolunteerSystemError as e:
            return OperationResult(False, str(e))
        except Exception as e:
            return OperationResult(False, f"[Critical] {e}")

    def _adjust_for_weather(self, shift):
        weather = self.weather_service.get_weather(shift.start_date)

        if weather in ["heavy_rain", "extreme_heat"]:
            shift.start_date += timedelta(days=1)
            shift.end_date += timedelta(days=1)
            shift.status = "rescheduled"

            return True, weather

        return False, weather

    def add_shift(self, user, start_date, duration_days) -> ShiftResult:
        try:
            if not user or not getattr(user, "is_admin", False):
                raise AuthorizationError(getattr(user, "id", None), "add_shift")

            start_date = start_date.date()
            end_date = start_date + timedelta(days=duration_days)

            shift = Shift(start_date, end_date)

            rescheduled, weather = self._adjust_for_weather(shift)

            self.shifts[shift.id] = shift

            user.shifts = getattr(user, "shifts", [])
            user.shifts.append(shift)
            
            self._emit_event(
                ShiftCreated(
                    user.id,
                    shift.id,
                    rescheduled=rescheduled,
                    weather=weather
                )
            )

            return ShiftResult(
                success=True,
                shift=shift,
                error=f"Rescheduled due to {weather}" if rescheduled else None
            )

        except VolunteerSystemError as e:
            return ShiftResult(False, error=str(e))

        except Exception as e:
            return ShiftResult(False, error=f"[Critical] {e}")

    def assign(self, user, shift, members) -> AssignmentResult:
        try:
            if not user or not getattr(user, "is_admin", False):
                raise AuthorizationError(getattr(user, "id", None), "assign")

            if not shift:
                raise ShiftNotFoundError(None)

            for member in members:
                self.member_contribution.setdefault(member.id, {
                    "total_hours": 0,
                    "heavy_hours": 0
                })

            sorted_members = sorted(
                members,
                key=lambda m: self.member_contribution[m.id]["heavy_hours"]
            )

            heavy_tasks = [t for t in shift.tasks if t.category == "heavy"]
            light_tasks = [t for t in shift.tasks if t.category != "heavy"]

            assignments = []

            # Heavy
            for member, task in zip(sorted_members, heavy_tasks):
                assignment = VolunteerAssignment(member.id, shift.id, task.name, shift.end_date)
                assignments.append(assignment)

                member.tasks = getattr(member, "tasks", [])
                member.tasks.append(assignment)

            # Light
            remaining_members = sorted_members[len(heavy_tasks):]
            for member, task in zip(remaining_members, light_tasks):
                assignment = VolunteerAssignment(member.id, shift.id, task.name, shift.end_date)
                assignments.append(assignment)

                member.tasks.append(assignment)

            shift.assignments = assignments

            self._emit_event(
                MembersAssigned(user.id, shift.id, len(assignments))
            )

            return AssignmentResult(True, assignments)

        except VolunteerSystemError as e:
            return AssignmentResult(False, error=str(e))
        except Exception as e:
            return AssignmentResult(False, error=f"[Critical] {e}")

    def complete_shift(self, user, shift) -> ShiftResult:
        try:
            if not user or not getattr(user, "is_admin", False):
                raise AuthorizationError(getattr(user, "id", None), "complete_shift")

            if not shift:
                raise ShiftNotFoundError(None)

            for assignment in shift.assignments:
                if getattr(assignment, "status", None) != "completed":
                    assignment.status = "completed"
                    assignment.hours = getattr(assignment, "hours", 2)

                    self.member_contribution[assignment.user_id]["total_hours"] += assignment.hours

                    if assignment.role == "heavy":
                        self.member_contribution[assignment.user_id]["heavy_hours"] += 1

                    self.ledger.log_hours(assignment.user_id, assignment.hours)

            shift.status = "completed"

            self._emit_event(
                ShiftCompleted(user.id, shift.id)
            )

            return ShiftResult(True, shift)

        except VolunteerSystemError as e:
            return ShiftResult(False, error=str(e))
        except Exception as e:
            return ShiftResult(False, error=f"[Critical] {e}")

    def request_swap(self, user, target, assignment) -> SwapResult:
        try:
            shift = self.shifts.get(assignment.shift_id)
            if not shift:
                raise ShiftNotFoundError(assignment.shift_id)

            if not any(a.user_id == user.id for a in shift.assignments):
                raise SwapRequestError("Requester not assigned to this shift")

            swap = SwapRequest(user.id, target.id, shift.id)

            user.sent_swap_reqs = getattr(user, "sent_swap_reqs", [])
            target.swap_reqs = getattr(target, "swap_reqs", [])

            user.sent_swap_reqs.append(swap)
            target.swap_reqs.append(swap)

            self._emit_event(
                SwapRequested(user.id, target.id, shift.id)
            )

            return SwapResult(True, swap)

        except VolunteerSystemError as e:
            return SwapResult(False, error=str(e))
        except Exception as e:
            return SwapResult(False, error=f"[Critical] {e}")

    def approve_swap(self, user, request) -> OperationResult:
        try:
            shift = self.shifts.get(request.shift_id)
            if not shift:
                raise ShiftNotFoundError(request.shift_id)

            assignment = next(
                (a for a in shift.assignments if a.user_id == request.requester_id),
                None
            )

            if not assignment:
                raise AssignmentError("Assignment not found")

            assignment.user_id = request.target_id
            request.status = "approved"

            self._emit_event(
                SwapApproved(user.id, request.shift_id)
            )

            return OperationResult(True)

        except VolunteerSystemError as e:
            return OperationResult(False, str(e))
        except Exception as e:
            return OperationResult(False, f"[Critical] {e}")

    def reject_swap(self, user, request) -> OperationResult:
        try:
            if not request:
                raise SwapRequestError("Invalid request")

            request.status = "rejected"

            self._emit_event(
                SwapRejected(user.id, request.shift_id)
            )

            return OperationResult(True)

        except VolunteerSystemError as e:
            return OperationResult(False, str(e))
        except Exception as e:
            return OperationResult(False, f"[Critical] {e}")


    def update_ledger(self, member_id, required_hours=10):
        self.ledger.update_user(member_id, required_hours)
    

    def audit_all_shifts(self, user):
        """
        Daily audit: checks all shifts against end_date.
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




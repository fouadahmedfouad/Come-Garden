from datetime import datetime, timedelta
import uuid

from features.toolLibrary.tool_library_exceptions import (
    ToolLibraryError,
    InvalidUserError,
    ToolNotFoundError,
    InvalidDurationError,
    UserPenaltyError,
    ToolUnavailableError,
    BookingNotFoundError,
    ToolStateError,
    InvalidDamageSeverityError,
    AuthorizationError,
)
from features.toolLibrary.tool_library_info import (
    Tool,
    Booking,
    Penalty,
)

from features.toolLibrary.tool_library_results import (
    BookingResult,
    OperationResult,
    PenaltyResult,
    ToolResult
)

from features.toolLibrary.tool_library_events import *

class ToolLibrary:
    def __init__(self):
        self.tools = {}
        self.bookings = {}
        self.penalties = {}

        self.tasks  = []
        self.events = []

    def _emit_event(self, event):
        self.events.append(event)
        self._handle_event(event)
       
        ## future monitoring

    def _handle_event(self, event):

        # Overdue tracking
        if event.type == "tool_returned":
            if event.data.get("late"):
                print(f"[Alert] Late return by user {event.user_id}")
            self.process_waitlist(event.data.get("tool_name"))

        # Frequent penalties
        if event.type == "penalty_applied":
            user_penalties = self.penalties.get(event.user_id, [])
            if len(user_penalties) > 5:
                print(f"[Alert] Repeat offender: {event.user_id}")

        # Tool damage tracking
        if event.type == "tool_damaged":
            if event.data["severity"] == "high":
                print(f"[Critical] Tool {event.data['tool_name']} heavily damaged")

        #  Usage analytics (example)
        if event.type == "tool_booked":
            tool = self.tools.get(event.data["tool_name"])
            if tool and tool.total_usage_hours > tool.maintenance_threshold_hours:
                print(f"[Alert] Tool {tool.name} needs maintenance")

    def book_tool(self, user, tool_name, duration_hours) -> BookingResult:
        """
        Books a tool for a given user and duration.
        Handles availability, penalties, and waitlisting with robust error handling.
        """
        try:
            if not user or not hasattr(user, "id"):
                raise InvalidUserError(user)
    
            if not tool_name or not isinstance(tool_name, str):
                raise ToolNotFoundError(tool_name)
    
            if duration_hours <= 0:
                raise InvalidDurationError(duration_hours)
    
            tool = self.tools.get(tool_name)
            if not tool:
                raise ToolNotFoundError(tool_name)
    
            if self.has_pending_penalty(user.id):
                raise UserPenaltyError(user.id)
    
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
    
            if self.is_tool_available(tool_name, start_time, end_time):
                booking = Booking(tool.name, user.id, start_time, end_time)
    
                self.bookings[booking.id] = booking
                tool.check_out()
    
                user.bookings = getattr(user, "bookings", [])
                user.bookings.append(booking)

                self._emit_event(
                    ToolBooked(user.id, tool.name, booking.id)
                )
    
                return BookingResult(success=True, booking=booking)

            # --- Waitlist fallback ---
            score = self.calculate_priority(user.id)
            tool.waitlist.append((score, duration_hours, user))

            self._emit_event(
                ToolWaitlisted(user.id, tool_name)
            )

            return BookingResult(success=False, waitlisted=True,
                                 error=f"Tool '{tool_name}' unavailable from {start_time} to {end_time}")
    
        except ToolLibraryError as e:
            return BookingResult(success=False, error=str(e))
    
        except Exception as e:
            return BookingResult(success=False, error=f"[Critical] Unexpected failure: {e}")

    def return_tool(self, booking, cleaned=True) -> bool:

        """
        Handles tool return, penalties, and booking status updates.
        """
        try:

            if not self.bookings.get(booking.id):
                raise BookingNotFoundError(booking.id)
    
            tool = self.tools.get(booking.tool_name)
            if not tool:
                raise ToolStateError(booking.tool_name, "Tool not found in registry.")
    
            actual_return_date = datetime.now()
            required_return_time = booking.end_time

            booking.actual_return_date = actual_return_date
    
            if not cleaned:
                penalty = Penalty(booking.user_id, booking.id, "service", 2)
                self.penalties.append(penalty)
                booking.penalty_id = penalty.id

                self._emit_event(
                    PenaltyApplied(booking.user_id, penalty.type, severity)
                )
    
            hours_used = (actual_return_date - booking.start_time).total_seconds() / 3600
            late = actual_return_date > required_return_time

            if late:
                booking.status = "overdue"
            else:
                booking.status = "completed"
   
            tool.return_tool(hours_used)

            self._emit_event(
                ToolReturned(booking.user_id, booking.tool_name, late=late)
            )
            
            return OperationResult(success=True)
    
        except ToolLibraryError as e:
            return OperationResult(success=False, error=str(e))

        except Exception as e:
            return OperationResult(success=False, error=f"[Critical] Unexpected failure: {e}")
   
    def report_damage(self, booking, severity="medium") -> Penalty:
        """
        Reports damage for a booking and applies penalties based on severity.
        """
        try:
            if not self.bookings.get(booking.id):
                raise BookingNotFoundError(booking.id)
    
            tool = self.tools.get(booking.tool_name)
            if not tool:
                raise ToolStateError(booking.tool_name, "Tool not found in registry.")
    
            valid_severities = {"low", "medium", "high"}
            if severity not in valid_severities:
                raise InvalidDamageSeverityError(severity)
    
            if severity == "low":
                # Natural wear — no penalty
                return PenaltyResult(success=True, penalty=None)
    
            elif severity == "medium":
                penalty = Penalty(booking.user_id, booking.id, "service", 3)
                tool.mark_for_repair()
    
            elif severity == "high":
                penalty = Penalty(booking.user_id, booking.id, "fine", 50)
                tool.decommission()
    
            self.penalties.setdefault(booking.user_id, []).append(penalty)
            booking.penalty_id = penalty.id

            self._emit_event(
                ToolDamaged(booking.user_id, tool.name, severity)
            )

            self._emit_event(
                PenaltyApplied(booking.user_id, penalty.type, severity)
            )

            return PenaltyResult(success=True, penalty=penalty)

        except ToolLibraryError as e:
            return PenaltyResult(success=False, error=str(e))

        except Exception as e:
            return PenaltyResult(success=False, error=f"[Critical] Unexpected failure: {e}")

    def add_tool(self, user, tool_name, usage_status="low", maintenance_threshold_hours=5) -> Tool | None:
        """
        Admin-only: Adds a new tool to the system.
        """
        try:
            if not user or not user.is_admin:
                raise AuthorizationError(getattr(user, "id", None), "add_tool")
    
            if not tool_name or not isinstance(tool_name, str):
               raise ToolNotFoundError(tool_name)

            if tool_name in self.tools:
               raise ToolStateError(tool_name, "Tool already exists.")

            tool = Tool(tool_name, usage_status, maintenance_threshold_hours)
            self.tools[tool.name] = tool
    
            return ToolResult(success=True, tool=tool)

        except ToolLibraryError as e:
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            return ToolResult(success=False, error=f"[Critical] Unexpected failure: {e}")

    def calculate_priority(self, user_id):
        base_score = 100
        user_penalties = self.penalties.get(user_id, [])
        now = datetime.now()
    
        penalty_weight = {
            "service": 5,
            "fine": 20
        }

        total_penalty_score = 0
    
        for p in user_penalties:
            weight = penalty_weight.get(p.type, 10)
    
            # decay old penalties (for fairness)
            days_ago = (now - p.created_at).days if hasattr(p, "created_at") else 0
            
            if days_ago > 30:
                weight *= 0.5  
    
            total_penalty_score += weight
    
        return max(base_score - total_penalty_score, 0)


    def is_tool_available(self, tool_name, requested_start,requested_end):
        tool = self.tools.get(tool_name)

        if not tool:
           raise ToolNotFoundError(tool_name)

        if tool.status != "available":
            return False

        for booking in self.bookings.values():
            if booking.tool_name != tool_name:
                continue

            if booking.status in {"active", "overdue"}:
                if not (requested_end <= booking.start_time or requested_start >= booking.end_time):
                    return False
        return True

    def process_waitlist(self, tool_name):
        try:
            tool = self.tools.get(tool_name)

            if not tool: 
                raise ToolNotFoundError(tool_name)
        
            if tool.status != "available" or not tool.waitlist:
                return None
        
            # Sort by priority
            tool.waitlist.sort(key=lambda x: x[0], reverse=True)
        
            start_time = datetime.now()
            for i, (score, duration, user) in enumerate(tool.waitlist):
        
                if self.has_pending_penalty(user.id):
                    continue
        
                end_time = start_time + timedelta(hours=duration)
        
                if not self.is_tool_available(tool_name, start_time, end_time):
                    continue
        
                result = self.book_tool(user, tool_name, duration)

                if result.success:
                    tool.waitlist.pop(i)
                    return result
                    
        
            return None 

        except ToolLibraryError:
                return None

        except Exception:
            return None

    def has_pending_penalty(self, user_id):
        return any(p.status == "pending" for p in self.penalties.get(user_id, []))



    def daily_audit(self):
        """
        Processes the waitlist for all available tools in the library.
        Intended to run once per day to ensure waitlists are handled.
        """
        for tool_name, tool in self.tools.items():
            if tool.status == "available" and tool.waitlist:
                try:
                    self.process_waitlist(tool_name)
                except Exception:
                    # optionally log here
                    pass

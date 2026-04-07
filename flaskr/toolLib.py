from datetime import datetime, timedelta
import uuid

from exceptions import (
    ToolLibraryError,
    InvalidUserError,
    ToolNotFoundError,
    InvalidDurationError,
    UserPenaltyError,
    ToolUnavailableError,
    BookingNotFoundError,
    ToolStateError,
    InvalidDamageSeverityError,
    AuthorizationError
)


class Tool:
    def __init__(self, tool_name, usage_status, maintenance_threshold_hours=50):
        self.name = tool_name
        self.status = "available"
        self.usage_status = usage_status
        self.maintenance_threshold = maintenance_threshold_hours
        self.total_usage_hours = 0
        self.waitlist = []
        self.resources = []

    def check_out(self):
        if self.status != "available":
            raise ValueError("Tool not available")
        self.status = "checked_out"

    def return_tool(self, hours_used):
        self.total_usage_hours += hours_used

        if self.total_usage_hours >= self.maintenance_threshold:
            self.status = "in_repair"
        else:
            self.status = "available"

    def repair(self):
        self.status = "available"
        self.total_usage_hours = 0

    def mark_for_repair(self):
        if self.status == "decommissioned":
            raise ValueError("Cannot repair decommissioned tool")
        self.status = "in_repair"

    def decommission(self):
        self.status = "decommissioned"

class Booking:
    def __init__(self, tool_name, user_id, start_time, end_time):
        self.id = str(uuid.uuid4())
        self.tool_name = tool_name
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.actual_return_time = None
        self.status = "in_use"
        self.penalty_id = None

class Penalty:
    def __init__(self, user_id, booking_id, type_, amount):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.booking_id = booking_id
        self.type = type_  # fine or service
        self.amount = amount
        self.status = "pending"
        self.created_at = datetime.now()


class ToolLibrary:
    def __init__(self):
        self.tools = {}
        self.bookings = []
        self.penalties = {}
        self.tasks = []

    def book_tool(self, user, tool_name, duration_hours):
        """
        Books a tool for a given user and duration.
        Handles availability, penalties, and waitlisting with robust error handling.
        """
        try:
            # --- Input validation ---
            if not user or not hasattr(user, "id"):
                raise InvalidUserError(user)
    
            if not tool_name or not isinstance(tool_name, str):
                raise ToolNotFoundError(tool_name)
    
            if duration_hours <= 0:
                raise InvalidDurationError(duration_hours)
    
            tool = self.tools.get(tool_name)
            if not tool:
                raise ToolNotFoundError(tool_name)
    
            # --- Business rules ---
            if self.has_pending_penalty(user.id):
                raise UserPenaltyError(user.id)
    
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
    
            # --- Booking logic ---
            if self.is_tool_available(tool_name, start_time, end_time):
                booking = Booking(tool.name, user.id, start_time, end_time)
    
                self.bookings.append(booking)
                tool.check_out()
    
                # Attach booking safely
                user.booking_ids = getattr(user, "booking_ids", [])
                user.booking_ids.append(booking.id)
    
                return booking
    
            # --- Waitlist fallback ---
            score = self.calculate_priority(user.id)
            tool.waitlist.append((score, duration_hours, user))
    
            # Raise AFTER side-effect (important design)
            raise ToolUnavailableError(tool_name, start_time, end_time)
    
        except ToolLibraryError as e:
            # Known domain errors (clean + meaningful)
            print(f"[ToolLibraryError] {e}")
            return None
    
        except Exception as e:
            # Unexpected system errors
            print(f"[Critical] Unexpected failure in booking system: {e}")
            return None

    def return_tool(self, booking_id, cleaned=True):
        """
        Handles tool return, penalties, and booking status updates.
        """
        try:

            booking = next((b for b in self.bookings if b.id == booking_id), None)
            if not booking:
                raise BookingNotFoundError(booking_id)
    
            tool = self.tools.get(booking.tool_name)
            if not tool:
                raise ToolStateError(booking.tool_name, "Tool not found in registry.")
    
            actual_return_time = datetime.now()
            required_return_time = booking.end_time
    
            # --- Penalty handling ---
            if not cleaned:
                penalty = Penalty(booking.user_id, booking.id, "service", 2)
                self.penalties.append(penalty)
                booking.penalty_id = penalty.id
    
            # --- Status update ---
            if actual_return_time > required_return_time:
                booking.status = "overdue"
            else:
                booking.status = "completed"
    
            hours_used = (actual_return_time - booking.start_time).total_seconds() / 3600
    
            tool.return_tool(hours_used)
            self.process_waitlist(tool.name)

            return True
    
        except ToolLibraryError as e:
            print(f"[ToolLibraryError] {e}")
            return False
    
        except Exception as e:
            print(f"[Critical] Unexpected failure during tool return: {e}")
            return False   


    def report_damage(self, booking_id, severity="medium"):
        """
        Reports damage for a booking and applies penalties based on severity.
        """
        try:
            # --- Validate booking ---
            booking = next((b for b in self.bookings if b.id == booking_id), None)
            if not booking:
                raise BookingNotFoundError(booking_id)
    
            tool = self.tools.get(booking.tool_name)
            if not tool:
                raise ToolStateError(booking.tool_name, "Tool not found in registry.")
    
            # --- Validate severity ---
            valid_severities = {"low", "medium", "high"}
            if severity not in valid_severities:
                raise InvalidDamageSeverityError(severity)
    
            # --- Business logic ---
            if severity == "low":
                # Natural wear — no penalty
                return None
    
            elif severity == "medium":
                penalty = Penalty(booking.user_id, booking.id, "service", 3)
                tool.mark_for_repair()
    
            elif severity == "high":
                penalty = Penalty(booking.user_id, booking.id, "fine", 50)
                tool.decommission()
    
            # --- Apply penalty ---
            self.penalties.setdefault(booking.user_id, []).append(penalty)
            booking.penalty_id = penalty.id
    
            return penalty

        except ToolLibraryError as e:
            print(f"[ToolLibraryError] {e}")
            return None
    
        except Exception as e:
            print(f"[Critical] Unexpected failure during damage report: {e}")
            return None   

    def add_tool(self, user, tool_name, usage_status="low", maintenance_threshold_hours=5):
        """
        Admin-only: Adds a new tool to the system.
        """
        try:
            # --- Authorization ---
            if not user or not user.is_admin:
                raise AuthorizationError(getattr(user, "id", None), "add_tool")
    
            # --- Validation ---
            if not tool_name or not isinstance(tool_name, str):
                raise ValueError("Tool name must be a valid string.")
    
            if tool_name in self.tools:
                raise ValueError(f"Tool '{tool_name}' already exists.")
    
            # --- Create tool ---
            tool = Tool(tool_name, usage_status, maintenance_threshold_hours)
            self.tools[tool.name] = tool
    
            return tool

        except ToolLibraryError as e:
            print(f"[ToolLibraryError] {e}")
            return None
    
        except Exception as e:
            print(f"[Critical] Failed to add tool: {e}")
            return None 

    def calculate_priority(self, user_id):
        base_score = 100
        user_penalties = self.penalties.get(user_id, [])
    
        penalty_weight = {
            "service": 5,
            "fine": 20
        }

        total_penalty_score = 0
    
        for p in user_penalties:
            weight = penalty_weight.get(p.type, 10)
    
            # decay old penalties (for fairness)
            days_ago = (datetime.now() - p.created_at).days if hasattr(p, "created_at") else 0
            
            if days_ago > 30:
                weight *= 0.5  # older penalties matter less
    
            total_penalty_score += weight
    
        score = base_score - total_penalty_score

        return max(score, 0)


    def is_tool_available(self, tool_name, requested_start,requested_end):
        tool = self.tools.get(tool_name)

        if not tool or tool.status != "available":
            return False

        for booking in self.bookings:
            if booking.tool_name != tool_name:
                continue

            if booking.status in {"active", "overdue"}:
                # Check time overlap
                if not (requested_end <= booking.start_time or requested_start >= booking.end_time):
                    return False
        return True

    def has_pending_penalty(self, user_id):
        for p in self.penalties.get(user_id, []):
            if p.status == "pending":
                return True
        return False

    def process_waitlist(self, tool_name):
        tool = self.tools.get(tool_name)
    
        if not tool or tool.status != "available" or not tool.waitlist:
            return
    
        # Sort ONLY by score (highest first)
        tool.waitlist.sort(key=lambda x: x[0], reverse=True)
    
        for i, (score, duration, user) in enumerate(tool.waitlist):
    
            if self.has_pending_penalty(user.id):
                continue
    
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration)
    
            if not self.is_tool_available(tool_name, start_time, end_time):
                continue
    
            booking = self.book_tool(user, tool_name, duration)
    
            tool.waitlist.pop(i)
            return booking  


    def daily_audit(self):
        """
        Processes the waitlist for all available tools in the library.
        Intended to run once per day to ensure waitlists are handled.
        """
        for tool_name, tool in self.tools.items():
            if tool.status == "available" and tool.waitlist:
                self.process_waitlist(tool_name)

from datetime import datetime, timedelta
import uuid


class Tool:
    def __init__(self, tool_name, usage_status, maintenance_threshold_hours=50):
        self.tool_name = tool_name
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


class VolunteerTask:
    def __init__(self, user_id, hours_required, source, related_penalty_id=None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.hours_required = hours_required
        self.hours_completed = 0
        self.source = source
        self.related_penalty_id = related_penalty_id


class ToolLibrary:
    def __init__(self):
        self.tools = {}
        self.bookings = []
        self.penalties = []
        self.tasks = []

    def is_tool_available(self, tool_name, requested_start,requested_end):
        tool = self.tools.get(tool_name)

        if not tool or tool.status != "available":
            return False

        for booking in self.bookings:
            if booking.tool_name != tool_name:
                continue

            if booking.status != "completed":
                # Check time overlap
                if not (requested_end <= booking.start_time or requested_start >= booking.end_time):
                    return False

        return True

    def add_tool(self, tool_name, usage_status="low", maintenance_threshold_hours=5):
        tool = Tool(tool_name,usage_status,maintenance_threshold_hours)
        self.tools[tool.tool_name] = tool


    def _book_tool(self, tool_name, user_id, start_time, end_time):
        tool = self.tools.get(tool_name)
        booking = Booking(tool_name, user_id, start_time, end_time)
        self.bookings.append(booking)
        tool.check_out()
        return booking.id
 
    def book_tool(self, tool_name, user_id, duration_hours):
        tool = self.tools.get(tool_name)

        if self.has_pending_penalty(user_id):
            print("User blocked due to pending penalty")
            return None


        start_time = datetime.now()
        end_time   = start_time + timedelta(hours=duration_hours)

        if self.is_tool_available(tool_name, start_time, end_time):
            return self._book_tool(tool_name, user_id, start_time, end_time)

        # Otherwise 
        score = self.calculate_priority(user_id)
        tool.waitlist.append((score, user_id, duration_hours))

        return None

    def report_damage(self, booking_id, severity="medium"):
        booking = next((b for b in self.bookings if b.id == booking_id), None)
        tool = self.tools[booking.tool_name]

        if not booking:
            return None

        # Simple logic
        if severity == "low":
            return None  # natural wear

        elif severity == "medium":
            penalty = Penalty(booking.user_id, booking.id, "service", 3)
            tool.mark_for_repair()

        else:
            penalty = Penalty(booking.user_id, booking.id, "fine", 50)
            tool.decommission() # or in repair a well

        self.penalties.append(penalty)
        booking.penalty_id = penalty.id

        # # Create volunteer task if service
        # if penalty.type == "service":
        #     task = VolunteerTask(booking.user_id, penalty.amount, "penalty", penalty.id) # TODO: later change this to a record and add the task.
        #     self.tasks.append(task)


        return penalty

    def return_tool(self, booking_id, cleaned=True):
        booking = next((b for b in self.bookings if b.id == booking_id), None)

        if not booking:
            return False

        tool = self.tools[booking.tool_name]

        actual_return_time = datetime.now()
        required_return_time = booking.end_time


        ## TODO: QR Code
        if not cleaned:
            penalty = Penalty(booking.user_id, booking.id, "service", 2)
            self.penalties.append(penalty)
            booking.penalty_id = penalty.id


        if tool.usage_status == "high" and actual_return_time > required_return_time:
            booking.status = "overdue"
        else:
            booking.status = "completed"

        hours_used = (booking.start_time - actual_return_time).total_seconds() / 3600
        tool.return_tool(hours_used)

        return True
    
    def calculate_priority(self, user_id):
        # Example:
        # Could include:
        # - contribution points
        # - past tool usage
        return 100  # placeholder

    ## TODO: Resolve penality
    def has_pending_penalty(self, user_id):
        return any(p.user_id == user_id and p.status == "pending" for p in self.penalties)
    
    def process_waitlist(self, tool_name):
        tool = self.tools.get(tool_name)
    
        if not tool or tool.status != "available" or not tool.waitlist:
            return
    
        tool.waitlist.sort(reverse=True)
    
        for i, (_, user_id, duration) in enumerate(tool.waitlist):
    
            if self.has_pending_penalty(user_id):
                continue
    
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration)
    
            if not self.is_tool_available(tool_name, start_time, end_time):
                continue

            self._book_tool(tool_name, user_id, start_time, end_time)
            tool.waitlist.pop(i)
            break
        







# if __name__ == "__main__":
#     lib = ToolLibrary()

#     # Add tool
#     tool = Tool("T1", "Rototiller", "high", maintenance_threshold_hours=5)
#     lib.tools[tool.tool_name] = tool

#     # User books tool
#     booking = lib.book_tool("T1", "Alice", 2)

#     # Return tool (not cleaned → penalty)
#     lib.return_tool(booking.id, hours_used=2, cleaned=False)

#     # Report damage
#     penalty = lib.report_damage(booking.id, severity="high")

#     print("Penalties:")
#     for p in lib.penalties:
#         print(vars(p))

#     print("Volunteer Tasks:")
#     for t in lib.tasks:
#         print(vars(t))

#     print("Tool Status:", tool.status)



# if __name__ == "__main__":
#     lib = ToolLibrary()

#     # Add tool
#     tool = Tool("Rototiller", usage_status="high", maintenance_threshold_hours=5)
#     lib.tools[tool.tool_name] = tool

#     print("\n--- Initial Booking ---")
#     b1 = lib.book_tool("Rototiller", "Alice", 2)
#     print("Alice booked:", b1)

#     print("\n--- Conflict Booking (goes to waitlist) ---")
#     b2 = lib.book_tool("Rototiller", "Bob", 2)
#     print("Bob booked:", b2)
#     print("Waitlist:", tool.waitlist)

#     print("\n--- Return Tool ---")
#     booking_obj = lib.bookings[0]
#     lib.return_tool(booking_obj.id, hours_used=2)

#     print("Tool status after return:", tool.status)

#     print("\n--- Process Waitlist ---")
#     lib.process_waitlist("Rototiller")

#     print("Bookings after waitlist processing:")
#     for b in lib.bookings:
#         if b.user_id != "Alice":
#             print(vars(b))

#     print("\n--- Damage Reporting ---")
#     last_booking = lib.bookings[-1]
#     penalty = lib.report_damage(last_booking.id, severity="medium")
#     print("Penalty:", vars(penalty))
#     print("Tool status:", tool.status)

#     print("\n--- Try Booking with Penalty ---")
#     lib.book_tool("Rototiller", "Bob", 1)

#     print("\n--- Final State ---")
#     print("Tool:", vars(tool))
#     print("Penalties:")
#     for p in lib.penalties:
#         print(vars(p))

#     print("Tasks:")
#     for t in lib.tasks:
#         print(vars(t))

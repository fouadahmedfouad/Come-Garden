from datetime import datetime, timedelta
import uuid

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


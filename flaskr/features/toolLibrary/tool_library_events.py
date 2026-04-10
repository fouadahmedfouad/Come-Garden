from datetime import datetime

class LibraryEvent:
    def __init__(self, event_type, user_id=None, **data):
        self.type = event_type
        self.user_id = user_id
        self.timestamp = datetime.utcnow()
        self.data = data

class ToolBooked(LibraryEvent):
    def __init__(self, user_id, tool_name, booking_id):
        super().__init__(
            "tool_booked",
            user_id,
            tool_name=tool_name,
            booking_id=booking_id
        )


class ToolWaitlisted(LibraryEvent):
    def __init__(self, user_id, tool_name):
        super().__init__(
            "tool_waitlisted",
            user_id,
            tool_name=tool_name
        )


class ToolReturned(LibraryEvent):
    def __init__(self, user_id, tool_name, late=False):
        super().__init__(
            "tool_returned",
            user_id,
            tool_name=tool_name,
            late=late
        )


class PenaltyApplied(LibraryEvent):
    def __init__(self, user_id, penalty_type, severity):
        super().__init__(
            "penalty_applied",
            user_id,
            penalty_type=penalty_type,
            severity=severity
        )


class ToolDamaged(LibraryEvent):
    def __init__(self, user_id, tool_name, severity):
        super().__init__(
            "tool_damaged",
            user_id,
            tool_name=tool_name,
            severity=severity
        )

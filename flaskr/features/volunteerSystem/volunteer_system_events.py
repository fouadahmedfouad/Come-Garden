from datetime import datetime

class VolunteerEvent:
    def __init__(self, event_type, user_id=None, **data):
        self.type = event_type
        self.user_id = user_id
        self.timestamp = datetime.utcnow()
        self.data = data


class MemberAdded(VolunteerEvent):
    def __init__(self, user_id, required_hours):
        super().__init__(
            "member_added",
            user_id,
            required_hours=required_hours
        )


class ShiftCreated(VolunteerEvent):
    def __init__(self, user_id, shift_id, rescheduled=False, weather=None):
        super().__init__(
            "shift_created",
            user_id,
            shift_id=shift_id,
            rescheduled=rescheduled,
            weather=weather
        )


class MembersAssigned(VolunteerEvent):
    def __init__(self, user_id, shift_id, count):
        super().__init__(
            "members_assigned",
            user_id,
            shift_id=shift_id,
            count=count
        )


class ShiftCompleted(VolunteerEvent):
    def __init__(self, user_id, shift_id):
        super().__init__(
            "shift_completed",
            user_id,
            shift_id=shift_id
        )


class SwapRequested(VolunteerEvent):
    def __init__(self, user_id, target_id, shift_id):
        super().__init__(
            "swap_requested",
            user_id,
            target_id=target_id,
            shift_id=shift_id
        )


class SwapApproved(VolunteerEvent):
    def __init__(self, user_id, shift_id):
        super().__init__(
            "swap_approved",
            user_id,
            shift_id=shift_id
        )


class SwapRejected(VolunteerEvent):
    def __init__(self, user_id, shift_id):
        super().__init__(
            "swap_rejected",
            user_id,
            shift_id=shift_id
        )

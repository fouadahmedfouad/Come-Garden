class VolunteerSystemError(Exception):
    pass


class InvalidUserError(VolunteerSystemError):
    def __init__(self, user):
        super().__init__(f"Invalid user: {user}")


class AuthorizationError(VolunteerSystemError):
    def __init__(self, user_id, action):
        super().__init__(f"User {user_id} not authorized for {action}")


class ShiftNotFoundError(VolunteerSystemError):
    def __init__(self, shift_id):
        super().__init__(f"Shift not found: {shift_id}")


class AssignmentError(VolunteerSystemError):
    def __init__(self, message):
        super().__init__(message)


class SwapRequestError(VolunteerSystemError):
    def __init__(self, message):
        super().__init__(message)



## Garden Exceptions
class PermissionDeniedError(Exception):
    pass

## Rental Excpetions
class RentalError(Exception):
    pass

class MemberNotFoundError(RentalError):
    pass

class PlotNotFoundError(RentalError):
    pass

class InvalidShareError(RentalError):
    pass

class InsufficientCreditsError(RentalError):
    pass

class DuplicateParticipantError(RentalError):
    pass




## Plot Excptions
class PlotError(Exception):
    pass

class MemberNotInPlot(PlotError):
    pass




## Tool Library
class ToolLibraryError(Exception):
    """Base exception for all tool library errors."""
    pass


class InvalidUserError(ToolLibraryError):
    def __init__(self, user):
        super().__init__(f"Invalid user provided: {user}")


class ToolNotFoundError(ToolLibraryError):
    def __init__(self, tool_name):
        super().__init__(f"Tool '{tool_name}' does not exist.")


class InvalidDurationError(ToolLibraryError):
    def __init__(self, duration):
        super().__init__(f"Invalid duration: {duration}. Must be > 0.")


class UserPenaltyError(ToolLibraryError):
    def __init__(self, user_id):
        super().__init__(f"User {user_id} is blocked due to a pending penalty.")


class ToolUnavailableError(ToolLibraryError):
    def __init__(self, tool_name, start_time, end_time):
        super().__init__(
            f"Tool '{tool_name}' is unavailable from {start_time} to {end_time}."
        )


class BookingNotFoundError(ToolLibraryError):
    def __init__(self, booking_id):
        super().__init__(f"Booking with ID '{booking_id}' was not found.")


class ToolStateError(ToolLibraryError):
    def __init__(self, tool_name, message):
        super().__init__(f"Tool '{tool_name}' state error: {message}")

class InvalidDamageSeverityError(ToolLibraryError):
    def __init__(self, severity):
        super().__init__(
            f"Invalid damage severity '{severity}'. Must be one of: low, medium, high."
        )

class AuthorizationError(ToolLibraryError):
    def __init__(self, user_id, action):
        super().__init__(f"User {user_id} is not authorized to perform '{action}'.")
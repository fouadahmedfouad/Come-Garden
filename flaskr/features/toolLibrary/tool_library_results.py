class BookingResult:
    def __init__(self, success: bool, booking=None, waitlisted=False, error=None):
        self.success = success
        self.booking = booking          
        self.waitlisted = waitlisted   
        self.error = error           

class OperationResult:
    def __init__(self, success: bool, error: str = None):
        self.success = success
        self.error = error


class PenaltyResult(OperationResult):
    def __init__(self, success: bool, penalty=None, error: str = None):
        super().__init__(success, error)
        self.penalty = penalty


class ToolResult(OperationResult):
    def __init__(self, success: bool, tool=None, error: str = None):
        super().__init__(success, error)
        self.tool = tool


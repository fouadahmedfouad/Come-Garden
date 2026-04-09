class OperationResult:
    def __init__(self, success: bool, error: str = None):
        self.success = success
        self.error = error


class ShiftResult(OperationResult):
    def __init__(self, success: bool, shift=None, error=None):
        super().__init__(success, error)
        self.shift = shift


class AssignmentResult(OperationResult):
    def __init__(self, success: bool, assignments=None, error=None):
        super().__init__(success, error)
        self.assignments = assignments


class SwapResult(OperationResult):
    def __init__(self, success: bool, request=None, error=None):
        super().__init__(success, error)
        self.request = request


class OperationResult:
    def __init__(self, success: bool, error: str = None):
        self.success = success
        self.error = error

class ApplicationResult(OperationResult):
    def __init__(self, success, application=None, error=None):
        super().__init__(success, error)
        self.application = application


class RentalResult(OperationResult):
    def __init__(self, success: bool, rental=None, waitlisted=False, error=None):
        super().__init__(success, error)
        self.rental = rental
        self.waitlisted = waitlisted


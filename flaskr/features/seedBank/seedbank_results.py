
class OperationResult:
    def __init__(self, success: bool, error: str = None):
        self.success = success
        self.error = error


class DepositResult(OperationResult):
    def __init__(self, success: bool, batch=None, credits_added=0, error=None):
        super().__init__(success, error)
        self.batch = batch
        self.credits_added = credits_added

class WithdrawResult(OperationResult):
    def __init__(self, success: bool, batches=None, credits_used=0, error=None):
        super().__init__(success, error)
        self.batches = batches or []
        self.credits_used = credits_used

class InventoryResult(OperationResult):
    def __init__(self, success: bool, item=None, error=None):
        super().__init__(success, error)
        self.item = item

class HealthCheckResult:
    def __init__(self, success: bool, alerts=None, error=None):
        super().__init__(success, error)
        self.alerts = alerts or []



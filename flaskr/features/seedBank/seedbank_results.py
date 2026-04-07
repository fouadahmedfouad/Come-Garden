
class DepositResult:
    def __init__(self, success: bool, batch=None, credits_added=0, error=None):
        self.success = success
        self.batch = batch
        self.credits_added = credits_added
        self.error = error

class WithdrawResult:
    def __init__(self, success: bool, batches=None, credits_used=0, error=None):
        self.success = success
        self.batches = batches or []
        self.credits_used = credits_used
        self.error = error

class InventoryResult:
    def __init__(self, success: bool, item=None, error=None):
        self.success = success
        self.item = item
        self.error = error

class HealthCheckResult:
    def __init__(self, success: bool, alerts=None, error=None):
        self.success = success
        self.alerts = alerts or []
        self.error = error



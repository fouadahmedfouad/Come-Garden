
# --- Domain Errors ---
class SeedBankError(Exception): pass

class InvalidUserError(SeedBankError):
    def __init__(self, user):
        super().__init__(f"Invalid user provided: {user}")

class SeedTypeNotFoundError(SeedBankError):
    def __init__(self, seed_type):
        super().__init__(f"Seed type '{seed_type}' not found.")

class InsufficientCreditsError(SeedBankError):
    def __init__(self, user_id, required, available):
        super().__init__(f"User {user_id} has insufficient credits ({available}/{required})")

class AdminRequiredError(SeedBankError):
    def __init__(self, action):
        super().__init__(f"Admin privileges required for: {action}")



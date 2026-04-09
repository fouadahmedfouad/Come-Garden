from datetime import datetime

class BaseEvent:
    def __init__(self, event_type: str):
        self.type = event_type
        self.timestamp = datetime.now()


class SeedDeposited(BaseEvent):
    def __init__(self, user_id, seed_type, quantity, viability, origin):
        super().__init__("seed_deposited")
        self.user_id = user_id
        self.seed_type = seed_type
        self.quantity = quantity
        self.viability = viability
        self.origin = origin


class SeedWithdrawn(BaseEvent):
    def __init__(self, user_id, seed_type, quantity):
        super().__init__("seed_withdrawn")
        self.user_id = user_id
        self.seed_type = seed_type
        self.quantity = quantity


class InventoryAdded(BaseEvent):
    def __init__(self, item_name, quantity):
        super().__init__("inventory_added")
        self.item_name = item_name
        self.quantity = quantity




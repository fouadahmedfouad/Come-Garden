
class SeedInfo:
    def __init__(self, viability, age, gt_flag=False, parent_plant=None, lah=False, resources=None):
        self.viability = viability
        self.age = age
        self.gt_flag = gt_flag
        self.parent_plant = parent_plant
        self.lah = lah
        self.resources = resources or []


class SeedBatch: 
    EXPIRE_AGE = 24
    GT_THRESHOLD = 70

    def __init__(self, seed_type, quantity, info: SeedInfo, created_at=None):
        self.seed_type = seed_type
        self.quantity = quantity
        self.info = info
        self.created_at = created_at or datetime.now()

    def is_expired(self):
        return self.info.age > self.EXPIRE_AGE

    def needs_testing(self):
        return self.info.gt_flag or self.info.viability < self.GT_THRESHOLD

    def __repr__(self):
        return f"{self.seed_type} | qty={self.quantity} | age={self.info.age} | viability={self.info.viability}"

# Inventory (Non-seed items)
class InventoryItem:
    def __init__(self, name, quantity, reorder_threshold):
        self.name = name
        self.quantity = quantity
        self.reorder_threshold = reorder_threshold

    def needs_reorder(self):
        return self.quantity <= self.reorder_threshold

    def __repr__(self):
        return f"{self.name} (qty={self.quantity})"


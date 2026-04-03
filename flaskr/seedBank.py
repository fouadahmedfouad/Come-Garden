from datetime import datetime
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

class SeedBank:
    HIGH_QUALITY_THRESHOLD = 80

    def __init__(self):
        self.seeds = {}  # { seed_type: [SeedBatch] }
        self.inventory_items = {}
        self.transactions = []
        self.member_balances = {}

    def deposit(self, member_id, batch: SeedBatch):
        self.seeds.setdefault(batch.seed_type, []).append(batch)

        # Reward only high-quality seeds
        if batch.info.viability >= self.HIGH_QUALITY_THRESHOLD:
            self.member_balances[member_id] = self.member_balances.get(member_id, 0) + batch.quantity

        self.transactions.append(("deposit", member_id, batch.seed_type, batch.quantity))

    # Withdraw (2:1 ratio)
    def withdraw(self, member_id, seed_type, quantity):
        if seed_type not in self.seeds:
            return None
    
        required_credit = quantity / 2
    
        if self.member_balances.get(member_id, 0) < required_credit:
            return None
    
        batches = sorted(self.seeds[seed_type], key=lambda b: b.info.age, reverse=True)
    
        taken = 0
        taken_batches = []
    
        for batch in batches:
            if taken >= quantity:
                break
    
            take = min(batch.quantity, quantity - taken)
            batch.quantity -= take
            taken += take
    
            taken_batches.append({
                "seed_type": seed_type,
                "quantity": take,
                "age": batch.info.age
            })
    
        self.seeds[seed_type] = [b for b in batches if b.quantity > 0]
    
        self.member_balances[member_id] -= required_credit
        self.transactions.append(("withdraw", member_id, seed_type, taken))
    
        return {
            "seed_type": seed_type,
            "total_taken": taken,
            "batches": taken_batches
        }
    
    # Seed Health Check
    def check_seed_health(self):
        alerts = []

        for seed_type, batches in self.seeds.items():
            for batch in batches:
                if batch.is_expired():
                    alerts.append((seed_type, "EXPIRED"))

                elif batch.needs_testing():
                    alerts.append((seed_type, "TEST_REQUIRED"))

        return alerts


    # Inventory
    def add_inventory_item(self, item: InventoryItem):
        self.inventory_items[item.name] = item

    def check_inventory_alerts(self):
        alerts = []

        for item in self.inventory_items.values():
            if item.needs_reorder():
                alerts.append(item.name)

        return alerts


    # Debug / Display
    def print_state(self):
        print("\n Seed Bank State")
        for seed_type, batches in self.seeds.items():
            print(f"{seed_type}: {batches}")

        print("\n Member Balances:", self.member_balances)
        print("\n Inventory:", self.inventory_items)
        print("\n Transactions:", self.transactions)

    def create_batchInfo(self, viability, age, gt_flag, parent_plant, lah=True):
        info = SeedInfo(viability, age, gt_flag, parent_plant, lah)
        return info

    def create_batch(self, seed_type, quantity, info: SeedInfo):
        created_at = datetime.now()
        batch = SeedBatch(seed_type, quantity, info, created_at)
        return batch


# # -----------------------------
# # TEST SCENARIO
# # -----------------------------
# if __name__ == "__main__":
#     bank = SeedBank()

#     # Members
#     member1 = "Alice"
#     member2 = "Bob"

#     # Seed batches
#     tomato_batch = SeedBatch(
#         "Tomato",
#         quantity=10,
#         info=SeedInfo(viability=90, age=5, parent_plant="Roma", lah=True)
#     )

#     old_carrot_batch = SeedBatch(
#         "Carrot",
#         quantity=8,
#         info=SeedInfo(viability=60, age=30)  # expired + low viability
#     )

#     lettuce_batch = SeedBatch(
#         "Lettuce",
#         quantity=6,
#         info=SeedInfo(viability=75, age=10)
#     )

#     # -------------------------
#     # Deposits
#     # -------------------------
#     print("\n--- Deposits ---")
#     bank.deposit(member1, tomato_batch)
#     bank.deposit(member2, old_carrot_batch)
#     bank.deposit(member1, lettuce_batch)

#     bank.print_state()

#     # -------------------------
#     # Withdraw
#     # -------------------------
#     print("\n--- Withdraw ---")
#     success = bank.withdraw(member1, "Tomato", 4)
#     print("Withdraw success:", success)

#     bank.print_state()

#     # -------------------------
#     # Seed Health Check
#     # -------------------------
#     print("\n--- Seed Health Alerts ---")
#     alerts = bank.check_seed_health()
#     for alert in alerts:
#         print(alert)

#     # -------------------------
#     # Inventory
#     # -------------------------
#     print("\n--- Inventory ---")
#     fertilizer = InventoryItem("Fertilizer", quantity=5, reorder_threshold=10)
#     mulch = InventoryItem("Mulch", quantity=20, reorder_threshold=5)

#     bank.add_inventory_item(fertilizer)
#     bank.add_inventory_item(mulch)

#     alerts = bank.check_inventory_alerts()
#     print("Reorder Alerts:", alerts)

#     bank.print_state()

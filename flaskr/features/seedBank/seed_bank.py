from datetime import datetime
from features.seedBank.seedbank_results import (
    DepositResult,
    WithdrawResult,
    InventoryResult,
    HealthCheckResult
)

from features.seedBank.seedbank_info import (
    SeedInfo,
    SeedBatch,
    InventoryItem
)

from features.seedBank.seedbank_exceptions import (
    SeedBankError,
    InvalidUserError,
    SeedTypeNotFoundError,
    InsufficientCreditsError,
    AdminRequiredError
)


from features.seedBank.seedbank_events import (
    SeedDeposited,
    SeedWithdrawn,
    InventoryAdded
)

class SeedBank:
    HIGH_QUALITY_THRESHOLD = 80

    def __init__(self):
        self.seeds = {}
        self.inventory_items = {}
        self.members_balance = {}

        self.events = []

    def _emit_event(self, event):
        self.events.append(event)
        self._handle_event(event)

        ## future monitoring

    def _handle_event(self, event):
        ## ALERTS 
        if event.type == "seed_withdrawn" and event.quantity > 50:
            print(f"[Alert] Large withdrawal by user {event.user_id}")


    def deposit(self, user, seed_type, quantity, viability, origin, gt_flag, age, lah=True) -> DepositResult:
        try:
            if not user or not hasattr(user, "id"):
                raise InvalidUserError(user)

            info = SeedInfo(viability, age, gt_flag, origin, lah)
            batch = SeedBatch(seed_type, quantity, info, datetime.now())

            self.seeds.setdefault(seed_type, []).append(batch)

            credits_added = 0
            if viability >= self.HIGH_QUALITY_THRESHOLD:
                self.members_balance[user.id] = self.members_balance.get(user.id, 0) + quantity
                credits_added = quantity

            self._emit_event(
                SeedDeposited(user.id, seed_type, quantity, viability, origin)
            )

            return DepositResult(success=True, batch=batch, credits_added=credits_added)

        except SeedBankError as e:
            return DepositResult(success=False, error=str(e))

        except Exception as e:
            return DepositResult(success=False, error=f"[Critical] Unexpected failure: {e}")

    def withdraw(self, user, seed_type, quantity) -> WithdrawResult:
        try:
            if not user or not hasattr(user, "id"):
                raise InvalidUserError(user)

            if seed_type not in self.seeds:
                raise SeedTypeNotFoundError(seed_type)

            required_credit = quantity / 2
            available_credit = self.members_balance.get(user.id, 0)

            if available_credit < required_credit:
                raise InsufficientCreditsError(user.id, required_credit, available_credit)

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

            self.members_balance[user.id] -= required_credit

            user.inventory = getattr(user, "inventory", [])
            user.inventory.extend(taken_batches)

            self._emit_event(
                SeedWithdrawn(user.id, seed_type, taken)
            )

            return WithdrawResult(
                success=True,
                batches=taken_batches,
                credits_used=required_credit
            )

        except SeedBankError as e:
            return WithdrawResult(success=False, error=str(e))

        except Exception as e:
            return WithdrawResult(success=False, error=f"[Critical] Unexpected failure: {e}")


    def add_inventory_item(self, user, item_name, quantity, reorder_threshold) -> InventoryResult:
        try:
            if not getattr(user, "is_admin", False):
                raise AdminRequiredError("add_inventory_item")

            item = InventoryItem(item_name, quantity, reorder_threshold)
            self.inventory_items[item.name] = item

            self._emit_event(
                InventoryAdded(item.name, quantity)
            )

            return InventoryResult(success=True, item=item)

        except SeedBankError as e:
            return InventoryResult(success=False, error=str(e))

        except Exception as e:
            return InventoryResult(success=False, error=f"[Critical] Unexpected failure: {e}")

    def check_seed_health(self, user) -> HealthCheckResult:
        try:
            if not getattr(user, "is_admin", False):
                raise AdminRequiredError("check_seed_health")

            alerts = []

            for seed_type, batches in self.seeds.items():
                for batch in batches:
                    if batch.is_expired():
                        alerts.append((seed_type, "EXPIRED"))
                    elif batch.needs_testing():
                        alerts.append((seed_type, "TEST_REQUIRED"))

            return HealthCheckResult(success=True, alerts=alerts)

        except SeedBankError as e:
            return HealthCheckResult(success=False, error=str(e))

        except Exception as e:
            return HealthCheckResult(success=False, error=f"[Critical] Unexpected failure: {e}")

    def check_inventory_alerts(self, user) -> HealthCheckResult:
        try:
            if not getattr(user, "is_admin", False):
                raise AdminRequiredError("check_inventory_alerts")

            alerts = [
                item.name
                for item in self.inventory_items.values()
                if item.needs_reorder()
            ]

            return HealthCheckResult(success=True, alerts=alerts)

        except SeedBankError as e:
            return HealthCheckResult(success=False, error=str(e))

        except Exception as e:
            return HealthCheckResult(success=False, error=f"[Critical] Unexpected failure: {e}")


    def get_events(self):
        return self.events


    # debug
    def print_state(self):
        print("Seed Bank State")

        for seed_type, batches in self.seeds.items():
            print(f"{seed_type}: {batches}")

        print("\nMembers Balance:", self.members_balance)
        print("\nInventory:", self.inventory_items)

        print("\nEvents:")
        for e in self.events:
            print(vars(e))

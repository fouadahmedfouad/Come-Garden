
class SeedBatch:
    seed_type: str
    quantity: int
    stored_season: int
    viability: float
    
    expiry_flag: bool
    needs_testing: bool


class SeedBank:
    """ Seed Bank that manages borrow/deposite operations
        and tracks the age of seeds and viability. 
    """
    INTEREST_RATE = 0.2    ## 20% interest rate for borrowing seeds
    VIABILITY_DECAY = 0.1 ## seeds lose 10% viability per season
    THRESHOLD = 0.7      ## 70% viability
    MIN_VIABILITY = 0.3 ## 30% viablity

    def __init__(self):
        self.inventory = {} 
        self.deposits = {}  
        self.loans = {}
        self.current_season = 0
    # Farmer deposits seeds
    def deposit(self, farmer, seed_type, quantity, season):
        batch = {
            "quantity": quantity,
            "stored_season": season,
            "viability": 1.0 # fresh seeds
            }

        self.inventory.setdefault(seed_type, []).append(batch)

        # record deposit
        self.deposits.setdefault(farmer, []).append({
            "seed_type": seed_type,
            "quantity": quantity,
            "season": season
        })


    def borrow(self, farmer, seed_type, quantity, due_season, interest_rate=INTEREST_RATE):
        """ borrowing from the oldest seeds in the bank, creating loans considering interst rate for repaying """
        if seed_type not in self.inventory:
            raise ValueError("Seed not available")
    
        needed = quantity
        for batch in sorted(self.inventory[seed_type], key=lambda x: x["stored_season"]):
            if batch["quantity"] >= needed:
               batch["quantity"] -= needed
               needed = 0
               break
            else:
                needed -= batch["quantity"]
                batch["quantity"] = 0

        if needed > 0:
            raise ValueError("Not enough seeds")

        repay_amount = quantity * (1 + interest_rate)

        self.loans.setdefault(farmer, []).append({
            "seed_type": seed_type,
            "quantity": quantity,
            "due_season": due_season,
            "repay_amount": repay_amount,
            "status": "active"
        })    
 
    def repay(self, farmer, seed_type, quantity):
        if farmer not in self.loans:
            raise ValueError("No loans found")

        for loan in self.loans[farmer]:
            if loan["seed_type"] == seed_type and loan["status"] == "active":
                loan["repay_amount"] -= quantity

                # add back to inventory
                batch = {
                    "quantity": quantity,
                    "stored_season": self.current_season,
                    "viability": 1.0
                }

                self.inventory.setdefault(seed_type, []).append(batch)

                if loan["repay_amount"] <= 0:
                    loan["status"] = "repaid"

                return

        raise ValueError("No matching active loan found")

    def update_viability(self, current_season, decay_rate=VIABILITY_DECAY):
        for seed_type, batches in self.inventory.items():
            for batch in batches:
                age = current_season - batch["stored_season"]
                batch["viability"] = max(0, 1 - decay_rate * age)

    def check_germination(self, threshold=THRESHOLD):
        """ flag seeds with viability below threshold for germination testing """

        flagged = []

        for seed_type, batches in self.inventory.items():
            for batch in batches:
                if batch["viability"] < threshold:
                         flagged.append({
                                "seed_type": seed_type,
                                "quantity" : batch["quantity"],
                                "viability": batch["viability"]
                             })
        return flagged

    def remove_expired(self, min_viability=MIN_VIABILITY):
        """ Remove seeds with viability below min_viability, and return a summary of removed seeds """
        removed_summary = {}

        for seed_type in list(self.inventory.keys()):
            kept_batches = []
            removed_batches = []

            for batch in self.inventory[seed_type]:
                if batch["viability"] > min_viability:
                    kept_batches.append(batch)
                else:
                    removed_batches.append(batch)

            self.inventory[seed_type] = kept_batches

            if removed_batches:
                removed_summary[seed_type] = removed_batches

        return removed_summary  

    def summary(self):
        return {
            "inventory": self.inventory,
            "deposits": self.deposits,
            "loans": self.loans
        }
#
def run_tests():
    bank = SeedBank()

    print("=== Test 1: Deposit ===")
    bank.deposit("Farmer A", "maize", 100, 0)
    print(bank.inventory)

    print("\n=== Test 2: Borrow ===")
    bank.borrow("Farmer B", "maize", 40, due_season=2)
    print(bank.inventory)
    print(bank.loans)

    print("\n=== Test 3: Repay ===")
    bank.current_season = 1
    bank.repay("Farmer B", "maize", 20)
    print(bank.inventory)
    print(bank.loans)

    print("\n=== Test 4: Viability Update ===")
    bank.update_viability(current_season=3)
    print(bank.inventory)

    print("\n=== Test 5: Germination Check ===")
    flagged = bank.check_germination()
    print(flagged)

    print("\n=== Test 6: Remove Expired ===")
    removed = bank.remove_expired()
    print("Removed:", removed)
    print("Inventory:", bank.inventory)

    print("\n=== Final Summary ===")
    print(bank.summary())


if __name__ == "__main__":
    run_tests()



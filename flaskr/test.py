from datetime import datetime


# =========================
# MEMBER
# =========================
class Member:
    def __init__(self, name, credits, mtype="regular"):
        self.name = name
        self.credits = credits
        self.type = mtype


# =========================
# RENTAL
# =========================
class Rental:
    def __init__(self, plot, total_price):
        self.plot = plot
        self.total_price = total_price
        self.participants = []  # [{member, share, paid}]
        self.status = "active"

    def add_participant(self, member, share):
        # prevent duplicate
        for p in self.participants:
            if p["member"] == member:
                raise ValueError("Member already in this rental")

        cost = self.total_price * share

        if member.credits < cost:
            raise ValueError("Not enough credits")

        member.credits -= cost

        self.participants.append({
            "member": member,
            "share": share,
            "paid": cost
        })

    def total_share(self):
        return sum(p["share"] for p in self.participants)

    def is_full(self):
        return self.total_share() >= 1.0

    def is_active(self):
        return self.status == "active"


# =========================
# PLOT
# =========================
class Plot:
    def __init__(self, plot_id, size, soil_quality="normal"):
        self.id = plot_id
        self.size = size
        self.soil_quality = soil_quality
        self.rental = None

    def is_available(self):
        return self.rental is None or not self.rental.is_full()

    def get_owners(self):
        if not self.rental:
            return []
        return [p["member"].name for p in self.rental.participants]


# =========================
# ALLOTMENT
# =========================
class Allotment:
    PLOT_PRICING = {
        "small": 10,
        "medium": 20,
        "large": 30
    }

    SOIL_PRICE_MODIFIER = {
        "normal": 1.0,
        "premium": 1.5
    }

    MEMBERSHIP_DISCOUNT = {
        "regular": 1.0,
        "gold": 0.8
    }

    def __init__(self):
        self.plots = {}

    def add_plot(self, plot):
        self.plots[plot.id] = plot

    def calculate_rent(self, plot, member):
        base = self.PLOT_PRICING[plot.size]
        soil = self.SOIL_PRICE_MODIFIER.get(plot.soil_quality, 1)
        discount = self.MEMBERSHIP_DISCOUNT.get(member.type, 1)

        return base * soil * discount

    def rent_plot(self, plot_id, member, share=1.0):
        plot = self.plots.get(plot_id)

        if not plot:
            return "Plot not found"

        if not plot.is_available():
            return "Plot fully rented"

        price = self.calculate_rent(plot, member)

        if plot.rental is None:
            plot.rental = Rental(plot, price)

        rental = plot.rental

        if rental.total_share() + share > 1.0:
            return "Not enough share available"

        try:
            rental.add_participant(member, share)
        except ValueError as e:
            return str(e)

        return f"{member.name} rented {share*100:.0f}% of plot {plot_id}"


# =========================
# TESTS
# =========================
if __name__ == "__main__":
    allotment = Allotment()

    # Create plot
    plot = Plot(1, "medium", "premium")
    allotment.add_plot(plot)

    # Members
    A = Member("Alice", 100)
    B = Member("Bob", 100)

    print("=== Test 1: Full Rent ===")
    print(allotment.rent_plot(1, A, 1.0))
    print("Owners:", plot.get_owners())
    print("Available:", plot.is_available())
    print("Alice credits:", A.credits)
    print()

    # Reset
    plot = Plot(2, "medium", "premium")
    allotment.add_plot(plot)

    print("=== Test 2: Shared Rent ===")
    print(allotment.rent_plot(2, A, 0.6))
    print(allotment.rent_plot(2, B, 0.4))
    print("Owners:", plot.get_owners())
    print("Available:", plot.is_available())
    print("Alice credits:", A.credits)
    print("Bob credits:", B.credits)
    print()

    print("=== Test 3: Overbooking ===")
    print(allotment.rent_plot(2, B, 0.2))  # should fail

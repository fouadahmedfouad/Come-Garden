from datetime import datetime, timedelta

class Rental:
    def __init__(self, plot, total_price,season):
        self.plot = plot
        self.season = season
        self.total_price = total_price
        self.participants = []  # [{member, share, paid}]

    def add_participant(self, member, share):

        for p in self.participants:
            if p["member"] == member:
                raise ValueError("Member already in this rental")

        cost = self.total_price * share
        season = self.season

        if member.credits < cost:
            raise ValueError("Not enough credits")

        member.credits -= cost

        self.participants.append({
            "member": member,
            "share": share,
            "paid": cost,
            "season": season
        })

    def total_share(self):
        return sum(p["share"] for p in self.participants)

    def is_full(self):
        return self.total_share() >= 1.0


from datetime import datetime, timedelta

class Participant:
    def __init__(self, member, share, cost, auto_renew):
        self.member = member
        self.share = share
        self.cost = cost
        self.paid = True
        self.auto_renew = auto_renew

        self.status = "Active"

class Rental:
    def __init__(self, plot, total_price, season, status="Active"):
        self.plot = plot
        self.total_price = total_price
        self.participants = []
        self.status = status

        self.start_date = max(datetime.now(), season.start_date)
        self.end_date = season.end_date

        self.joined_mid_season = datetime.now() > season.start_date

    def _add_participant(self, member, share, calculated_cost, auto_renew):

        for p in self.participants:
            if p.member == member:
                raise ValueError("Member already in this rental")

        if self.total_share() + share > 1.0:
            raise ValueError("Total share exceeds 100%")

        cost = calculated_cost

        if member.credits < cost:
            raise ValueError("Not enough credits")

        member.credits -= cost

        participant = Participant(member, share, cost, auto_renew)
        self.participants.append(participant)

    def total_share(self):
        return sum(p.share for p in self.participants)

    def is_full(self):
        return round(self.total_share(), 5) >= 1.0

from datetime import datetime, timedelta
from .environment import TimeProvider

class Participant:
    def __init__(self, member, share, cost, late, auto_renew):
        self.member = member
        self.share = share
        self.cost = cost
        self.auto_renew = auto_renew
        
        self.start_date = None
        self.end_date   = None
        self.status = "Active"
        self.late = late

class Rental:
    def __init__(self, plot, total_price, season, status="Active"):
        self.plot = plot
        self.total_price = total_price
        self.participants = []
        self.status = status

        self.start_date = max(datetime.now().date(), season.start_date)
        self.end_date = season.end_date


    def _add_participant(self, member, share, calculated_cost, season, auto_renew):

        for p in self.participants:
            if p.member == member:
                raise ValueError("Member already in this rental")

        if self.total_share() + share > 1.0:
            raise ValueError("Total share exceeds 100%")

        cost = calculated_cost

        if member.credits < cost:
            raise ValueError("Not enough credits")

        member.credits -= cost

        today = TimeProvider().now()
        midpoint = season.start_date + (season.end_date - season.start_date) / 2 
        late = today > midpoint


        participant = Participant(member, share, cost, late, auto_renew)

        participant.start_date = self.start_date
        participant.end_date   = self.end_date

        self.participants.append(participant)

    def total_share(self):
        return sum(p.share for p in self.participants)

    def is_full(self):
        return round(self.total_share(), 5) >= 1.0

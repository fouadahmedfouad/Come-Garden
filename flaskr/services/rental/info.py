from datetime import datetime

class Application:
    def __init__(self, member, plot, share=1.0, auto_renew=False):
        self.member = member
        self.plot = plot
        self.share = share
        self.auto_renew = auto_renew

        self.score = self.calculate_score()

    def calculate_score(self):
        residency = self.member.calculate_residency_duration()
        return residency * 2 + self.member.contribution_points


class Participant:
    def __init__(self, member, share, cost, late, auto_renew=False):
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
        
        self.season = season
        self.start_date = max(datetime.now().date(), season.first_day())
        self.end_date = season.last_day()

    def total_share(self):
        return sum(p.share for p in self.participants)

    def is_full(self):
        return round(self.total_share(), 5) >= 1.0



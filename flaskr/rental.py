from datetime import datetime, timedelta

class Rental:
    def __init__(self, plot, total_price,season,status="Active"):
        self.plot = plot
        self.total_price = total_price
        self.participants = [] ##TODO Move to Particpation class
        self.status = status
       
        self.season = season
        self.start_date = max(datetime.now(), season.start_date)
        self.end_date = season.end_date

        self.joined_mid_season = datetime.now() > season.start_date

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


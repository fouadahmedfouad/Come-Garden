from datetime import datetime
from environment import TimeProvider
from config import  PLOT_PRICING, SOIL_PRICE_MODIFIER, MEMBERSHIP_DISCOUNT

from services.service_exceptions import (
    MemberNotFoundError,
    PlotNotFoundError,
    InvalidShareError,
    InsufficientCreditsError,
    DuplicateParticipantError
)
from enums import RentalStatus


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

class RentalResult:
    def __init__(self, status, rental=None):
        self.status = status
        self.rental = rental

class RentalService:

    def calculate_rent(self, plot, member):
        base = PLOT_PRICING[plot.size]
        soil_factor = SOIL_PRICE_MODIFIER.get(plot.soil_quality, 1)
        discount = MEMBERSHIP_DISCOUNT.get(member.type, 1)
        tier_factor = member.get_member_tier_factor()

        return base * soil_factor * discount * tier_factor


    def _rent_plot(self, plot, member, current_season, app) -> RentalResult:
        if member is None:
            raise MemberNotFoundError("Member does not exist")

        if plot is None:
            raise PlotNotFoundError("Plot does not exist")

        if app.share not in (0.5, 1):
            raise InvalidShareError("Share must be 0.5 or 1")

        cost = self.calculate_rent(plot, member)

        if member.credits < cost:
            raise InsufficientCreditsError("Not enough credits")

        if plot.rental is None:
            plot.rental = Rental(plot, PLOT_PRICING[plot.size], current_season)

        rental = plot.rental

        # NOTE: We're allowing only one participant for each member (we can later change that or allow updating participant share)
        if any(p.member == member for p in rental.participants):
            raise DuplicateParticipantError("Already renting this plot")

        if rental.is_full() or rental.total_share() + app.share > 1.0:
            plot.add_to_season_list(app)
            return RentalResult(RentalStatus.WAITLISTED)

        # ---- Rent ----
        today = TimeProvider().now()

        midpoint = current_season.first_day() + (
            current_season.last_day() - current_season.first_day()
        ) / 2

        late = today > midpoint

        participant = Participant(member, app.share, cost, late, app.auto_renew)
        participant.start_date = rental.start_date
        participant.end_date = rental.end_date

        member.minus_credits(cost)
        rental.participants.append(participant)

        return RentalResult(RentalStatus.SUCCESS, rental)



    def apply(self, member, plot, share=1.0, auto_renew=False):

        if member is None:
            raise MemberNotFoundError("Member does not exist")

        if plot is None:
            raise PlotNotFoundError("Plot does not exist")


        application = Application(member, plot, share, auto_renew)
        plot.waitlist.append(application)

        return application

    
    def end_rentals(self, plot, new_season):
        old_rental = plot.rental
        plot.rental = None
        ## Renew autos

        plot.waitlist = []
        for p in old_rental.participants:
            if p.auto_renew:
                self.apply(p.member, plot.id,p.share,p.auto_renew)
            else:
                p.status = "Terminated"
        if plot.waitlist:
            self.process_waitlist(plot,plot.waitlist, new_season) 

        ## Rent the rest
        plot.season_waitlist.sort(key=lambda app: app.score, reverse=True)            

        self.process_waitlist(plot, plot.season_waitlist, new_season)
        plot.season_waitlist = []

        old_rental.status = "Expired"
        plot.history_of_rentals.append(old_rental)



    def rent_plots(self, plot, current_season):
        plot.season_waitlist.sort(key=lambda app: app.score, reverse=True)
        self.process_waitlist(plot,plot.waitlist, current_season)
        plot.waitlist = []


    def alert_rentals(self,plot):  
        for p in plot.rental.participants: 
            if p.auto_renew:
                p.status = "ExpiringSoon" # check your credits for renewal
            else:
                p.status = "PendingTermination" 



    def process_waitlist(self, plot, waitlist, season):
        for app in waitlist:
            self._rent_plot(plot,app.member,season,app) 


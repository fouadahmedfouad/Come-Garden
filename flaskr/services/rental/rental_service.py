from datetime import datetime
from environment import TimeProvider
from config import  PLOT_PRICING, SOIL_PRICE_MODIFIER, MEMBERSHIP_DISCOUNT

from services.rental.exceptions import (
    MemberNotFoundError,
    PlotNotFoundError,
    InvalidShareError,
    InsufficientCreditsError,
    DuplicateParticipantError
)


from services.rental.info import *
from services.rental.exceptions import *
from services.rental.results import *
from services.rental.events import *

class RentalService:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.events = []

    def _emit_event(self, event):
        self.events.append(event)   # optional debug log
        if self.event_bus:
            self.event_bus.publish(event)    
   
    def apply(self, member, plot, share=1.0, auto_renew=False) -> ApplicationResult:
        try:
            if member is None:
                raise MemberNotFoundError("Member does not exist")

            if plot is None:
                raise PlotNotFoundError("Plot does not exist")

            application = Application(member, plot, share, auto_renew)
            plot.waitlist.append(application)

            self._emit_event(
                ApplicationSubmitted(member.id, plot.id, share)
            )

            return ApplicationResult(True, application)

        except Exception as e:
            return ApplicationResult(False, error=str(e))    



    def _rent_plot(self, plot, member, current_season, app) -> RentalResult:
        try:
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

                self._emit_event(
                    RentalWaitlisted(member.id, plot.id)
                )

                return RentalResult(success=True, waitlisted=True)

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

            self._emit_event(
                RentalApproved(member.id, plot.id)
            )

            return RentalResult(success=True, rental=rental)

        ## TODO: Rental Failed event
        except RentalError as e:
            user_id = member.id if member else None
            plot_id = plot.id if plot else None

            self._emit_event(
                RentalFailed(user_id=user_id, plot_id=plot_id, message=str(e))
            )
            return RentalResult(success=False, error=str(e))

        except Exception as e:
            return RentalResult(success=False, error=f"[Critical] {e}")

    def end_rentals(self, plot, new_season):
        old_rental = plot.rental
        old_rental.status = "Expired"

        plot.history_of_rentals.append(old_rental)
        plot.rental = None

        self._emit_event(
            RentalExpired(plot.id)
        )

        ## Renew auto_renews
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


    def rent_plot(self, plot, current_season):
        plot.season_waitlist.sort(key=lambda app: app.score, reverse=True)
        self.process_waitlist(plot,plot.waitlist, current_season)
        plot.waitlist = []


    def calculate_rent(self, plot, member):
        base = PLOT_PRICING[plot.size]
        soil_factor = SOIL_PRICE_MODIFIER.get(plot.soil_quality, 1)
        discount = MEMBERSHIP_DISCOUNT.get(member.type, 1)
        tier_factor = member.get_member_tier_factor()

        return base * soil_factor * discount * tier_factor

    def alert_rentals(self,plot):  
        for p in plot.rental.participants: 
            if p.auto_renew:
                p.status = "ExpiringSoon" # check your credits for renewal
            else:
                p.status = "PendingTermination" 

    def process_waitlist(self, plot, waitlist, season):
        for app in waitlist:
            self._rent_plot(plot,app.member,season,app) 


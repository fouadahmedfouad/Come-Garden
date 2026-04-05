from datetime import datetime, timedelta
from environment import TimeProvider
from config import  PLOTS, PLOT_PRICING, SOIL_PRICE_MODIFIER, MEMBERSHIP_DISCOUNT, SUN_SCHEDULE

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

    def total_share(self):
        return sum(p.share for p in self.participants)

    def is_full(self):
        return round(self.total_share(), 5) >= 1.0




class RentalService():

    # def _add_participant(self, rental, member, share, calculated_cost, season, auto_renew):
    #
    #  
    def calculate_rent(self, plot, member):
        base = PLOT_PRICING[plot.size]
        soil_factor = SOIL_PRICE_MODIFIER.get(plot.soil_quality, 1)
        discount    = MEMBERSHIP_DISCOUNT.get(member.type, 1)
        tier_factor = member.get_member_tier_factor()

        return base * soil_factor * discount * tier_factor


    def process_waitlist(self,plot):
        waitlist = plot.waitlist

        for record in waitlist:
            _,share,member_id = record
            member= self.members[member_id]

            result = self.rental_service.rent_plot(plot,member,self.current_season, record) 
            print(result)

        plot.waitlist = []


    def rent_plot(self, plot, member, current_season, record):
        plot_cost = PLOT_PRICING[plot.size]

        score,share,member_id = record

        if not member:
            # "Member doesn't exist"
            print("member doesn't exist")
            return None


        if not plot:
            # "Plot doesn't exist"
            print("Plot doesn't exist")
            return None

        if share not in [0.5,1]:
            print("Share should be half or full")
            return None

        cost = self.calculate_rent(plot, member)
 
        if member.credits < cost:
            print("Not enough credits")
            return None


        if plot.rental is None:
            plot.rental = Rental(plot, plot_cost, current_season)
       
        rental = plot.rental
          

        for p in rental.participants:
            if p.member == member:
                print("Member already in this rental")
                return None



        if rental.is_full(): 
            plot.add_to_season_list(record)
            print("Seasoned")
            return 2

        if rental.total_share() + share > 1.0:
                plot.add_to_season_list(record)
                print("Seasoned")
                return 2


        ## OtherWise rent it to him



        today = TimeProvider().now()
        midpoint = current_season.start_date + (current_season.end_date - current_season.start_date) / 2 
        late = today > midpoint

        ## NOTE: WE'RE STORING THE MEMBER OBJECT
        participant = Participant(member, share, cost, late, False)

        participant.start_date = rental.start_date
        participant.end_date   = rental.end_date

        member.minus_credits(cost)
        rental.participants.append(participant)


        # print(f"{member.name} rented {share*100:.0f}% of plot {plot_id}")
        return 1

   
    def renew_rental(self, plot, old_rental, next_season):
        plot_cost = PLOT_PRICING[plot.size]

        if old_rental is None:
            return

        new_rental = Rental(plot, plot_cost, next_season)
    
        for p in old_rental.participants:

            # TODO: don't store the object, try store a record instead
            member = p.member
            member.rental_history.append(p)

            if p.auto_renew:
                cost = self.calculate_rent(plot.id,p.member.id)

                success = self._add_participant_to_rental(
                    new_rental,
                    p.member,
                    p.share,
                    cost
                )
                if success:
                    p.status = "Active"
            else:
                p.status = "Terminated"
    
        if not new_rental.participants:
            plot.rental = None
        else:
            plot.rental = new_rental
    
        old_rental.status = "Expired"

        return plot.rental   





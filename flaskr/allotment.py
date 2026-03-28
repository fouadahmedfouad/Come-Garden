from .rental import Rental 
from .plot import Plot
from .member import Member
from .time import TimeProvider
from datetime import datetime, timedelta, timezone
# Tips:
## Be realsitc
## Put constraints
## automate


class Season():
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date   = end_date

class Allotment():

    def __init__(self,width,height,road=2):
        self.allotment_width = width
        self.allotment_height = height
        self.road = road 
        
        self.seasons = ()
        self.current_season = None
        self.time_provider = TimeProvider()
        self.members = {}

       
        self.plots = {}
        self.plots_by_type = {"large":[],"small":[] }
        
        self.errno = 0

    PLOTS = {
        "large": {"w": 20, "h": 10},
        "small": {"w": 6.3, "h": 3.3}
    }

    PLOT_PRICING = {
        "small": 10,
        "large": 30
    }

    SOIL_PRICE_MODIFIER = {
        "normal": 1.0,
        "premium": 1.5
    }

    MEMBERSHIP_DISCOUNT = {
        "normal": 1.0,
        "premium": 0.8
    }

    sun_schedule = {
    "left": {
        "8am": 0.0,
        "9am": 0.0,
        "10am": 0.5,
        "11am": 1.0,
        "12pm": 1.0,
        "1pm": 1.0,
        "2pm": 1.0,
        "3pm": 0.5,
        "4pm": 0.5,
        "5pm": 0.0,
        "6pm": 0.0,
        "7pm": 0.0,
        "8pm": 0.0,
        "9pm": 0.0,
    },

    "middle": {
        "8am": 0.5,
        "9am": 1.0,
        "10am": 1.0,
        "11am": 1.0,
        "12pm": 1.0,
        "1pm": 1.0,
        "2pm": 1.0,
        "3pm": 1.0,
        "4pm": 0.5,
        "5pm": 0.5,
        "6pm": 0.5,
        "7pm": 0.0,
        "8pm": 0.0,
        "9pm": 0.0,
    },

    "right": {
        "8am": 1.0,
        "9am": 1.0,
        "10am": 1.0,
        "11am": 1.0,
        "12pm": 1.0,
        "1pm": 1.0,
        "2pm": 1.0,
        "3pm": 1.0,
        "4pm": 1.0,
        "5pm": 1.0,
        "6pm": 0.5,
        "7pm": 0.5,
        "8pm": 0.0,
        "9pm": 0.0,
    }
    }

    def assign_zone(self,x):
        if x < 0.25:
            return "left"
        elif x < 0.75:
            return "middle"
        else:
            return "right"
    
    def assign_sun_profile(self, plot, alt_w):
        x, _ = plot.center
    
        # normalize + clamp
        nx = (x + alt_w / 2) / alt_w
        nx = max(0, min(nx, 1))
    
        zone = self.assign_zone(nx)
    
        plot.zone = zone
        plot.sun_profile = self.sun_schedule[zone] 
 
    def create_plot(self,plot_id,plot_size,x,y,w,h):
        center = (round(x,2), round(y,2))
        area = w * h
        
        boundary = {
            "x_min": x - w/2,
            "x_max": x + w/2,
            "y_min": y - h/2,
            "y_max": y + h/2,
        }

        return Plot(plot_id,plot_size,center,w,h,area,boundary,"available")

    def add_plot(self,plot,plot_size):
        self.plots[plot.id] = plot
        self.plots_by_type[plot_size].append(plot)
    
    def join_member(self,memberFullName):
        for member in self.members.values():
            if member.name == memberFullName:
                return f"{member.name} Already exist with Id {member.id}"
        
        member_id = len(self.members)
        member = Member(member_id,memberFullName)
        self.members[member.id] = member
        
        return member.id
    
    def cad_render(self,large_pts,small_pts):
        try: 
            import cadquery as cq
            from ocp_vscode import show
        except ImportError:
            raise RuntimeError("cad_render requires cadquery and ocp_vscode installed")
      
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        
        lw, lh = self.PLOTS["large"]["w"], self.PLOTS["large"]["h"]
        sw, sh = self.PLOTS["small"]["w"], self.PLOTS["small"]["h"] 

        alt_thickness = 1
        plt_thickness = 3
        
        allotment = cq.Workplane("front").rect(alt_w,alt_h).extrude(alt_thickness)
        if large_pts:
            allotment = allotment.pushPoints(large_pts).rect(lw, lh).extrude(plt_thickness)
        if small_pts:
            allotment = allotment.pushPoints(small_pts).rect(sw, sh).extrude(plt_thickness)

        show(allotment, reset_camera=True)
   
    def generate_points(self,start_x, start_y, step_x, step_y, count_x, count_y):
        return [
            (start_x + i * step_x, start_y + j * step_y)
            for i in range(count_x)
            for j in range(count_y)
        ]
    
    def generate_layout(self):
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        road  = self.road
        
        lw, lh = self.PLOTS["large"]["w"], self.PLOTS["large"]["h"]
    
        # LARGE PLOTS FIRST (GREEDY) 
        stepLx, stepLy = lw + road, lh + road 
        
        nlp_W = int((alt_w - road) // stepLx)
        nlp_H = int((alt_h - road) // stepLy)
        
        used_width = nlp_W * stepLx
        used_height = nlp_H * stepLy
        
        startLx = -(alt_w / 2) + road + lw / 2
        startLy = -(alt_h / 2) + road + lh / 2
        
        large_pts = self.generate_points(startLx, startLy, stepLx, stepLy, nlp_W, nlp_H)

        # SMALL PLOTS
        remaining_width  = alt_w - used_width
        remaining_height = alt_h - used_height
        
        sw, sh = self.PLOTS["small"]["w"], self.PLOTS["small"]["h"]
        stepSx = sw + road
        stepSy = sh + road
        
        small_pts = []
        # RIGHT STRIP
        if remaining_width >= sw:
            nsp_W_right = int(remaining_width // stepSx)
            nsp_H_right = int((alt_h - road) // stepSy)
        
            right_edge_large = -(alt_w / 2) + used_width + road
    
            startRx = right_edge_large + sw / 2
            startRy = -(alt_h / 2) + road + sh / 2
    
            small_pts += self.generate_points(startRx, startRy, stepSx, stepSy, nsp_W_right, nsp_H_right)
        
        
        # TOP STRIP
        if remaining_height >= sh:
            nsp_W_top = int((used_width) // stepSx)
            nsp_H_top = int(remaining_height // stepSy)
        
            top_edge_large = -(alt_h / 2) + used_height + road
        
            startTx = -(alt_w / 2) + road + sw / 2
            startTy = top_edge_large + sh / 2
        
            small_pts += self.generate_points(startTx, startTy, stepSx, stepSy, nsp_W_top, nsp_H_top)

        return large_pts,small_pts

    def plot_maker(self):
        large_pts,small_pts = self.generate_layout()

        alt_w = self.allotment_width # used for sun exposure
        plot_id = 1 

        # LARGE
        lw, lh = self.PLOTS["large"]["w"], self.PLOTS["large"]["h"]
        for (x,y) in large_pts:
            plot = self.create_plot(plot_id,"large",x,y,lw,lh)
            self.assign_sun_profile(plot,alt_w) 
            self.add_plot(plot,"large")
            plot_id += 1

        # SMALL 
        sw, sh = self.PLOTS["small"]["w"], self.PLOTS["small"]["h"] 
        if small_pts:
            for (x,y) in small_pts:
                plot = self.create_plot(plot_id,"small",x,y,sw,sh) 
                self.assign_sun_profile(plot,alt_w) 
                self.add_plot(plot,"small")
                plot_id += 1

        self.totalLargePlots = len(large_pts)
        self.totalSmallPlots = len(small_pts)
        self.totalPlots = len(large_pts) + len(small_pts)
        
        # print("Total plots:", self.totalPlots)        
        # print("Large plots:", self.totalLargePlots)
        # print("Small plots:", self.totalSmallPlots)

    
    def get_member_tier_factor(self,member):
        count = len(member.rental_history)

        if count < 2:
            return 1.0
        elif count < 5:
            return 0.9
        else:
            return 0.8
    
    def calculate_rent(self, plot_id, member_id):
        plot = self.plots.get(plot_id)
        member= self.members[member_id]

        base = self.PLOT_PRICING[plot.size]
        soil_factor = self.SOIL_PRICE_MODIFIER.get(plot.soil_quality, 1)
        discount = self.MEMBERSHIP_DISCOUNT.get(member.type, 1)
        tier_factor = self.get_member_tier_factor(member)

        return base * soil_factor * discount * tier_factor

    def calculate_residency_duration(self,member_id):
        member = self.members.get(member_id)
        total_days = 0
    
        for rental in member.rental_history:
            start = rental.start_date
            end   = rental.end_date
            total_days += (end - start).days
        
        return total_days    

    def apply(self,plot_id,member_id,share=1.0): 
        plot = self.plots.get(plot_id)
        member = self.members.get(member_id)
        member_residency_duration = self.calculate_residency_duration(member_id)

        if member and plot:
            score = member_residency_duration*2 + member.contribution_points
            plot.waitlist.append((score,share,member_id))

    def add_participant_to_rental(self, rental, member, share, cost, auto_renew=False):
        try:
            rental._add_participant(member, share, cost, self.current_season, auto_renew)
            return True
        except ValueError:
            return False

    ## duration should be one season for all plots
    def _rent_plot(self, plot_id, member_id, share=1.0):

        plot = self.plots.get(plot_id)
        plot_cost = self.PLOT_PRICING[plot.size]
        member = self.members.get(member_id)
        current_season = self.current_season

        self.errno = 0

        if not member:
            # "Member doesn't exist"
            self.errno  = -3
            return None


        if not plot:
            # "Plot doesn't exist"
            self.errno  = -4
            return None

        cost = self.calculate_rent(plot.id, member.id)
 
        if plot.rental is None:
            plot.rental = Rental(plot, plot_cost, current_season)
       
        rental = plot.rental
   
        if not plot.is_available():
            # "Plot already rented"
            self.errno  = -1
            return None 
        
        added = self.add_participant_to_rental(rental, member, share, cost)

        if not added:
            #  str(e)
            self.errno  = -2
            return None 

        # print(f"{member.name} rented {share*100:.0f}% of plot {plot_id}")
        return plot

    def rent_plot(self,plot_id):
        plot = self.plots.get(plot_id)
        
        if not plot:
            return -2

        plot.waitlist.sort(reverse=True)

        for record in plot.waitlist:
            _,share,member_id = record
            self._rent_plot(plot.id,member_id,share) 

        plot.waitlist = []
        return 1 
    
    def renew_rental(self, plot, old_rental):
        next_season = self.get_next_season()
        plot_cost = self.PLOT_PRICING[plot.size]

        if old_rental is None:
            return

        new_rental = Rental(plot, plot_cost, next_season)
    
        for p in old_rental.participants:

            # TODO: don't store the object, try store a record instead
            member = p.member
            member.rental_history.append(p)

            if p.auto_renew:
                cost = self.calculate_rent(plot.id,p.member.id)

                success = self.add_participant_to_rental(
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


    # def audit_rental_alert(self):

    #     for plot in self.plots.values():  
    #         if plot.rental:
    #             if plot.rental.status != "Active":
    #                 return
        
    #             if datetime.now().date() >= plot.rental.end_date.date() - timedelta(days=15):
                
    #                 for p in plot.rental.participants:
                    
    #                     if p.auto_renew:
    #                         p.status = "ExpiringSoon"
    #                     else:
    #                         p.status = "PendingTermination"


    def update_current_season(self):
        today = self.time_provider.now()
    
        for season in self.seasons:
            if season.start_date <= today <= season.end_date:
                self.current_season = season
                return
    
        self.current_season = None
    
    
    def get_next_season(self):
        today = self.time_provider.now()
    
        for season in self.seasons:
            if season.start_date > today:
                return season
    
        return None


    def audit_rental_end(self):
        today = self.time_provider.now()

        for plot in self.plots.values():
    
            rental = plot.rental
            
            if not rental or rental.status != "Active":
                continue
    
            if today >= rental.end_date:
                print(f"Today is the day for ending {plot.id} rental")
                self.renew_rental(plot, rental)

    def audit_rent_plots(self):
       for plot in self.plots.values():
            if plot.is_available():
                self.rent_plot(plot.id)  
            
    @staticmethod
    def build_seasons(year):
        return [
            Season("Spring", datetime(year, 3, 1).date(), datetime(year, 5, 31).date()),
            Season("Summer", datetime(year, 7, 1).date(), datetime(year, 10, 31).date()),
            Season("Fall", datetime(year, 11, 1).date(), datetime(year, 11, 30).date()),
            Season("Winter", datetime(year, 12, 1).date(), datetime(year + 1, 2, 28).date()),
        ]

    ## then we may audit to rebuild seasons for new season

    def make(self):
        year = self.time_provider.now().year

        self.seasons = ( 
            self.build_seasons(year - 1) +
            self.build_seasons(year) 
            )

        self.update_current_season()
        self.plot_maker()
        return self

def test_renew_before_rent():
    alt = Allotment(100,50).make()
    plot = alt.plots[1]
    
    member_id  = alt.join_member("Fouad ahmed fouad")  
    member_id2 = alt.join_member("Ahmed fouad")
    member_id3 = alt.join_member("Alice marchel")
    member_id4 = alt.join_member("Dan alex")

    member = alt.members[member_id]
    member2 = alt.members[member_id2]
    member3 = alt.members[member_id3]
    member4 = alt.members[member_id4]

    member.credits = 200
    member2.credits = 200
    member3.credits = 200
    member4.credits = 200
    


    alt.apply(1,member_id,0.1)   
    alt.apply(1,member_id2,0.1)
    alt.apply(1,member_id3,0.1)
    alt.apply(1,member_id4,0.1)
    print("Wait",plot.waitlist)

    # Season 1 starts
    alt.audit_rental_end()
    alt.audit_rent_plots()

    print("Season 1 members")
    for p in plot.rental.participants:
        print(p.member.name)


    ## set auto_renew for current participant for the member 
    # i = 0
    # for p in plot.rental.participants:
    #     p.auto_renew = True
    #     i += 1
    #     if i == 2:
    #         break
 

    member_id5 = alt.join_member("New Member")
    member = alt.members[member_id5]
    member.credits = 200
    
    ## Accepting applications during season 1
    alt.apply(1,member_id5,0.2)
    alt.apply(1,member_id4,0.2)
     ## if the plot is available we allow rent (considering it will end by the end of the season no matter how late you are)
    alt.audit_rental_end()
    alt.audit_rent_plots()

    print("Season 1 members")
    for p in plot.rental.participants:
        print(p.member.name)


     
    # print("Season 2 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)

        
    # member_id6 = alt.join_member("New Member2")
    # member = alt.members[member_id6]
    # member.credits = 200

 
    # ## Accepting applications during season 2

    # alt.apply(1, member_id6, 0.1)
    # alt.apply(1, member_id4, 0.1)
    #     ## if the plot is available we can allow rent (considering it will end by the end of the season)
    # alt.audit_rent_plots()


    # alt.audit_rental_end() 
    # alt.audit_rent_plots()
    
    # print("Season 3 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)

    # # End of season 1, and Start of Season 2
    # alt.renew_rental(plot,plot.rental)
    # alt.rent_plot(1)

    # print("Season 2 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)


    # ## auto-renew got it, new member got it over the resident (because rentals are added to the history after it ends, and the season wasn't yet ended when new member applied)
  

    # ## set auto_renew for current participant for the member 
    # i = 0
    # for p in plot.rental.participants:
    #     p.auto_renew = True
    #     i += 1
    #     if i == 2:
    #         break


     
    # member_id6 = alt.join_member("New Member2")
    # member = alt.members[member_id6]
    # member.credits = 200

 
    # ## Accepting applications during season 2
    # alt.apply(1, member_id6, 0.2)
    # alt.apply(1, member_id4, 0.2)
    #     ## if the plot is available we can allow rent (considering it will end by the end of the season)

    # print("Wait",plot.waitlist)

    # ## End of season 2, and Start of Season 3
    # alt.renew_rental(plot,plot.rental)
    # alt.rent_plot(1)

    # print("Season 3 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)

    # ## auto-renew got it, member_id4 got it for his residency priority over the new member.

    # ## end of another season
    # alt.renew_rental(plot,plot.rental)
    # alt.rent_plot(1)
    #

    
test_renew_before_rent()

## generate_layout(), plot_maker(), apply(), 






# ## after all applications



# # before the end by 15 days
# allot.audit_rental_alert()
# for p in plot.rental.participants:
#     print(p.member.name, p.status)

# # at the end of the season
# allot.apply(1,member_id2,0.1)
# allot.apply(1,member_id4,0.1)

# print("Wait",plot.waitlist)
# allot.audit_rental_end()


# # Allotment
# # generate_layout(), plot_maker()
# #
#

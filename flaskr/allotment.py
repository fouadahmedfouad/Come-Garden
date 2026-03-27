from rental import Rental 
from plot import Plot
from member import Member
from datetime import datetime, timedelta
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
        
        self.seasons = []
        self.current_season = None
       
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

    def update_current_season(self):
        today = datetime.now()
        
        for season in self.seasons:
            if season.start_date <= today <= season.end_date:
                self.current_season = season
                return
        
        self.current_season = None
    
    def add_season(self, season):
        self.seasons.append(season)
        self.update_current_season()
    #
    # def get_next_season(self):
    #
    #     today = datetime.now()
    #         
    #     future_seasons = [s for s in self.seasons if s.start_date > today]
    #     future_seasons.sort(key=lambda s: s.start_date)
    #     
    #     return future_seasons[0] if future_seasons else None
    #

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
    
    def calculate_rent(self, plot, member):
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

        if member and plot and plot.is_available():
            score = member_residency_duration*2 + member.contribution_points
            plot.waitlist.append((score,share,member_id))


    def _rent_plot(self, plot_id, member_id, share=1.0):
        ## duration is one season for all plots

        plot = self.plots.get(plot_id)
        member = self.members.get(member_id)
        current_season = self.current_season

        self.errno = 0

        if not member:
            # "Member doesn't exist"
            self.errno  = -4
            return None


        if not plot:
            # "Plot doesn't exist"
            self.errno  = -3
            return None

        price = self.calculate_rent(plot, member)
 
        if plot.rental is not None:
            plot.rental.total_price = price
        else:
            print(self.current_season.start_date)
            plot.rental = Rental(plot, price, current_season)
       
        rental = plot.rental
   
        if rental.total_share() + share > 1.0:
            # "Not enough share available"
            self.errno  = -2
            return None 

        if not plot.is_available():
            # "Plot already rented"
            self.errno  = -1
            return None 
        try:
            rental.add_participant(member,share)
        except ValueError as e:
            #  str(e)
            self.errno  = -5
            return None 

        print(f"{member.name} rented {share*100:.0f}% of plot {plot_id}")
        return plot

    def rent_plot(self,plot_id):
        plot = self.plots.get(plot_id)
        
        if not plot:
            return -2

        plot.waitlist.sort(reverse=True)

        for record in plot.waitlist:
            _,share,member_id = record

            rent = self._rent_plot(plot.id,member_id,share) 
            errno = self.errno
            print(errno)

            if errno == -1:
                return -1
            else:
                continue

        plot.waitlist = []
        return 1 


    def end_rental(self,plot_id):
        plot = self.plots.get(plot_id)
        rental = plot.rental
        
        for p in rental.participants:
            member = p["member"]
            member.add_rental({
                "plot_id": plot.id,
                "share"  : p["share"],
                "paid"   : p["paid"],
                "season" : p["season"]
                })
            
        plot.rental = None

    def create_member(self,memberFullName):
        for member in self.members.values():
            if member.name == memberFullName:
                return f"{member.name} Already exist with Id {member.id}"
        
        member_id = len(self.members)
        member = Member(member_id,memberFullName)
        self.members[member.id] = member
        
        return member.id


#
#
# allot = Allotment(100, 200)
#
# spring = Season(
#     "Spring 2026",
#     datetime(2026, 3, 1),
#     datetime(2026, 6, 30)
# )
#
# summer = Season(
#     "Summer 2026",
#     datetime(2026, 7, 1),
#     datetime(2026, 10, 31)
# )
#
# allot.add_season(spring)
# allot.add_season(summer)
#
# print(allot.current_season.name)
#
#
# # large_pts,small_pts = allot.generate_layout()
# # allot.cad_render(large_pts,small_pts)
# #
# allot.plot_maker()
#
# member_id  = allot.create_member("Fouad ahmed fouad")
# # member_id2 = allot.create_member("Ahmed fouad")
# # member_id3 = allot.create_member("Alice marchel")
# # member_id4 = allot.create_member("Dan alex")
#
# member = allot.members[member_id]
# # member2 = allot.members[member_id2]
# # member3 = allot.members[member_id3]
# # member4 = allot.members[member_id4]
# #
# plot   = allot.plots[1]
# allot.apply(1,member_id,0.5)
# # allot.apply(1,member_id4,1)
# # allot.apply(1,member_id3,0.3)
# # allot.apply(1,member_id4,0.2)
# #
# #
# member.credits = 200
# # member2.credits = 200
# # member3.credits = 200
# # member4.credits = 200
# #
# # print("after applications",plot.waitlist)
# # ## after all applications
# allot.rent_plot(1)
# rental = plot.rental
# print(rental.season.name)
# print(rental.start_date)
# print(rental.end_date)
#
# # print(plot.waitlist)
# # print(plot.rental.participants)
# # print(plot.is_available())
# #
# # ## after one season
# # allot.end_rental(plot.id)
# # print(plot.is_available())
# #
# #
# ## Begining of the season applications for plots to the waitlist 

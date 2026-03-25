from .seedBank import SeedBank
from .member   import Member
from .rental import Rental 
from .plot import Plot

# Tips:
## Be realsitc
## Put constraints
## automate



class Allotment():

    def __init__(self,width,height,road=2):
        self.allotment_width = width
        self.allotment_height = height
        self.road = road 
        
        self.current_season = 1

        self.plots = {}
        self.plots_by_type = {"large":[],"small":[] }

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
    
    def generate_points(self,start_x, start_y, step_x, step_y, count_x, count_y):
        return [
            (start_x + i * step_x, start_y + j * step_y)
            for i in range(count_x)
            for j in range(count_y)
        ]
    
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

    def cad_render(self,large_pts,small_pts,lw,lh,sw,sh):
        try: 
            import cadquery as cq
            from ocp_vscode import show
        except ImportError:
            raise RuntimeError("cad_render requires cadquery and ocp_vscode installed")
      
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        alt_thickness = 1
        plt_thickness = 3
        
        allotment = cq.Workplane("front").rect(alt_w,alt_h).extrude(alt_thickness)
        if large_pts:
            allotment = allotment.pushPoints(large_pts).rect(lw, lh).extrude(plt_thickness)
        if small_pts:
            allotment = allotment.pushPoints(small_pts).rect(sw, sh).extrude(plt_thickness)

        show(allotment, reset_camera=True)

    def plotMaker(self):
    
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        road  = self.road
        
        lw, lh = self.PLOTS["large"]["w"], self.PLOTS["large"]["h"]
    
        # LARGE PLOTS (GREEDY FIRST)
    
        stepLx = lw + road
        stepLy = lh + road
        
        nlp_W = int((alt_w - road) // stepLx)
        nlp_H = int((alt_h - road) // stepLy)
        
        used_width = nlp_W * stepLx
        used_height = nlp_H * stepLy
        
        startLx = -(alt_w / 2) + road + lw / 2
        startLy = -(alt_h / 2) + road + lh / 2
        
        large_pts = self.generate_points(startLx, startLy, stepLx, stepLy, nlp_W, nlp_H)

        plot_id = 1 
        for (x,y) in large_pts:
            plot = self.create_plot(plot_id,"large",x,y,lw,lh)
            self.assign_sun_profile(plot,alt_w) 

            self.plots[plot_id] = plot
            self.plots_by_type["large"].append(plot)
            plot_id += 1
        
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
        
        if small_pts:
            for (x,y) in small_pts:
                plot = self.create_plot(plot_id,"small",x,y,sw,sh) 
                self.assign_sun_profile(plot,alt_w) 

                self.plots[plot_id] = plot
                self.plots_by_type["small"].append(plot)
                plot_id += 1

        self.totalLargePlots = len(large_pts)
        self.totalSmallPlots = len(small_pts)
        self.totalPlots = len(large_pts) + len(small_pts)
        
        print("Total plots:", self.totalPlots)        
        print("Large plots:", self.totalLargePlots)
        print("Small plots:", self.totalSmallPlots)

    
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

    def rent_plot(self, plot_id, member,share=1.0):
        ## duration is one season for all plots

        plot = self.plots.get(plot_id)
        current_season = self.current_season

        if not plot:
            return "Plot does not exist"

        price = self.calculate_rent(plot, member)
 
        if plot.rental is not None:
            plot.rental.total_price = price
        else:
            plot.rental = Rental(plot, price, current_season)
       
        rental = plot.rental
   
        if rental.total_share() + share > 1.0:
            return "Not enough share available"


        if plot.rental and plot.rental.is_full():
            return "Plot already rented"

        try:
            rental.add_participant(member,share)
        except ValueError as e:
            return str(e)

        print(f"{member.name} rented {share*100:.0f}% of plot {plot_id}")
        return plot


    def end_rental(slef,plot):
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



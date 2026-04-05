
CROP_WATER_NEEDS = {
        "carrot": {"freq": 3, "amount": 2},
        "tomato": {"freq": 2, "amount": 3},
        "lettuce": {"freq": 1, "amount": 2},
        }

from config import  PLOTS, PLOT_PRICING, SOIL_PRICE_MODIFIER, MEMBERSHIP_DISCOUNT, SUN_SCHEDULE

class Plot:

    def __init__(self,plot_id,plot_size,center,width,height,area,boundary,status,soil_quality="normal"):
        self.id     = plot_id
        self.size   = plot_size
        self.width  = width
        self.height = height
        self.center = center
        self.area   = area
        self.boundary = boundary
        self.status = status
        x,y = center
        
        self.neighbors = []
        self.zone = None
        self.sun_profile = None
 
        self.rental = None
        self.waitlist = []
        self.season_waitlist = []
      
        self.sun_profile = None



        self.neighbors = []
        self.soil_quality = soil_quality


        self.activities = []        

        self.soil_state = "healthy"   # healthy, depleted, recovering
        self.ph_level = 7
        self.fertilizer_history = []
        self.current_crop_type = None
        self.last_crop = None

        self.infection_status = None
        self.infection_type = None
        self.infection_date = None

        watering_schedule = None
        self.tasks = []
        self.alerts = []

    def assign_zone(self,x):
        if x < 0.25:
            return "left"
        elif x < 0.75:
            return "middle"
        else:
            return "right"
 
    def assign_sun_profile(self, alt_w):
        x, _ = self.center
    
        # normalize + clamp [0,1]
        nx = (x + alt_w / 2) / alt_w
        nx = max(0, min(nx, 1))
    
        zone = self.assign_zone(nx)
    
        self.zone = zone
        self.sun_profile = SUN_SCHEDULE[zone] 
  
    def is_available(self):
        return self.rental is None or not self.rental.is_full()

    def get_owners(self):
        if self.rental and self.rental.participants:
            return [p.member.name for p in self.rental.participants]
        return []


    def add_to_season_list(self,record):
        if record not in self.season_waitlist:
            self.season_waitlist.append(record)
            return True
        return False


class PlotService():

    def assign_sun_profile(self, plot, alt_w):
        plot.assign_sun_profile(alt_w)

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

    def generate_points(self,start_x, start_y, step_x, step_y, count_x, count_y):
        return [
            (start_x + i * step_x, start_y + j * step_y)
            for i in range(count_x)
            for j in range(count_y)
        ]
    
    def generate_layout(self, alt_w,alt_h,road):
        
        lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
    
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
        
        sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"]
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

    def assign_neighbors(self, plots):
    
        for p1 in plots:
            p1.neighbors = []
            for p2 in plots:
                if p1.id == p2.id:
                    continue

                if self.are_neighbors(p1, p2):
                    p1.neighbors.append(p2.id)


    def are_neighbors(self, p1, p2, tol=2.5, debug=False):
        dx = abs(p1.center[0] - p2.center[0])
        dy = abs(p1.center[1] - p2.center[1])
    
        max_dx = (p1.width + p2.width) / 2
        max_dy = (p1.height + p2.height) / 2
    
        # Allow small gaps / imperfections using tolerance
        horizontal = abs(dx - max_dx) <= tol and dy <= max_dy + tol
        vertical   = abs(dy - max_dy) <= tol and dx <= max_dx + tol
    
        result = horizontal or vertical
    
        if debug:
            print(f"""
    --- CHECKING PLOTS {p1.id} & {p2.id} ---
    centers: {p1.center} vs {p2.center}
    dx={dx}, max_dx={max_dx}, diff={abs(dx - max_dx)}
    dy={dy}, max_dy={max_dy}, diff={abs(dy - max_dy)}
    tol={tol}
    horizontal={horizontal}, vertical={vertical}
    RESULT={result}
    """)
    
        return result    



CROP_WATER_NEEDS = {
        "carrot": {"freq": 3, "amount": 2},
        "tomato": {"freq": 2, "amount": 3},
        "lettuce": {"freq": 1, "amount": 2},
        }

from config import  PLOTS, SUN_SCHEDULE

from services.service_exceptions import PlotError,  MemberNotInPlot
from enums import PlotStatus
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class PlotGenerationResult:
    plots: list               # all created plot objects
    large_pts: List[Tuple[int,int]]
    small_pts: List[Tuple[int,int]]
    total_large: int
    total_small: int
    
    total: int
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
        self.history_of_rentals = []
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

        self.watering_schedule = []

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

    def update_soil_state(self):
        # Extract recent activities
        recent_activities = self.activities[-10:]
    
        # --- Get last 3 crops ---
        recent_crops = [
            act["crop"]
            for act in recent_activities
            if act["type"] == "plant"
        ][-3:]
    
        # --- Get last fertilizer ---
        last_fertilizer = None
        for act in reversed(recent_activities):
            if act["type"] == "fertilize":
                last_fertilizer = act
                break
    
        # --- Rule 1: Organic fertilizer gives recovery boost (highest priority) ---
        if last_fertilizer and last_fertilizer.get("fertilizer") == "organic":
            self.soil_state = "recovering"
            return
    
        # --- Rule 2: Same crop repeated → depletion ---
        if len(recent_crops) >= 3 and len(set(recent_crops)) == 1:
            self.soil_state = "depleted"
            return
    
        # --- Rule 3: Crop diversity → healthy ---
        if len(recent_crops) >= 2 and len(set(recent_crops)) > 1:
            self.soil_state = "healthy"
            return
    
        # --- Default fallback ---
        self.soil_state = "neutral"

    def add_crop(self, user, crop_name):
        try:
            if user.name not in self.get_owners():
                raise MemberNotInPlot("Member doesn't own the plot")
    
            if self.current_crop_type and self.current_crop_type != crop_name:
                raise Exception("Conflict")
    
            self.last_crop = self.current_crop_type
            self.current_crop_type = crop_name
        
            self.activities.append({
                "type": "plant",
                "member": user.name,
                "crop": crop_name
            })
            self.update_soil_state()

            return PlotStatus.SUCCESS

        except PlotError as e:
            return PlotStatus.FAILED


    ## This operatoin should be considered accepted from both owners
    def update_current_crop(self, user, new_crop_name):
        try:
            if user.name not in self.get_owners():
                raise MemberNotInPlot("Member doesn't own the plot")
            self.current_crop_type = new_crop_name 

            return PlotStatus.SUCCESS
        except PlotError as e:
            return PlotStatus.FAILED


    def add_fertilizer(self, user, fert_type):
        try:
            if user.name not in self.get_owners():
                raise MemberNotInPlot("Member doesn't own the plot")
            self.activities.append({
                "type": "fertilize",
                "member": user.name,
                "fertilizer": fert_type
            })
            self.update_soil_state()

            return PlotStatus.SUCCESS
        except PlotError as e:
            return PlotStatus.FAILED
    

    def generate_watering_schedule(self):
        if not self.current_crop_type:
            return []

        crop = CROP_WATER_NEEDS.get(self.current_crop_type)
        if not crop:
            return []

        schedule = []
        for day in range(0, 14, crop["freq"]):  # 2-week plan
            schedule.append({
                "day": day,
                "amount": crop["amount"]
            })

        self.watering_schedule = schedule
        return schedule

    def generate_winter_tasks(self):
        tasks = []
    
        if self.soil_state == "depleted":
            tasks.append("Add heavy compost")
    
        if self.ph_level < 6:
            tasks.append("Add lime to raise pH")
    
        tasks.extend([
            "Remove dead plants",
            "Cover soil",
            "Clean tools"
        ])
    
        self.tasks = tasks  # overwrite instead of extend
        return tasks

    def get_activities(self):
        result = []
        for act in self.activities:
            result.append(act)

        return result

class PlotService():
    
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

    def generate_and_assign(self, allotment_width, allotment_height, road, plot_id_start=1):
        large_pts, small_pts = self.generate_layout(allotment_width, allotment_height, road)
    
        plots = []
        plot_id = plot_id_start
        alt_w = allotment_width
    
        # Create LARGE plots
        lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
        for x, y in large_pts:
            plot = self.create_plot(plot_id, "large", x, y, lw, lh)
            plot.assign_sun_profile(alt_w)
            plots.append(plot)
            plot_id += 1
    
        # Create SMALL plots
        sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"]
        for x, y in small_pts:
            plot = self.create_plot(plot_id, "small", x, y, sw, sh)
            plot.assign_sun_profile(alt_w)
            plots.append(plot)
            plot_id += 1
    
        # Assign neighbors
        self.assign_neighbors(plots)
    
        return PlotGenerationResult(
            plots=plots,
            large_pts=large_pts,
            small_pts=small_pts,
            total_large=len(large_pts),
            total_small=len(small_pts),
            total=len(large_pts)+len(small_pts)
        )

    def assign_neighbors(self, plots):
    
        for p1 in plots:
            p1.neighbors = []
            for p2 in plots:
                if p1.id == p2.id:
                    continue

                if self.are_neighbors(p1, p2):
                    p1.neighbors.append(p2)


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


    
      ## manually, or we can automate it with audit
    def alert_neighbors(self, plot):
        if plot.infection_status != "infected":
            return
        
        for neighbor in plot.neighbors:
            if neighbor:
                neighbor.alerts.append(f"Warning: Nearby infection from {plot.id} ({plot.infection_type})")



    def report_infection(self, plot, infection_type, date):
        plot.infection_status = "infected"
        plot.infection_type = infection_type
        plot.infection_date = date

        self.alert_neighbors(plot)



from config import SUN_SCHEDULE, CROP_WATER_NEEDS

## TODO: SMART PLOT

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
        if user.name not in self.get_owners():
            return False

        if self.current_crop_type and self.current_crop_type != crop_name:
            return False
            # raise Exception("Conflict")

        self.last_crop = self.current_crop_type
        self.current_crop_type = crop_name
    
        self.activities.append({
            "type": "plant",
            "member": user.name,
            "crop": crop_name
        })
        self.update_soil_state()

        return True


    ## This operatoin should be considered accepted from both owners
    def update_current_crop(self, user, new_crop_name):
        if user.name not in self.get_owners():
            return False

        self.current_crop_type = new_crop_name 

        return True


    def add_fertilizer(self, user, fert_type):
        if user.name not in self.get_owners():
            return False

        self.activities.append({
            "type": "fertilize",
            "member": user.name,
            "fertilizer": fert_type
        })
        self.update_soil_state()

        return False
    

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


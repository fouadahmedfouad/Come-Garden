from rental import Rental



CROP_WATER_NEEDS = {
        "carrot": {"freq": 3, "amount": 2},
        "tomato": {"freq": 2, "amount": 3},
        "lettuce": {"freq": 1, "amount": 2},
        }

class Plot:
    # --- identity & Geometry ---
    id: int
    size: str
    center: tuple

    width: int
    height: int
    area: int
    
    boundary: dict
    neighbors: list[int]
    status: str
   
    subPlots:list

    # --- Rental / Ownership ---
    waitlist: list
    season_waitlist:list

    rental: Rental
  

    # --- Environment ---
    sun_profile: dict
    soil_quality: str


    moisture_level: int


    # --- soil health ---
    soil_state: str
    ph_level: int
    fertilizer_history: list
  
    current_crop_type: None
    last_crop: None

    watering_schedule = []

    # --- Tasks & compliance ---
    tasks: list
    compliance_records: list

    # --- Pest ---
    infection_status: str
    infection_type: None
    infection_date: None


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

    def is_available(self):
        return self.rental is None or not self.rental.is_full()

    def get_owners(self):
        if self.rental and self.rental.participants:
            return [p.member.name for p in self.rental.participants]
        return []
    #
    # def set_sunlight(self, hours):
    #     self.sunlight_hours = hours
    #
    #     if hours >= 8:
    #         self.sunlight_level = "high"
    #     elif hours >= 5:
    #         self.sunlight_level = "medium"
    #     else:
    #         self.sunlight_level = "low"

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

    def add_crop(self, member_name, crop):
        self.last_crop = self.current_crop_type
        self.current_crop_type = crop
    
        self.activities.append({
            "type": "plant",
            "member": member_name,
            "crop": crop
        })

        self.update_soil_state()

    def add_fertilizer(self, member_name, fert_type):
        self.activities.append({
            "type": "fertilize",
            "member": member_name,
            "fertilizer": fert_type
        })
    
        self.update_soil_state()

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

    def report_infection(self, infection_type, date):
        self.infection_status = "infected"
        self.infection_type = infection_type
        self.infection_date = date


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

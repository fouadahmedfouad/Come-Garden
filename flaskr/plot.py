from .rental import Rental
class Plot:
    # --- identity & Geometry ---
    plot_id: int
    plot_size: str
    center: tuple

    width: int
    height: int
    area: int
    
    boundary: dict
    neighbors: list[int]
    status: str
    
    # --- Rental / Ownership ---
    rental: Rental
    co_owners: list
   
    # --- Environment ---
    sunlight_hours: int
    sunlight_level: str

    soil_type: str
    soil_quality: str
    moisture_level: int


    # --- soil health ---
    soil_state: str
    ph_level: int
    fertilizer_history: list
  
    current_crop_type: None
    last_crop: None
    crop_history: list

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
       
        self.zone = None
        self.sun_profile = None

        
        self.neighbors = []


        self.rental = None
      

        self.sunlight_hours = 0
        self.sunlight_level = None
        
        self.rental = None
        self.tasks = []

        self.soil_quality = soil_quality


    def is_available(self):
        return self.rental is None or not self.rental.is_full()

    def get_owners(self):
        if self.rental and self.rental.participants:
            return [p["member"].name for p in self.rental.participants]
        return []

    def set_sunlight(self, hours):
        self.sunlight_hours = hours

        if hours >= 8:
            self.sunlight_level = "high"
        elif hours >= 5:
            self.sunlight_level = "medium"
        else:
            self.sunlight_level = "low"


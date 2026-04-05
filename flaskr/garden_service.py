from datetime import datetime, timedelta

from rental import Rental 
from member import Member, Admin
from environment import TimeProvider, Season

from toolLib import ToolLibrary
from seedBank import SeedBank
from tasks    import VolunteerSystem 
from market   import Marketplace

from config import  PLOTS, PLOT_PRICING, SOIL_PRICE_MODIFIER, MEMBERSHIP_DISCOUNT, SUN_SCHEDULE


class Garden():

    def __init__(self,width,height,road=2):
        self.allotment_width = width
        self.allotment_height = height
        self.road = road 
        
        self.members = {}
        self.seasons = ()
        
        self.current_season = None
        self.time_provider = TimeProvider()

       
        self.plots = {}
        self.plots_by_type = {"large":[],"small":[] }
      
        self.tool_library = ToolLibrary()
        self.seed_bank = SeedBank()
        self.volunteer_system = VolunteerSystem()
        self.market_place = Marketplace()
      
        self.errno = 0

    def plot_maker(self):
        large_pts,small_pts = self.generate_layout()

        alt_w = self.allotment_width # used for sun exposure
        plot_id = 1 

        # LARGE
        lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
        for (x,y) in large_pts:
            plot = self.create_plot(plot_id,"large",x,y,lw,lh)
            self.assign_sun_profile(plot,alt_w) 
            self.add_plot(plot,"large")
            plot_id += 1

        # SMALL 
        sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"] 
        if small_pts:
            for (x,y) in small_pts:
                plot = self.create_plot(plot_id,"small",x,y,sw,sh) 
                self.assign_sun_profile(plot,alt_w) 
                self.add_plot(plot,"small")
                plot_id += 1

        self.assign_neighbors()

        self.totalLargePlots = len(large_pts)
        self.totalSmallPlots = len(small_pts)
        self.totalPlots = len(large_pts) + len(small_pts)

        self.large_pts = large_pts
        self.small_pts = small_pts


class GardenService():
    


from datetime import timedelta, datetime

from member import Member, Admin
from environment import TimeProvider, EnvService

from services.plot_service import PlotService
from services.rental_service import RentalService, Application

from features.toolLibrary.tool_library import ToolLibrary
from features.seedBank.seed_bank import SeedBank
from features.volunteerSystem.volunteer_system import VolunteerSystem 
from features.marketPlace.market_place   import Marketplace


from config import  PLOTS

class Garden:

    def __init__(self,width,height,road=2):
        self.allotment_width = width
        self.allotment_height = height
        self.road = road 

        self.plot_service = PlotService()
        self.rental_service = RentalService()


        self.members = {}
        self.members_by_name = {}

        self.time_provider = TimeProvider() 
        self.env_service = EnvService(region="EG")
        self.env_service.initialize()

      
        self.plots = {}
      
        self.tool_library = ToolLibrary()
        self.seed_bank = SeedBank()
        self.volunteer_system = VolunteerSystem()
        self.market_place = Marketplace()
      


    def _generate_member_id(self):
        return len(self.members) + 1

    def join_member(self, name):
        if name in self.members_by_name:
            raise ValueError("Member already exists")
    
        member_id = self._generate_member_id()
        member = Member(member_id, name)
    
        self.members[member_id] = member
        self.members_by_name[name] = member
    
        return member
    
    def plot_maker(self):
        """ Construct the plots """

        result = self.plot_service.generate_and_assign(
            self.allotment_width, self.allotment_height, self.road
        )
    
        for plot in result.plots:
            self.add_plot(plot)
    
        self.totalLargePlots = result.total_large
        self.totalSmallPlots = result.total_small
        self.totalPlots = result.total
        self.large_pts = result.large_pts
        self.small_pts = result.small_pts


    def audit_rental_end(self):
        """ End rentals by the end of the season (end of the rental) """

        today = self.time_provider.now()
        current_season = self.get_current_season()
        new_season = self.get_next_season()
        last_day = current_season.last_day()

        if today >= last_day:
            self.env_service.update_current_season()

        for plot in self.plots.values():
            if not  plot.rental: 
                continue
            
            self.rental_service.end_rentals(plot, new_season)

    def audit_rent_plots(self):
       """ Process the plot applications """

       today = self.time_provider.now() 
       current_season = self.get_current_season()
       last_day = current_season.last_day()
       
       # close the window before the end of the season of 15 days
       if today < last_day - timedelta(days=15):
           for plot in self.plots.values():  
            if plot.is_available():
                self.rental_service.rent_plots(plot, current_season)

    def audit_rental_alert(self):
        """ Alert before 15 days of the end of the season """

        today = self.time_provider.now()
        current_season = self.get_current_season()
        last_day = current_season.last_day()
       


        if today >= last_day - timedelta(days=15):
            for plot in self.plots.values():  
                if not plot.rental:
                    continue
                
                self.rental_service.rental_alert(plot)



    ## TODO: then add audit to rebuild seasons for new season

    def build(self): 
        self.plot_maker()
        return self

    def get_current_season(self):
        return self.env_service.get_current_season()

    def get_next_season(self):
        return self.env_service.get_next_season() 

    def add_plot(self,plot):
        self.plots[plot.id] = plot

 #    def cad_render(self):
 #        try: 
 #            from ocp_vscode  import show
 #            from cadquery import cq
 #    
 #        except ImportError:
 #            raise RuntimeError("cad_render requires cadquery and ocp_vscode installed")
 #    
 #        large_pts = self.large_pts
 #        small_pts = self.small_pts
 #    
 #        alt_w = self.allotment_width
 #        alt_h = self.allotment_height
 #        
 #        lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
 #        sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"] 
 #    
 #        alt_thickness = 1
 #        plt_thickness = 3
 #        
 #        allotment = cq.Workplane("front").rect(alt_w,alt_h).extrude(alt_thickness)
 #        if large_pts:
 #            allotment = allotment.pushPoints(large_pts).rect(lw, lh).extrude(plt_thickness)
 #        if small_pts:
 #            allotment = allotment.pushPoints(small_pts).rect(sw, sh).extrude(plt_thickness)
 # 
 #        show(allotment, reset_camera=True)        
 #

garden = Garden(150,60).build()
#garden.cad_render()

admin = Admin(100,"Garden Admin")
garden.members[100] = admin

Fouad = garden.join_member("Fouad")
Mina = garden.join_member("Mina")
David = garden.join_member("David")
Ria = garden.join_member("Ria")
Saged = garden.join_member("Saged")
Steven = garden.join_member("Steven")


Fouad.add_credits(200)
Mina.add_credits(200)




## RENT TEST (Fouad)
# garden.rental_service.apply(Fouad, garden.plots[1],share=0.5,auto_renew=False)
# garden.rental_service.apply(Mina, garden.plots[1],share=1)
#
# print(garden.plots[1].waitlist)
# garden.audit_rent_plots()
#
# print(garden.plots[1].get_owners())
# garden.audit_rental_end()
# print(garden.plots[1].get_owners())


### Planting Test
#
# my_plot = garden.plots[1]
#
# garden.rental_service.apply(Fouad, my_plot,share=0.5)
# garden.rental_service.apply(Mina, my_plot,share=0.5)
# garden.audit_rent_plots()
#
# result = my_plot.add_crop(Fouad,"tomato")
# my_plot.add_crop(Mina,"tomato")
# my_plot.add_crop(Mina,"tomato")
#
# my_plot.add_fertilizer(Fouad, "organic")
# garden.plot_service.report_infection(my_plot, "infection type", garden.time_provider.now())
#
# my_plot.generate_watering_schedule()
# my_plot.generate_winter_tasks()
#
# print(my_plot.neighbors)
# print(garden.plots[2].alerts)
# print(garden.plots[5].alerts)
# print(garden.plots[6].alerts)




### Tool library Test (Steven)
#
# # admin add tools
# print(garden.tool_library.add_tool(admin, "Rototiller", usage_status="high", maintenance_threshold_hours=5).success)
#
# # Fouad books a tool
# print(garden.tool_library.book_tool(Fouad, "Rototiller", duration_hours=10).success)
#
# # Steven try to book the same tool
# print(garden.tool_library.book_tool(Steven, "Rototiller", duration_hours=10).success)
#
#
# # Fouad returns the tool (the waitlist automatically proccessed and Steven gets the tool)
# print(garden.tool_library.return_tool(Fouad.bookings[0], cleaned=True).success)
# # Steven returns the tool (the waitlist automatically proccessed and the tool now is available)
# print(garden.tool_library.return_tool(Steven.bookings[0], cleaned=True).success)
#
# # Fouad report damage 
# print(garden.tool_library.report_damage(Fouad.bookings[0], severity="medium").success)
# print(vars(Fouad.bookings[0]))


### Bank Test 

# ## admin add inventory itmes
# garden.seed_bank.add_inventory_item(admin, "Fertilizer", quantity=5, reorder_threshold=10)
#
# # admin does checks
# garden.seed_bank.check_inventory_alerts(admin)
# garden.seed_bank.check_seed_health(admin)
#
#
# # Steven deposit high quaility tomato
# garden.seed_bank.deposit(Steven, "tomato", quantity=10, viability=90, origin="Roma", gt_flag=True, age=5)
#
# # Steven withdraw tomato
# garden.seed_bank.withdraw(Steven,"tomato", quantity=5)
#
# # debug
# garden.seed_bank.print_state()
#


### Volunteer Test (Saged)

## add shift & autmoatically check weather
shift_result = garden.volunteer_system.add_shift(admin, datetime.now(), duration_days=15)
print(shift_result.success)

admin.shifts[0].add_task("Turn Compost",9,"heavy")
admin.shifts[0].add_task("Turn Compost",9,"heavy")

# print(admin.shifts)
# print(admin.shifts[0].tasks)

members = [Fouad, Saged]
print(garden.volunteer_system.assign(admin,admin.shifts[0],members).success)

print("Fouad's tasks", Fouad.tasks)
print("Saged's tasks", Saged.tasks)

print(garden.volunteer_system.complete_shift(admin, admin.shifts[0]).success)
print("the shift", shift_result.shift.status)

Fouad.tasks[0].complete_assignment()


# Fouad requests a swap
print(garden.volunteer_system.request_swap(Fouad, Saged, Saged.tasks[0]).success)

# Saged Approves or Reject
print(garden.volunteer_system.reject_swap(Saged, Saged.swap_reqs[0]).success)
print(Fouad.sent_swap_reqs[0].status)



## MarketPlace Test (Mina)
#
# # Fouad creates listings
# print(garden.market_place.create_listing(Fouad,"tomato",10,"normal","potato").success)
# print(garden.market_place.ask_question(Fouad, "How to avoid over planting", 10).success)
#
#
#  # Mina view trades & questions
# listings = garden.market_place.get_listings(Mina)
# questions = garden.market_place.get_questions(Mina)
# print("The market listings: ", listings)
# print("The mareket questions: ", questions)
#
#
# ## Mina trades
# print(garden.market_place.request_trade(Mina, listings[0]).success)
# #
#
# # ## Mina answers questions
# print(garden.market_place.answer_question(Mina,  questions[0], "Try to divide your normal estimate by 2, and you will mostly be fine").success)
#
# # Fouad view his listing's trades
# listing_trades = Fouad.listings[0].get_trades()
# print("Your listing's trades", listing_trades)
#
# # # Fouad view his question's answer
# question_answers = Fouad.questions[0].get_answers()
# print("Yr Q's answers", question_answers)
#
# # # Fouad accept trade
# print(garden.market_place.complete_trade(Fouad, listing_trades[0]).success)
#
# # # # Fouad accept answer
# print(garden.market_place.accept_answer(Fouad,Fouad.questions[0],question_answers[0]).success)
#




# ## The system checks plots rentals everyday, the application is satisfied after 24 hours
# ## if the plot is available and all requirments are satasifed (eg., enough credits)
# ## the plot is rented, Otherwise the member is added to season waitlist that will be proccessed
# ## by the end of the season.

# garden.audit_rental_alert()
# garden.audit_rental_end()
# garden.audit_rent_plots()


## Resolve penality routine


## Remove expired routine, and reorder inventory


### Audit for updating ledger every month


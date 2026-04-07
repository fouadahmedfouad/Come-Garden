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
      
    def cad_render(self):
        try: 
            from ocp_vscode  import show
            from cadquery import cq
    
        except ImportError:
            raise RuntimeError("cad_render requires cadquery and ocp_vscode installed")
    
        large_pts = self.large_pts
        small_pts = self.small_pts
    
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        
        lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
        sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"] 
    
        alt_thickness = 1
        plt_thickness = 3
        
        allotment = cq.Workplane("front").rect(alt_w,alt_h).extrude(alt_thickness)
        if large_pts:
            allotment = allotment.pushPoints(large_pts).rect(lw, lh).extrude(plt_thickness)
        if small_pts:
            allotment = allotment.pushPoints(small_pts).rect(sw, sh).extrude(plt_thickness)
 
        show(allotment, reset_camera=True)        

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
        today = self.time_provider.now()
        current_season = self.get_current_season()
        new_season = self.get_next_season()
        last_day = current_season.last_day()

        today = last_day ## debug

        for plot in self.plots.values():
            old_rental = plot.rental
            if not old_rental:
                continue

            ## LAST DAY OF THE SEASON 
            if today >= last_day:
                # print(f"Today is the day for ending plot {plot.id} rental")

                ## UPDATE CURRENT SEASON 
                self.env_service.update_current_season()

                plot.rental = None

                ## Renew autos

                plot.waitlist = []
                for p in old_rental.participants:
                    if p.auto_renew:
                        self.apply(p.member, plot.id,p.share,p.auto_renew)
                    else:
                        p.status = "Terminated"
                if plot.waitlist:
                    self.process_waitlist(plot,plot.waitlist, new_season) 

                ## Rent the rest
                plot.season_waitlist.sort(key=lambda app: app.score, reverse=True)            

                self.process_waitlist(plot, plot.season_waitlist, new_season)
                plot.season_waitlist = []

            old_rental.status = "Expired"
            plot.history_of_rentals.append(old_rental)

    def audit_rent_plots(self):
       today = self.time_provider.now() 
       current_season = self.get_current_season()
       last_day = current_season.last_day()

       for plot in self.plots.values():  
           if today < last_day:
                if plot.is_available():
                    plot.season_waitlist.sort(key=lambda app: app.score, reverse=True)
                    self.process_waitlist(plot,plot.waitlist)
                    plot.waitlist = []


    def audit_rental_alert(self):
        ## Alert before 15 days of the end of the season
        today = self.time_provider.now()
        current_season = self.get_current_season()
        last_day = current_season.last_day()
       

        #today = self.current_season.end_date - timedelta(days=10) ## debug

        for plot in self.plots.values():  
            if not plot.rental:
                continue
                
            if today >= last_day - timedelta(days=15):
            
                for p in plot.rental.participants:
                
                    if p.auto_renew:
                        p.status = "ExpiringSoon" # check your credits for renewal
                    else:
                        p.status = "PendingTermination" 

    def process_waitlist(self, plot, waitlist, season=None):
        current_season = season
        
        if not current_season:
        # Add plots to the manager
            current_season = self.get_current_season() 
            
        for app in waitlist:
            self.rental_service._rent_plot(plot,app.member,current_season,app) 

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

    def apply(self, user, plot_id, share=1.0, auto_renew=False):
        plot = self.plots.get(plot_id)
    
        if not user or not plot:
            return
    
        application = Application(user, plot, share, auto_renew)
        plot.waitlist.append(application)

        return application

      ## manually, or we can automate it with audit
    def alert_neighbors(self, plot_id):
        plot = self.plots[plot_id]

        if plot.infection_status != "infected":
            return []
        
        for neighbor_id in plot.neighbors:
            neighbor = self.plots.get(neighbor_id)

            if neighbor:
                neighbor.alerts.append(f"Warning: Nearby infection from {plot.id} ({plot.infection_type})")


    ## LAYERED APPROACH (if we need to prevent user from adding crops to other plots in the garden)
    ## Okay, we need so, but LAYERED APPROACH VS SMART PLOTS. Smart plot it is


garden = Garden(150,60).build()
garden.cad_render()

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




### RENT TEST
# garden.apply(Fouad, garden.plots[1].id,0.5,False)
# garden.apply(Mina, garden.plots[1].id,1)

# print(garden.plots[1].waitlist)
# garden.audit_rent_plots()

# print(garden.plots[1].get_owners())
# garden.audit_rental_end()
# print(garden.plots[1].get_owners())


### Planting Test

# my_plot = garden.plots[1]

# garden.apply(Fouad, my_plot.id,0.5)
# garden.apply(Mina, my_plot.id,0.5)
# garden.audit_rent_plots()

# result = my_plot.add_crop(Fouad,"tomato")
# my_plot.add_crop(Mina,"tomato")
# my_plot.add_crop(Mina,"tomato")

# my_plot.add_fertilizer(Fouad, "organic")
# my_plot.report_infection("infection type", garden.time_provider.now())

# my_plot.generate_watering_schedule()
# my_plot.generate_winter_tasks()

# print(my_plot.neighbors)
# garden.alert_neighbors(my_plot.id)
# print(garden.plots[2].alerts)
# print(garden.plots[5].alerts)
# print(garden.plots[6].alerts)




### Tool library Test

## admin add tools
# garden.tool_library.add_tool(admin, "Rototiller", usage_status="high", maintenance_threshold_hours=5)

# # Fouad books a tool
# booking = garden.tool_library.book_tool(Fouad, "Rototiller", duration_hours=10)
# booking2 = garden.tool_library.book_tool(Steven, "Rototiller", duration_hours=10)


# # Fouad returns the tool 

# garden.tool_library.return_tool(Fouad.booking_ids[0], cleaned=True)
# print(garden.tool_library.tools[booking.booking.tool_name].status)
# garden.tool_library.return_tool(Steven.booking_ids[0], cleaned=True)
# print(garden.tool_library.tools[booking.booking.tool_name].status)

# # Fouad report damage 
# garden.tool_library.report_damage(Fouad.booking_ids[0], severity="medium")



### Bank Test

# ## admin add inventory itmes
# print(garden.seed_bank.add_inventory_item(admin, "Fertilizer", quantity=5, reorder_threshold=10))

# # admin does checks
# print(garden.seed_bank.check_inventory_alerts(admin))
# print(garden.seed_bank.check_seed_health(admin))


# # Fouad deposit high quaility tomato
# print(garden.seed_bank.deposit(Steven, "tomato", quantity=10, viability=90, origin="Roma", gt_flag=True, age=5))

# # Fouad withdraw tomato
# print(garden.seed_bank.withdraw(Steven,"tomato", quantity=5))





### Volunteer Test

# print(garden.volunteer_system.add_shift(admin, 
#                                         datetime.now()))

# print(garden.volunteer_system.add_task(admin, 
#                                        shift_id=admin.shifts_ids[0],task_name="Turn Compost", difficulty_score=9, category="heavy"))

# weather = "heavy_rain"
# print(garden.volunteer_system.check_weather(admin,
#                                              shift_id=admin.shifts_ids[0],weather=weather))


# members = [Fouad, Saged]
# print(garden.volunteer_system.assign_members_to_shift(admin, 
#                                                       shift_id=admin.shifts_ids[0],members=members))

# ## Fouad requests a swap
# print(garden.volunteer_system.request_swap(Fouad,target=Saged, shift_id=Saged.shifts_ids[0]))

# ## Saged Approves
# print(garden.volunteer_system.approve_swap(Saged, Saged.swaps_req_ids[0]))






## MarketPlace Test

# # Fouad creates listings
# print(garden.market_place.create_listing(Fouad,"tomato",10,"normal","potato"))
# print(garden.market_place.ask_question(Fouad, "How to avoid over planting", 10))


#  # Mina view trades & questions
# listings = garden.market_place.get_listings(Mina)
# questions = garden.market_place.get_questions(Mina)
# print(listings)
# print(questions)


# ## Mina trades
# print(garden.market_place.request_trade(Mina, listings[0].id))

# # ## Mina answers questions
# print(garden.market_place.answer_question(Mina,  questions[0].id, "Try to divide your normal estimate by 2, and you will be fine"))

# # Fouad view his listing's trades
# listing_trades = garden.market_place.get_trades_by_listing(Fouad, Fouad.listings_ids[0])
# print(listing_trades)

# # # Fouad view his question's answer
# question_answers = garden.market_place.get_answers_by_question(Fouad, Fouad.questions_ids[0])
# print(question_answers)


# # # Fouad accept trade
# print(garden.market_place.complete_trade(Fouad, listing_trades[0].id))

# # # # Fouad accept answer
# print(garden.market_place.accept_answer(Fouad,Fouad.questions_ids[0],question_answers[0].id))























# Fouad = garden.join_member("Fouad Ahmed Fouad")
# Mina = garden.join_member("Mina")
# David = garden.join_member("David")
# Ria = garden.join_member("Ria")
# Saged = garden.join_member("Saged")
# Steven = garden.join_member("Steven")


# plot1 = garden.plots[1]
# plot2 = garden.plots[2]
# plot3 = garden.plots[3]


# garden.apply(Fouad, plot1.id, 1)
# garden.apply(Mina, plot1.id, 1)

# garden.audit_rental_alert()
# garden.audit_rental_end()
# garden.audit_rent_plots()



# # print("\n--- Soil State Test ---")

# garden.add_crop(Mina, plot1.id, "carrot")
# garden.add_crop(Mina, plot1.id, "carrot")
# garden.add_crop(Mina, plot1.id, "carrot") ## soil state depleted

# garden.add_fertilizer(Mina, plot1.id,"organic")  ## recovering the soil


# garden.new_crop(Mina, plot1.id, "tomato")

# garden.report_infection(Mina, plot1.id, "potato_blight", datetime.now())



# ## audit
# garden.generate_watering_schedule(Mina, plot1.id)
# garden.propagate_infections(Mina)
# garden.seasonal_update(Mina)


## Admin

# ## The system checks plots rentals everyday, the application is satisfied after 24 hours
# ## if the plot is available and all requirments are satasifed (eg., enough credits)
# ## the plot is rented, Otherwise the member is added to season waitlist that will be proccessed
# ## by the end of the season.

# garden.audit_rental_alert()
# garden.audit_rental_end()
# garden.audit_rent_plots()


# ## Resolve penality routine

# #### Bank

# ## Remove expired routine, and reorder inventory


# print(garden.volunteer_system.complete_shift(admin, admin.shifts_ids[0]).status)


# ### Audit for updating ledger every month


# ## Member

# # Credits
# Fouad.add_credits(200)



# ## Fouad Choose plot0 and apply for rent
# plot0 = garden.plots[1]
# garden.apply(Fouad,plot0.id, share=1)
# garden.apply(Mina, plot0.id, share=1)






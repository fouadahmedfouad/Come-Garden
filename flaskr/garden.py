from datetime import datetime, timedelta

from member import Member, Admin
from environment import TimeProvider, EnvService

from plot_service import PlotService
from rental_service import RentalService, Application

from toolLib import ToolLibrary
from seedBank import SeedBank
from tasks    import VolunteerSystem 
from market   import Marketplace

from config import  PLOTS

from enums import RentalStatus
from exceptions import (RentalError, PermissionDeniedError)

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
      
    # def cad_render(self):
    #     try: 
    #         from ocp_vscode  import show
    #         from cadquery import cq
    
    #     except ImportError:
    #         raise RuntimeError("cad_render requires cadquery and ocp_vscode installed")
    
    #     large_pts = self.large_pts
    #     small_pts = self.small_pts
    
    #     alt_w = self.allotment_width
    #     alt_h = self.allotment_height
        
    #     lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
    #     sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"] 
    
    #     alt_thickness = 1
    #     plt_thickness = 3
        
    #     allotment = cq.Workplane("front").rect(alt_w,alt_h).extrude(alt_thickness)
    #     if large_pts:
    #         allotment = allotment.pushPoints(large_pts).rect(lw, lh).extrude(plt_thickness)
    #     if small_pts:
    #         allotment = allotment.pushPoints(small_pts).rect(sw, sh).extrude(plt_thickness)
 
    def rent_plot(self, plot, member, season, record):
        try:
            result = self.rental_service._rent_plot(
                plot, member, season, record
            )

            if result.status == RentalStatus.SUCCESS:
                # print(f"Plot {plot.id} rented successfully")
                pass

            elif result.status == RentalStatus.WAITLISTED:
                # print(f"Plot {plot.id} is full → added to next season")
                pass

            return result

        except RentalError as e:
            print(f"Rental failed: {e}")
            return None

        except Exception as e:
            # Unexpected system errors
            print(f"[Critical] Unexpected failure in rental system: {e}")
            return None
 
        
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
        large_pts,small_pts = self.plot_service.generate_layout(self.allotment_width,self.allotment_height,self.road)

        alt_w = self.allotment_width # used for sun exposure
        plot_id = 1 

        # LARGE
        lw, lh = PLOTS["large"]["w"], PLOTS["large"]["h"]
        for (x,y) in large_pts:
            plot = self.plot_service.create_plot(plot_id,"large",x,y,lw,lh)
            plot.assign_sun_profile(alt_w) 
            self.add_plot(plot)
            plot_id += 1

        # SMALL 
        sw, sh = PLOTS["small"]["w"], PLOTS["small"]["h"] 
        if small_pts:
            for (x,y) in small_pts:
                plot = self.plot_service.create_plot(plot_id,"small",x,y,sw,sh) 
                plot.assign_sun_profile(alt_w) 
                self.add_plot(plot)
                plot_id += 1

        ## NOTE: WE'RE PASSING THE PLOTS
        self.plot_service.assign_neighbors(self.plots.values())

        self.totalLargePlots = len(large_pts)
        self.totalSmallPlots = len(small_pts)
        self.totalPlots = len(large_pts) + len(small_pts)

        self.large_pts = large_pts
        self.small_pts = small_pts  

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
                ## TODO: WAITLIST CONTAINS APPLICATIONS
                plot.season_waitlist.sort(reverse=True)

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
                    
                    ## TODO: WAITLIST CONTAINS APPLICATIONS
                    ## AND WHERE is the sorting?

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
            current_season = self.get_current_season() 
            
        for app in waitlist:
            self.rent_plot(plot,app.member,current_season,app) 

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






    def admin_required(func):
        def wrapper(self, user, *args, **kwargs):
            if not getattr(user, "is_admin", False):
                raise PermissionDeniedError("Admin privileges required")
            return func(self, user, *args, **kwargs)
        return wrapper
   
  ##  -------- Rent ---------
  
    def apply(self, user, plot_id, share=1.0, auto_renew=False):
        plot = self.plots.get(plot_id)
    
        if not user or not plot:
            return
    
        application = Application(user, plot, share, auto_renew)
        plot.waitlist.append(application)

    
#     ## -------- Seed Bank --------
    
#     def deposit(self, user, seed_type, quantity, viability, origin, gt_flag, age, lah=True):
#         batch_info = self.seed_bank.create_batchInfo(
#             viability, age, gt_flag, origin, lah
#         )
#         batch = self.seed_bank.create_batch(seed_type, quantity, batch_info)
    
#         self.seed_bank.deposit(user.id, batch)
    
    
#     def withdraw(self, user, seed_type, quantity):
#         withdrawn = self.seed_bank.withdraw(user.id, seed_type, quantity)
#         if withdrawn:
#             user.inventory.append(withdrawn)
    
    
#     ## -------- Volunteer --------
    
#     @admin_required
#     def create_shift(self, user, date):
#         shift = self.volunteer_system.create_shift(date)
#         user.shifts_ids.append(shift.shift_id)
    
    
#     @admin_required
#     def create_task(self, user, shift_id, name, difficulty, category):
#         self.volunteer_system.add_task(shift_id, name, difficulty, category)
    
    
#     @admin_required
#     def assign_members(self, user, shift_id, members_ids):
#         for mid in members_ids:
#             member = self.members.get(mid)
#             member.shifts_ids.append(shift_id)

#         self.volunteer_system.assign_members_to_shift(shift_id, members_ids)

#     @admin_required      
#     def check_weather(self, user, shift_id,weather):
#         garden.volunteer_system.check_weather(shift_id, weather)


#     def request_swap(self, user, target_id , shift_id):
#         target = self.members.get(target_id)

#         swap = garden.volunteer_system.request_swap(user.id,target_id,shift_id)
#         target.swaps_req_ids.append(swap.request_id)

#     def approve_swap(self, user, req_id):
#         garden.volunteer_system.approve_swap(req_id)

#         ## remove the req_id from the user
#         user.swaps_req_ids.remove(req_id)


#     # ------- Market Place --------
#     def create_listing(self,user, item, quantity, listing_type, request=None):
#         listing = garden.market_place.create_listing(user.id, item, quantity, listing_type, request)
#         if listing:
#             user.listings_ids.append(listing.id) 

#     def trade(self, user, listing_id):
#         garden.market_place.request_trade(listing_id, user.id)

#     def complete_trade(self, user, trade_id):
#         garden.market_place.complete_trade(trade_id, user.id)

#     def get_listings(self, user):
#         return garden.market_place.get_listings()
    
#     def get_my_trades(self, user):
#         return garden.market_place.get_my_trades(user.id)
 
#     def get_trades_by_listing(self, user, listing_id):
#         return garden.market_place.get_trades_by_listing(listing_id)

#     def ask_question(self, user, content, bounty):
#         q = garden.market_place.ask_question(user.id, content,bounty)
#         if q:
#             user.questions_ids.append(q.id)
#             user.credits -= q.bounty

#         return q

#     def answer_question(self, user, question_id, content):
#         garden.market_place.answer_question(user.id, question_id, content)

#     def get_questions(self, user):
#         return garden.market_place.get_questions()
    
#     def get_answers_by_question(self, user, question_id):
#         return garden.market_place.get_answers_by_question(Fouad.questions_ids[0])
 
#     def accept_answer(self, user, question_id, answer_id):
#         answer = garden.market_place.accept_answer(question_id,answer_id)
#         responder = self.members[answer.responder_id]

#         responder.credits += q.bounty

    ## manually, or we can automate it with audit
    def alert_neighbors(self, plot_id):
        plot = self.plots[plot_id]

        if plot.infection_status != "infected":
            return []
        
        for neighbor_id in plot.neighbors:
            neighbor = self.plots.get(neighbor_id)

            if neighbor:
                neighbor.alerts.append(f"Warning: Nearby infection from {plot.id} ({plot.infection_type})")

    # def seasonal_update(self,user):
    #     for plot in self.plots.values():
    #         plot.generate_winter_tasks()

    # def propagate_infections(self):
    #     all_alerts = []
    #     for plot_id in self.plots:
    #         alerts = self.alert_neighbors(plot_id)
    #         all_alerts.extend(alerts)
    #     return all_alerts



    ## LAYERED APPROACH (if we need to prevent user from adding crops to other plots in the garden)
    ## Okay, we need so, but LAYERED APPROACH VS SMART PLOTS

# TODO: Moving all these other stuff into Services
        
garden = Garden(100,50).build()
admin = Admin(100,"Fouad Ahmed")
garden.members[100] = admin




### RENT TEST

Fouad = garden.join_member("Fouad Ahmed Fouad")
Mina = garden.join_member("Mina")

Fouad.add_credits(200)
Mina.add_credits(200)

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

# admin add tools
# garden.tool_library.add_tool(admin, "Rototiller", usage_status="high", maintenance_threshold_hours=5)

# # Fouad books a tool
# booking = garden.tool_library.book_tool(Fouad, "Rototiller", duration_hours=10)
# booking2 = garden.tool_library.book_tool(Mina, "Rototiller", duration_hours=10)


# # Fouad returns the tool 

# garden.tool_library.return_tool(Fouad.booking_ids[0], cleaned=True)
# print(garden.tool_library.tools[booking.tool_name].status)
# garden.tool_library.return_tool(Mina.booking_ids[0], cleaned=True)
# print(garden.tool_library.tools[booking.tool_name].status)

# # Fouad report damage 
# garden.tool_library.report_damage(Fouad.booking_ids[0], severity="medium")











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


# #### Volunteer

# garden.create_shift(admin, datetime.now())
# garden.create_task(admin, admin.shifts_ids[0],"Turn Compost", 9, "heavy")

# weather = "heavy_rain"
# garden.check_weather(admin,admin.shifts_ids[0],weather)


# members_ids = [Fouad.id, Mina.id]
# garden.assign_members(admin, admin.shifts_ids[0],members_ids)

# ### Audit for updating ledger every month


# ## Member

# # Credits
# Fouad.add_credits(200)



# ## Fouad Choose plot0 and apply for rent
# plot0 = garden.plots[1]
# garden.apply(Fouad,plot0.id, share=1)
# garden.apply(Mina, plot0.id, share=1)



# ### Bank
# garden.deposit(Steven, "Tomato", quantity=10, viability=90, origin="Roma", gt_flag=True, age=5)
# garden.withdraw(Steven,"Tomato", quantity=5)





# #### Volunteer
# ## Fouad requests a swap
# garden.request_swap(Fouad, Mina.id, Fouad.shifts_ids[0])
# ## Mina Approve
# garden.approve_swap(Mina, Mina.swaps_req_ids[0])



# ### MarketPlace

# garden.create_listing(Fouad,"tomato",10,"normal","potato")
# q = garden.ask_question(Fouad, "How to avoid over planting", 10)


# ## Mina view trades & questions
# listings = garden.get_listings(Mina)
# questions = garden.get_questions(Mina)

# ## Mina trades
# garden.trade(Mina, listings[0].id)

# ## Mina answers questions
# garden.answer_question(Mina,  questions[0].id, "Try to divide your normal estimate by 2, and you will be fine")

# # Fouad view his listing's trades
# listing_trades = garden.get_trades_by_listing(Fouad, Fouad.listings_ids[0])

# # Fouad view his question's answer
# question_answers = garden.get_answers_by_question(Fouad, Fouad.questions_ids[0])

# # Fouad accept trade
# garden.complete_trade(Fouad, listing_trades[0].id)

# # Fouad accept answer
# garden.accept_answer(Fouad,Fouad.questions_ids[0],question_answers[0].id)

# # print(q.status)


# # print(Mina.credits)
# # print(Fouad.credits)








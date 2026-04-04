from datetime import datetime, timedelta

from rental import Rental 
from plot import Plot
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

    @staticmethod
    def build_seasons(year):
        return [
            Season("Spring", datetime(year, 3, 1).date(), datetime(year, 5, 31).date()),
            Season("Summer", datetime(year, 7, 1).date(), datetime(year, 10, 31).date()),
            Season("Fall", datetime(year, 11, 1).date(), datetime(year, 11, 30).date()),
            Season("Winter", datetime(year, 12, 1).date(), datetime(year + 1, 2, 28).date()),
        ]
    
    def update_current_season(self):
        today = self.time_provider.now()
    
        for season in self.seasons:
            if season.start_date <= today <= season.end_date:
                self.current_season = season
                return
    
        self.current_season = None

    def get_next_season(self):
        today = self.time_provider.now()
    
        for season in self.seasons:
            if season.start_date > today:
                return season
    
        return None
    
    def assign_zone(self,x):
        if x < 0.25:
            return "left"
        elif x < 0.75:
            return "middle"
        else:
            return "right"
    
    def assign_sun_profile(self, plot, alt_w):
        x, _ = plot.center
    
        # normalize + clamp [0,1]
        nx = (x + alt_w / 2) / alt_w
        nx = max(0, min(nx, 1))
    
        zone = self.assign_zone(nx)
    
        plot.zone = zone
        plot.sun_profile = SUN_SCHEDULE[zone] 
 
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

    def add_plot(self,plot,plot_size):
        self.plots[plot.id] = plot
        self.plots_by_type[plot_size].append(plot)
    
    def cad_render(self):
        try: 
            import cadquery as cq
            from ocp_vscode import show
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
   
    def generate_points(self,start_x, start_y, step_x, step_y, count_x, count_y):
        return [
            (start_x + i * step_x, start_y + j * step_y)
            for i in range(count_x)
            for j in range(count_y)
        ]
    
    def generate_layout(self):
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        road  = self.road
        
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
    

    def assign_neighbors(self):
        plots = list(self.plots.values())
    
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

    def join_member(self,memberFullName):
        for member in self.members.values():
            if member.name == memberFullName:
                return f"{member.name} Already exist with Id {member.id}"
        
        member_id = len(self.members)
        member = Member(member_id,memberFullName)
        self.members[member.id] = member

        ## TODO:ADD member to voulnteer system ledger
        
        return member
    
    def get_member_tier_factor(self,member):
        count = len(member.rental_history)

        if count < 2:
            return 1.0
        elif count < 5:
            return 0.9
        else:
            return 0.8
    
    def calculate_rent(self, plot_id, member_id):
        plot = self.plots.get(plot_id)
        member= self.members[member_id]

        base = PLOT_PRICING[plot.size]
        soil_factor = SOIL_PRICE_MODIFIER.get(plot.soil_quality, 1)
        discount    = MEMBERSHIP_DISCOUNT.get(member.type, 1)
        tier_factor = self.get_member_tier_factor(member)

        return base * soil_factor * discount * tier_factor

    def calculate_residency_duration(self,member_id):
        member = self.members.get(member_id)
        total_days = 0
    
        for rental in member.rental_history:
            start = rental.start_date
            end   = rental.end_date
            total_days += (end - start).days
        
        return total_days    

    def add_participant_to_rental(self, rental, member, share, cost, auto_renew=False):
        try:
            rental._add_participant(member, share, cost, self.current_season, auto_renew)
            return True
        except ValueError as e:
            print("Error:", e)
            return False

    ## duration is one season for all plots
    ## TODO: The state of rents and error handling
    def _rent_plot(self, plot_id, member_id, share=1.0):
        plot = self.plots.get(plot_id)
        plot_cost = PLOT_PRICING[plot.size]
        member = self.members.get(member_id)
        current_season = self.current_season

        self.errno = 0

        if not member:
            # "Member doesn't exist"
            self.errno  = -3
            print("member doesn't exist")
            return None


        if not plot:
            # "Plot doesn't exist"
            self.errno  = -4
            print("Plot doesn't exist")
            return None
        if share not in [0.5,1]:
            print("Share should be half or full")
            return None

        cost = self.calculate_rent(plot.id, member.id)
 
        if member.credits < cost:
            print("Not enough credits")
            return None


        if plot.rental is None:
            plot.rental = Rental(plot, plot_cost, current_season)
       
        rental = plot.rental
   
        if not plot.is_available():
            # "Plot already rented"
            self.errno  = -1
            print("plot already rented")
            return None 
        
        added = self.add_participant_to_rental(rental, member, share, cost)

        if not added:
            #  str(e)
            self.errno  = -2
            print("Rental system error")
            return None 

        # print(f"{member.name} rented {share*100:.0f}% of plot {plot_id}")
        return plot

    def rent_plot(self,plot_id):
        plot = self.plots.get(plot_id)
        
        if not plot:
            print("Plot doesn't exist")
            return -2

        ## Note that the member_id is the factor after score and share 
        plot.waitlist.sort(reverse=True)

        for record in plot.waitlist:
            _,share,member_id = record
            if not self._rent_plot(plot.id, member_id, share):
                plot.add_to_season_list(record)

        plot.waitlist = []
        return 1 
    
    def renew_rental(self, plot, old_rental):
        next_season = self.get_next_season()
        plot_cost = PLOT_PRICING[plot.size]

        if old_rental is None:
            return

        new_rental = Rental(plot, plot_cost, next_season)
    
        for p in old_rental.participants:

            # TODO: don't store the object, try store a record instead
            member = p.member
            member.rental_history.append(p)

            if p.auto_renew:
                cost = self.calculate_rent(plot.id,p.member.id)

                success = self.add_participant_to_rental(
                    new_rental,
                    p.member,
                    p.share,
                    cost
                )
                if success:
                    p.status = "Active"
            else:
                p.status = "Terminated"
    
        if not new_rental.participants:
            plot.rental = None
        else:
            plot.rental = new_rental
    
        old_rental.status = "Expired"

        return plot.rental   

    def audit_rental_end(self):
        today = self.time_provider.now()

        for plot in self.plots.values():
            rental = plot.rental
            if not rental or rental.status != "Active":
                continue

            # today = rental.end_date
            if today >= rental.end_date:
                print(f"Today is the day for ending plot {plot.id} rental")
                self.renew_rental(plot, rental)

                plot.season_waitlist.sort(reverse=True)

                for record in plot.season_waitlist:
                    _,share,member_id = record
                    self._rent_plot(plot.id,member_id,share)

                plot.season_waitlist = []

    def audit_rent_plots(self):
        ## Close before 15 days of the end of the season
       for plot in self.plots.values():  
           if self.time_provider.now() < self.current_season.end_date - timedelta(days=15):
                if plot.is_available():
                    self.rent_plot(plot.id)  

    def audit_rental_alert(self):
        ## Alert before 15 days of the end of the season
        for plot in self.plots.values():  
            if plot.rental:
                if plot.rental.status != "Active":
                    return
                
                if self.time_provider.now() >= plot.rental.end_date - timedelta(days=15):
                
                    for p in plot.rental.participants:
                    
                        if p.auto_renew:
                            p.status = "ExpiringSoon" # check your credits for renewal
                        else:
                            p.status = "PendingTermination" 
           
    ## TODO: then add audit to rebuild seasons for new season
    def build(self):
        year = self.time_provider.now().year

        self.seasons = ( 
            self.build_seasons(year - 1) +
            self.build_seasons(year) 
            )

        self.update_current_season()
        self.plot_maker()

        return self
   
    # --- Permission Decorator ---
    def admin_required(func):
        def wrapper(self, user, *args, **kwargs):
            if not isinstance(user, Admin):
                print("Permission denied")
                return
            return func(self, user, *args, **kwargs)
        return wrapper
    


   
  ##  -------- Rent ---------
  
    def apply(self,user,plot_id,share=1.0): 
        plot = self.plots.get(plot_id)
        member_residency_duration = self.calculate_residency_duration(user.id)

        if user and plot:
            score = member_residency_duration*2 + user.contribution_points
            plot.waitlist.append((score,share,user.id))

   ## -------- Tools --------

    def book_tool(self, user, tool_name, duration_hours):
        booking = self.tool_library.book_tool(tool_name, user.id, duration_hours)
        if booking:
            user.booking_ids.append(booking.id)
    
    
    def return_tool(self, user, booking_id, cleaned=True):
        self.tool_library.return_tool(booking_id, cleaned)
    
    
    def report_damage(self, user, booking_id, severity):
        self.tool_library.report_damage(booking_id, severity)
    
    
    ## -------- Seed Bank --------
    
    def deposit(self, user, seed_type, quantity, viability, origin, gt_flag, age, lah=True):
        batch_info = self.seed_bank.create_batchInfo(
            viability, age, gt_flag, origin, lah
        )
        batch = self.seed_bank.create_batch(seed_type, quantity, batch_info)
    
        self.seed_bank.deposit(user.id, batch)
    
    
    def withdraw(self, user, seed_type, quantity):
        withdrawn = self.seed_bank.withdraw(user.id, seed_type, quantity)
        if withdrawn:
            user.inventory.append(withdrawn)
    
    
    ## -------- Volunteer --------
    
    @admin_required
    def create_shift(self, user, date):
        shift = self.volunteer_system.create_shift(date)
        user.shifts_ids.append(shift.shift_id)
    
    
    @admin_required
    def create_task(self, user, shift_id, name, difficulty, category):
        self.volunteer_system.add_task(shift_id, name, difficulty, category)
    
    
    @admin_required
    def assign_members(self, user, shift_id, members_ids):
        for mid in members_ids:
            member = self.members.get(mid)
            member.shifts_ids.append(shift_id)

        self.volunteer_system.assign_members_to_shift(shift_id, members_ids)

    @admin_required      
    def check_weather(self, user, shift_id,weather):
        garden.volunteer_system.check_weather(shift_id, weather)


    def request_swap(self, user, target_id , shift_id):
        target = self.members.get(target_id)

        swap = garden.volunteer_system.request_swap(user.id,target_id,shift_id)
        target.swaps_req_ids.append(swap.request_id)

    def approve_swap(self, user, req_id):
        garden.volunteer_system.approve_swap(req_id)

        ## remove the req_id from the user
        user.swaps_req_ids.remove(req_id)


    # ------- Market Place --------
    def create_listing(self,user, item, quantity, listing_type, request=None):
        listing = garden.market_place.create_listing(user.id, item, quantity, listing_type, request)
        if listing:
            user.listings_ids.append(listing.id) 

    def trade(self, user, listing_id):
        garden.market_place.request_trade(listing_id, user.id)

    def complete_trade(self, user, trade_id):
        garden.market_place.complete_trade(trade_id, user.id)

    def get_listings(self, user):
        return garden.market_place.get_listings()
    
    def get_my_trades(self, user):
        return garden.market_place.get_my_trades(user.id)
 
    def get_trades_by_listing(self, user, listing_id):
        return garden.market_place.get_trades_by_listing(listing_id)

    def ask_question(self, user, content, bounty):
        q = garden.market_place.ask_question(user.id, content,bounty)
        if q:
            user.questions_ids.append(q.id)
            user.credits -= q.bounty

        return q

    def answer_question(self, user, question_id, content):
        garden.market_place.answer_question(user.id, question_id, content)

    def get_questions(self, user):
        return garden.market_place.get_questions()
    
    def get_answers_by_question(self, user, question_id):
        return garden.market_place.get_answers_by_question(Fouad.questions_ids[0])
 
    def accept_answer(self, user, question_id, answer_id):
        answer = garden.market_place.accept_answer(question_id,answer_id)
        responder = self.members[answer.responder_id]

        responder.credits += q.bounty


    def alert_neighbors(self, plot_id):
        plot = self.plots[plot_id]

        if plot.infection_status != "infected":
            return []

        alerts = []

        for neighbor_id in plot.neighbors:
            neighbor = self.plots.get(neighbor_id)

            if neighbor:
                owners = neighbor.get_owners()
                alerts.append({
                    "plot": neighbor_id,
                    "owners": owners,
                    "message": f"Warning: Nearby infection ({plot.infection_type})"
                })

        return alerts

    def seasonal_update(self):
        for plot in self.plots.values():
            plot.generate_winter_tasks()

    def propagate_infections(self):
        all_alerts = []
        for plot_id in self.plots:
            alerts = self.alert_neighbors(plot_id)
            all_alerts.extend(alerts)
        return all_alerts
        ## credits


    def add_credits(self, user, amount):
        user.add_credits(amount)
     
    def add_crop(self, user, plot_id, crop_name):
        plot = garden.plots.get(plot_id)

        ## constraint same plot same crop at a time.
        if plot.current_crop_type and plot.current_crop_type != crop_name:
            raise Exception("Conflict")

        if user.name in plot.get_owners():
            plot.add_crop(user.name,crop_name)

    def add_fertilizer(self, user, plot_id, fertilizer_name):
        plot = garden.plots.get(plot_id)
        plot.add_fertilizer(user, fertilizer_name)

    def update_current_crop(self, user, plot_id, crop_name):
        plot = garden.plots.get(plot_id)
        plot.current_crop_type = crop_name
    
    def generate_watering_schedule(self, user, plot_id):
        plot = garden.plots.get(plot_id)
        schedule = plot.generate_watering_schedule()

        return schedule

# TODO: Moving all these other stuff into Services
        
garden = Garden(100,50).build()
# garden.cad_render()

# admin = Admin(100,"Fouad Ahmed")
# garden.members[100] = admin

# Fouad = garden.join_member("Fouad Ahmed Fouad")
# Mina = garden.join_member("Mina")
# David = garden.join_member("David")
# Ria = garden.join_member("Ria")
# Saged = garden.join_member("Saged")
# Steven = garden.join_member("Steven")





# ## Planting

# --- Setup Garden ---

# pick some plots
plot1 = garden.plots[1]
plot2 = garden.plots[2]
plot3 = garden.plots[3]

# manually define neighbors (if not already set)
plot1.neighbors = plot1.neighbors
plot2.neighbors = plot2.neighbors
plot3.neighbors = plot3.neighbors




# --- Create Members ---
alice = garden.join_member("Alice")
bob = garden.join_member("Bob")
charlie = garden.join_member("Charlie")

garden.add_credits(alice,200)
garden.add_credits(bob,200)
garden.add_credits(charlie,200)

garden.apply(alice, plot1.id, 0.5)
garden.apply(bob, plot1.id, 0.5)
garden.apply(charlie, plot2.id, 1)


garden.audit_rental_alert()
garden.audit_rental_end()
garden.audit_rent_plots()



print("\n--- Soil State Test ---")

garden.add_crop(alice, plot1.id, "carrot")
garden.add_crop(bob, plot1.id, "carrot")
garden.add_crop(alice, plot1.id, "carrot")

print("Soil state (expect depleted):", plot1.soil_state)

garden.add_fertilizer(bob, plot1.id,"organic")

print("Soil state (expect recovering):", plot1.soil_state)


# =========================================================
# 💧 2. IRRIGATION TEST
# =========================================================

print("\n--- Irrigation Test ---")

garden.update_current_crop(alice,plot1.id,"tomato")
schedule = garden.generate_watering_schedule(alice, plot1.id)

print("Watering schedule:", schedule)


# =========================================================
# 🐛 3. INFECTION + PROPAGATION TEST
# =========================================================

print("\n--- Infection Propagation Test ---")

plot1.report_infection("potato_blight", datetime.now())

alerts = garden.propagate_infections()

for alert in alerts:
    print(alert)


# =========================================================
# ❄️ 4. SEASONAL TASKS TEST
# =========================================================

print("\n--- Seasonal Tasks Test ---")

# force conditions
plot1.soil_state = "depleted"
plot1.ph_level = 5

garden.seasonal_update()

print("Plot1 tasks:", plot1.tasks)


# =========================================================
# 👥 5. MULTI-USER ACTIVITY LOG TEST
# =========================================================

print("\n--- Activity Log ---")

for act in plot1.activities:
    print(act)


# =========================================================
# 🔍 6. OWNERS TEST
# =========================================================

print("\n--- Owners Test ---")

print("Plot1 owners:", plot1.get_owners())
print("Plot2 owners:", plot2.get_owners())

# ## Admin

# ## The system checks plots rentals everyday, the application is satisfied after 24 hours
# ## if the plot is available and all requirments are satasifed (eg., enough credits)
# ## the plot is rented, Otherwise the member is added to season waitlist that will be proccessed
# ## by the end of the season.
# garden.audit_rental_alert()
# garden.audit_rental_end()
# garden.audit_rent_plots()


# #### Tools
# garden.tool_library.add_tool("Rototiller", usage_status="high", maintenance_threshold_hours=5)

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


# ### TOOLS

# ## Fouad books a tool
# garden.book_tool(Steven, "Rototiller", duration_hours=10)

# ## Fouad returns the tool 
# garden.return_tool(Steven, Steven.booking_ids[0], cleaned=True)

# ## Fouad report damage
# garden.report_damage(Steven, Steven.booking_ids[0], severity="medium")



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








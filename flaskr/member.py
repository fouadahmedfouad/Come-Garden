class Member:
    def __init__(self,id,name,mytype="normal"):
            
        self.id  = id
        self.name = name
        self.type = mytype
        

        self.credits = 0
        self.contribution_points = 0 
        
        self.rental_history = []

        self.inventory = []
        self.bookings = []

        self.shifts_ids = []
        self.swaps_req_ids = []

        self.listings_ids = []
        self.questions_ids = []

    def add_rental(self,rental):
        self.rental_history.append(rental)

    def add_credits(self, amount):
        self.credits += amount

    def minus_credits(self, amount):
        self.credits -= amount 

    def add_rental_to_history(self,p):
        self.rental_history.append(p)

    def get_member_tier_factor(self):
        count = len(self.rental_history)

        if count < 2:
            return 1.0
        elif count < 5:
            return 0.9
        else:
            return 0.8
 
    def calculate_residency_duration(self):
        total_days = 0

        for rental in self.rental_history:
            start = rental.start_date
            end   = rental.end_date
            total_days += (end - start).days
        
        return total_days    

    @property
    def is_admin(self):
        return False

class Admin(Member):
    def __init__(self, id, name):
        super().__init__(id, name)

    @property
    def is_admin(self):
        return True


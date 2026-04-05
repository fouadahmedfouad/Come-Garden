class Member:
    def __init__(self,id,name,mytype="normal"):
            
        self.id   = id
        self.name = name
        self.type = mytype
        

        self.credits = 0
        self.contribution_points = 0 
        
        self.rental_history = []
        self.booking_ids = []
        self.inventory = []

        self.shifts_ids = []
        self.swaps_req_ids = []

        self.listings_ids = []
        self.questions_ids = []

    def add_rental(self,rental):
        self.rental_history.append(rental)

    def add_credits(self, amount):
        self.credits += amount


    def get_member_tier_factor(self):
        count = len(self.rental_history)

        if count < 2:
            return 1.0
        elif count < 5:
            return 0.9
        else:
            return 0.8
 
    def is_available(self):
        return self.rental is None or not self.rental.is_full()

    def get_owners(self):
        if self.rental and self.rental.participants:
            return [p.member.name for p in self.rental.participants]
        return []   

    @classmethod
    def create_member(self, member_name):
        return Member(1,member_name)

class Admin(Member):
    def __init__(self, id, name):
        super().__init__(id, name)

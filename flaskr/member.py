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

    def add_rental(self,rental):
        self.rental_history.append(rental)

    def add_credits(self, amount):
        self.credits += amount

class Admin(Member):
    def __init__(self, id, name):
        super().__init__(id, name)

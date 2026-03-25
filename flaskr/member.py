class Member:
    def __init__(self,name, credits=0, mytype="normal"):
        self.credits = credits
        self.name = name
        self.type = mytype

        self.rental_history = []
        self.inventory = []


    def add_rental(self,rental):
        self.rental_history.append(rental)

    

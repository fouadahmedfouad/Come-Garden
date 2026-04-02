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
    
   

    def add_rental(self,rental):
        self.rental_history.append(rental)

    

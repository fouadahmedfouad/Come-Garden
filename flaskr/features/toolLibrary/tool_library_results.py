class BookingResult:
    def __init__(self, success: bool, booking=None, waitlisted=False, error=None):
        self.success = success
        self.booking = booking          
        self.waitlisted = waitlisted   
        self.error = error           


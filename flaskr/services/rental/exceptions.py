## Rental Excpetions
class RentalError(Exception):
    pass

class MemberNotFoundError(RentalError):
    def __init__(self,message):
        super().__init__(message)

class PlotNotFoundError(RentalError):
    def __init__(self,message):
        super().__init__(message)


class InvalidShareError(RentalError):
    def __init__(self,message):
        super().__init__(message)

class InsufficientCreditsError(RentalError):
    def __init__(self,message):
        super().__init__(message)


class DuplicateParticipantError(RentalError):
    def __init__(self,message):
        super().__init__(message)





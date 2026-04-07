
## Rental Excpetions
class RentalError(Exception):
    pass

class MemberNotFoundError(RentalError):
    pass

class PlotNotFoundError(RentalError):
    pass

class InvalidShareError(RentalError):
    pass

class InsufficientCreditsError(RentalError):
    pass

class DuplicateParticipantError(RentalError):
    pass




## Plot Excptions
class PlotError(Exception):
    pass

class MemberNotInPlot(PlotError):
    pass


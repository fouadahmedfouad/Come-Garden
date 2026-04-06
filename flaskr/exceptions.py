

## Garden Exceptions
class PermissionDeniedError(Exception):
    pass

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

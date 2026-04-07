from enum import Enum


class RentalStatus(Enum):
    SUCCESS = "success"
    WAITLISTED = "waitlisted"

class PlotStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
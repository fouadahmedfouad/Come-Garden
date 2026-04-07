from enum import Enum


class RentalStatus(Enum):
    SUCCESS = "success"
    WAITLISTED = "waitlisted"
    FAILED = "failed"

class PlotStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
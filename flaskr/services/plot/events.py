
## TODO: Plot is different from plot service. and these are events in the "smart plot".

class PlotEvent:
    def __init__(self, event_type, plot_id=None, user=None, **data):
        self.type = event_type
        self.plot_id = plot_id
        self.user = user
        self.data = data


class CropPlanted(DomainEvent):
    def __init__(self, plot_id, user, crop):
        super().__init__("crop_planted", plot_id, user, crop=crop)


class FertilizerAdded(DomainEvent):
    def __init__(self, plot_id, user, fertilizer):
        super().__init__("fertilizer_added", plot_id, user, fertilizer=fertilizer)


class PlotInfected(DomainEvent):
    def __init__(self, plot_id, infection_type, date):
        super().__init__("plot_infected", plot_id, None,
                         infection_type=infection_type, date=date)


class SoilStateChanged(DomainEvent):
    def __init__(self, plot_id, new_state):
        super().__init__("soil_state_changed", plot_id, None,
                         state=new_state)

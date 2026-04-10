from datetime import datetime

class RentalEvent:
    def __init__(self, event_type, user_id=None, **data):
        self.type = event_type
        self.user_id = user_id
        self.timestamp = datetime.utcnow()
        self.data = data



class ApplicationSubmitted(RentalEvent):
    def __init__(self, user_id, plot_id, share):
        super().__init__(
            "application_submitted",
            user_id,
            plot_id=plot_id,
            share=share
        )


class RentalApproved(RentalEvent):
    def __init__(self, user_id, plot_id):
        super().__init__(
            "rental_approved",
            user_id,
            plot_id=plot_id
        )


class RentalWaitlisted(RentalEvent):
    def __init__(self, user_id, plot_id):
        super().__init__(
            "rental_waitlisted",
            user_id,
            plot_id=plot_id
        )


class RentalExpired(RentalEvent):
    def __init__(self, plot_id):
        super().__init__(
            "rental_expired",
            None,
            plot_id=plot_id
        )

class RentalFailed(RentalEvent):
    def __init__(self, user_id, plot_id, message):
        super().__init__(
            "rental_failed",
            user_id,
            plot_id=plot_id,
            message=message
        )




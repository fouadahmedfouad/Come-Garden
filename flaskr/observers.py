class MarketplaceObserver:
    def __init__(self, marketplace):
        self.marketplace = marketplace

    def on_trade_completed(self, event):
        listing = self.marketplace.listings.get(event.data["listing_id"])
        if listing and listing.type == "gift":
            uid = event.user_id
            self.marketplace.member_karam[uid] = \
                self.marketplace.member_karam.get(uid, 0) + 10

    def on_answer_accepted(self, event):
        responder_id = event.data.get("responder_id")
        bounty = event.data.get("bounty", 0)

        self.marketplace.member_credits[responder_id] = \
            self.marketplace.member_credits.get(responder_id, 0) + bounty

class ToolLibraryObserver:
    def __init__(self, tool_library):
        self.tool_library = tool_library

    def on_tool_returned(self, event):
        if event.data.get("late"):
            print(f"[Alert] Late return by user {event.user_id}")

        self.tool_library.process_waitlist(event.data.get("tool_name"))

    def on_tool_damaged(self, event):
        if event.data["severity"] == "high":
            print(f"[Red Flag] Tool {event.data['tool_name']} heavily damaged")

    def on_tool_booked(self, event):
        tool = self.tool_library.tools.get(event.data["tool_name"])
        if tool and tool.total_usage_hours > tool.maintenance_threshold_hours:
            print(f"[Alert] Tool {tool.name} needs maintenance")


class SeedBankObserver:
    def __init__(self, seed_bank):
        self.seed_bank = seed_bank

    def on_seed_withdrawn(self, event):
        if event.quantity > 50:
            print(f"[Alert] Large withdrawal by user {event.user_id}")


class VolunteerObserver:
    def __init__(self, volunteer_system):
        self.volunteer_system = volunteer_system

    def on_shift_created(self, event):
        if event.data.get("rescheduled"):
            print(f"[Info] Shift {event.data['shift_id']} rescheduled due to {event.data['weather']}")

    def on_members_assigned(self, event):
        if event.data["count"] == 0:
            print("[Alert] No members assigned to shift")

    def on_shift_completed(self, event):
        shift = self.volunteer_system.shifts.get(event.data["shift_id"])
        if shift and not shift.assignments:
            print("[Alert] Shift completed with no assignments")

    def on_swap_requested(self, event):
        print(f"[Info] Swap requested from {event.user_id} → {event.data['target_id']}")

        # future: abuse detection (too many swaps, etc.)


class RentalObserver:
    def on_application_submitted(self, event):
        print(f"[Info] Application for plot {event.data['plot_id']}")

    def on_rental_waitlisted(self, event):
        print(f"[Alert] Plot {event.data['plot_id']} is oversubscribed")

    def on_rental_expired(self, event):
        print(f"[Info] Rental cycle completed for plot {event.data['plot_id']}")

    def on_rental_failed(slef, event):
        print(f"[Fail] Rental failed by member {event.user_id} while renting plot {event.data['plot_id']} due to {event.data['message']}")



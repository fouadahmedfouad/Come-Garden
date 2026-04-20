from datetime import datetime, timedelta
import uuid

from features.marketPlace.market_place_info import (
    Listing,
    Trade,
    Rating,
    Question,
    Answer
)


from features.marketPlace.market_place_exceptions import *
from features.marketPlace.market_place_results import *
from features.marketPlace.market_place_events import *


class Marketplace:
    def __init__(self, event_bus):
        self.listings = {}
        self.questions = {}


        self.member_karam = {}
        self.member_credits = {}
        
        # self.ratings = [] 
        self.event_bus = event_bus
        self.events = []


    def _emit_event(self, event):
        self.events.append(event) # debug
        if self.event_bus:
            self.event_bus.publish(event)

    def create_listing(self, user, item, quantity, listing_type="normal", request=None) -> ListingResult:
        try:
            if not user:
                raise InvalidUserError(user)

            listing = Listing(user.id, item, quantity, listing_type, request)

            user.listings = getattr(user, "listings", [])
            user.listings.append(listing)

            self._apply_allergy_flags(listing)
            self.listings[listing.id] = listing

            self._emit_event(
                ListingCreated(user.id, listing.id, item, quantity)
            )
            
            return ListingResult(True, listing)

        except MarketplaceError as e:
            return ListingResult(False, error=str(e))
        except Exception as e:
            return ListingResult(False, error=f"[Critical] {e}")

    def request_trade(self, user, listing) -> TradeResult:
        try:
            if not user:
                raise InvalidUserError(user)

            if not listing:
                raise ListingNotFoundError(None)

            if listing.status != "active":
                raise TradeError("Listing not active")

            if listing.type == "flash" and datetime.now() > listing.expires_at:
                listing.status = "expired"
                raise TradeError("Listing expired")

            trade = Trade(listing.id, user.id)
            listing.trades.append(trade)

            self._emit_event(
                TradeRequested(user.id, listing.id, trade.id)
            )

            return TradeResult(True, trade)

        except MarketplaceError as e:
            return TradeResult(False, error=str(e))
        except Exception as e:
            return TradeResult(False, error=f"[Critical] {e}")

    def complete_trade(self, user, trade) -> TradeResult:
        try:
            if not trade:
                raise TradeError("Invalid trade")

            listing = self.listings.get(trade.listing_id)
            if not listing:
                raise ListingNotFoundError(trade.listing_id)

            trade.status = "completed"
            listing.status = "completed"

            self._emit_event(
                TradeCompleted(user.id, listing.id, trade.id)
            )

            return TradeResult(True, trade)

        except MarketplaceError as e:
            return TradeResult(False, error=str(e))
        except Exception as e:
            return TradeResult(False, error=f"[Critical] {e}")


    def ask_question(self, user, content, bounty=0) -> QuestionResult:
        try:
            if not user:
                raise InvalidUserError(user)

            if user.seedBank_credits < bounty:
                raise QuestionError("Not enough credits")

            q = Question(user.id, content, bounty)

            user.questions = getattr(user, "questions", [])
            user.questions.append(q)

            user.seedBank_credits = getattr(user, "seedBank_credits", 0) - bounty
            self.questions[q.id] = q

            self._emit_event(
                QuestionAsked(user.id, q.id, bounty)
            )

            return QuestionResult(True, q)

        except MarketplaceError as e:
            return QuestionResult(False, error=str(e))
        except Exception as e:
            return QuestionResult(False, error=f"[Critical] {e}")

    def answer_question(self, user, question, content) -> AnswerResult:
        try:
            if not question:
                raise QuestionError("Question not found")

            if question.status != "open":
                raise QuestionError("Question not open")

            ans = Answer(question.id, user, content)

            question.answers.append(ans)

            return AnswerResult(True, ans)

        except MarketplaceError as e:
            return AnswerResult(False, error=str(e))
        except Exception as e:
            return AnswerResult(False, error=f"[Critical] {e}")

    def accept_answer(self, user, question, answer) -> AnswerResult:
        try:
            if not question or not answer:
                raise AnswerError("Invalid question or answer")

            answer.accepted = True
            question.accepted_answer_id = answer
            question.status = "resolved"

            responder = answer.responder
            responder.seedBank_credits = getattr(responder, "seedBank_credits", 0) + question.bounty

            self._emit_event(
                AnswerAccepted(
                    user.id,
                    answer.id,
                    question.bounty
                )
            )

            return AnswerResult(True, answer)

        except MarketplaceError as e:
            return AnswerResult(False, error=str(e))
        except Exception as e:
            return AnswerResult(False, error=f"[Critical] {e}")



    #
    # def rate_user(self, from_user_id, to_user_id, score, comment=""):
    #     self.ratings.append(Rating(from_user_id, to_user_id, score, comment))

 
    def _apply_allergy_flags(self, listing):
        allergens = {
            "tomato": "nightshade",
            "potato": "nightshade",
            "peanut": "allergen"
        }

        if listing.item.lower() in allergens:
            listing.flags.append(allergens[listing.item.lower()])

    def get_listings(self, user):
        return list(self.listings.values())
    
    def get_questions(self, user):
        return list(self.questions.values())



    # def get_listings(self, status=None, listing_type=None, item=None):
    #     results = self.listings.values()
    
    #     if status:
    #         results = filter(lambda l: l.status == status, results)
    
    #     if listing_type:
    #         results = filter(lambda l: l.type == listing_type, results)
    
    #     if item:
    #         results = filter(lambda l: l.item.lower() == item.lower(), results)
    
    #     return list(results)


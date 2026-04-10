class OperationResult:
    def __init__(self, success: bool, error: str = None):
        self.success = success
        self.error = error


class ListingResult(OperationResult):
    def __init__(self, success: bool, listing=None, error=None):
        super().__init__(success, error)
        self.listing = listing


class TradeResult(OperationResult):
    def __init__(self, success: bool, trade=None, error=None):
        super().__init__(success, error)
        self.trade = trade


class QuestionResult(OperationResult):
    def __init__(self, success: bool, question=None, error=None):
        super().__init__(success, error)
        self.question = question


class AnswerResult(OperationResult):
    def __init__(self, success: bool, answer=None, error=None):
        super().__init__(success, error)
        self.answer = answer

class Tags:
    MATCH = "amazon_match"
    LAST = "amazon_match_last"
    MANUAL = "amazon_manual"
    TODO = "amazon_todo"
    ERROR = "amazon_error"

    @staticmethod
    def all():
        return [Tags.MATCH, Tags.LAST, Tags.MANUAL, Tags.TODO, Tags.ERROR]

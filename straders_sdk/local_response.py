class LocalSpaceTradersRespose:
    def __init__(self, error, status_code, error_code, url=None):
        self.error = error
        self.status_code = status_code
        self.error_code = error_code
        self.content = {}
        self.data = {}
        self.response_json = {"error": {"code": self.error_code, "message": self.error}}
        self.url = "https://localhost/LOCAL" if url is None else url
        # logger goes here

    def json(self) -> dict:
        return self.response_json

    def __bool__(self):
        return self.error_code is None

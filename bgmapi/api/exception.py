class BangumiCLIException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class RequestFailedError(BangumiCLIException):
    pass


class LoginFailedError(RequestFailedError):
    pass

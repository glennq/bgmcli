"""Exceptions for the package
"""

class BangumiCLIException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class NotLoggedInError(BangumiCLIException):
    """Exception raised when trying to make requests while not logged in"""
    pass


class RequestFailedError(BangumiCLIException):
    """Exception raised when failed to get necessary data"""


class LoginFailedError(RequestFailedError):
    """Exception raised when login failed at construction of BangumiSession"""
    pass




"""Exceptions for the CLI
"""

class BangumiCLIException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class ConfigError(BangumiCLIException):
    """Error raised when config file does not exist or has wrong format"""
    pass


class CommandError(BangumiCLIException):
    """Error raised when there's something wrong with a command"""
    pass


class InvalidCommandError(CommandError):
    """Error raised when input commmand is invalid"""
    pass


class WrongCommandExcecutorError(CommandError):
    """Error raised when trying to create CommandExcecutor instance with
    incompatible command
    """
    pass
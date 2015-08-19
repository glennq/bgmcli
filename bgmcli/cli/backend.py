from __future__ import unicode_literals
from ..api import BangumiSession
from .exception import InvalidCommandError
from .command_executor import CommandExecutorIndex


class CLIBackend(object):
    """Backend for CLI, takes and parses command from CLI, and proxies calls
    to and results from API
    """
    
    _VALID_COMMANDS = ['kandao', 'kanguo', 'xiangkan', 'paoqi', 'chexiao',
                       'watched-up-to', 'watched', 'drop', 'want-to-watch',
                       'remove', 'ls-watching', 'ls-zaikan', 'ls-eps', 'undo']
    
    def __init__(self, email, password):
        self._session = BangumiSession(email, password)
        sub_ids = self._session.get_sub_id_list('anime', 3)
        self._watching = [self._session.get_sub_collection(sub_id)
                          for sub_id in sub_ids]
        self._titles = set()
        self._update_titles()
    
    def execute_command(self, command):
        parsed = command.strip().split()
        if parsed[0] not in self._VALID_COMMANDS:
            raise InvalidCommandError("Got invalid command: {0}"
                                      .format(parsed[0]))
        executor = (CommandExecutorIndex
                    .get_command_executor(parsed[0])(parsed, self._watching))
        executor.execute()
        self._update_titles()
    
    def get_user_id(self):
        return self._session.user_id
    
    def get_completion_list(self):
        return self._VALID_COMMANDS + list(self._titles)
    
    def get_valid_commands(self):
        return tuple(self._VALID_COMMANDS)
    
    def close(self):
        self._session.logout()
        
    def _parse_command(self, command):
        pass
    
    def _update_titles(self):
        for coll in self._watching:
            sub = coll.subject
            names = ([sub.title, sub.ch_title] +
                     sub.other_info.get('aliases', []))
            for name in names:
                if name not in self._titles:
                    self._titles.add(name)
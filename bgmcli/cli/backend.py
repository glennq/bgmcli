from __future__ import unicode_literals
from prompt_toolkit.key_binding.manager import KeyBindingManager
from xpinyin import Pinyin
from ..api import BangumiSession
from .exception import InvalidCommandError
from .command_executor import CommandExecutorIndex


key_bindings_manager = KeyBindingManager()
corrections = {}


@key_bindings_manager.registry.add_binding(' ')
def _(event):
    """
    When space is pressed, we check the word before the cursor, and
    autocorrect that.
    """
    buf = event.cli.current_buffer
    text = buf.document.text_before_cursor
    word = text.split()[-1]

    if word is not None:
        if word in corrections:
            buf.delete_before_cursor(count=len(word))
            buf.insert_text(corrections[word])

    buf.insert_text(' ')
    

class CLIBackend(object):
    """Backend for CLI, takes and parses command from CLI, and proxies calls
    to and results from API
    
    Args:
        email (str or unicode): email address for login
        password (str or unicode) password for login
    """
    
    _VALID_COMMANDS = CommandExecutorIndex.valid_commands
#     ['kandao', 'kanguo', 'xiangkan', 'paoqi', 'chexiao',
#                        'watched-up-to', 'watched', 'drop', 'want-to-watch',
#                        'remove', 'ls-watching', 'ls-zaikan', 'ls-eps', 'undo']
    
    def __init__(self, email, password):
        self._session = BangumiSession(email, password)
        self._colls = self._session.get_dummy_collections('anime', 3)
        pinyin = Pinyin()
        for coll in self._colls:
            if not coll.subject.ch_title:
                continue
            pinyin_title = pinyin.get_pinyin(coll.subject.ch_title, '')
            if not coll.subject.other_info.get('aliases'):
                coll.subject.other_info['aliases'] = [pinyin_title]
            else:
                coll.subject.other_info['aliases'].append(pinyin_title)
            corrections.update({pinyin_title: coll.subject.ch_title})
        self._titles = set()
        self._update_titles()
    
    def execute_command(self, command):
        """Execute given command
        
        Args:
            command (unicode): command from user interface
            
        Raises:
            InvalidCommandError: if command head is not valid
        """
        parsed = command.strip().split()
        if not parsed:
            return
        if parsed[0] not in self._VALID_COMMANDS:
            raise InvalidCommandError("Got invalid command: {0}"
                                      .format(parsed[0]))
        executor = (CommandExecutorIndex
                    .get_command_executor(parsed[0])(parsed, self._colls))
        executor.execute()
        self._update_titles()
    
    def get_user_id(self):
        """Get the user id for current user
        
        Returns:
            str or unicode: user id
        """
        return self._session.user_id
    
    def get_completion_list(self):
        """Get the list of names for auto completion
        
        Returns:
            list[unicode]: commands and titles
        """
        return self._VALID_COMMANDS + list(self._titles)
    
    def get_valid_commands(self):
        """Get valid command head
        
        Return:
            tuple(unicode): valid commands
        """
        return tuple(self._VALID_COMMANDS)
    
    def close(self):
        """Close the session
        """
        self._session.logout()
        
    def _parse_command(self, command):
        pass
    
    def _update_titles(self):
        for coll in self._colls:
            sub = coll.subject
            names = ([sub.title, sub.ch_title] +
                     sub.other_info.get('aliases', []))
            for name in names:
                if name and name not in self._titles:
                    self._titles.add(name)
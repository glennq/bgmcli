"""The backend of CLI and autocorrections"""

from __future__ import unicode_literals
import re
from prompt_toolkit.key_binding.manager import KeyBindingManager
from xpinyin import Pinyin
from bgmcli.api import BangumiSession
from .command_executor import CommandExecutorIndex


key_bindings_manager = KeyBindingManager()
corrections = {}


@key_bindings_manager.registry.add_binding(' ')
def _(event):
    """ Registers event of white space for auto-correction
    When space is pressed, we check the phrase before the cursor and after
    command head, and autocorrect that.
    This is used to automatically transform pinyin input of subject titles to
    Chinese
    """
    buffr = event.cli.current_buffer
    text = buffr.document.text_before_cursor
    word = text.split(None, 1)[-1]

    if word is not None:
        if word in corrections:
            buffr.delete_before_cursor(count=len(word))
            buffr.insert_text(corrections[word])

    buffr.insert_text(' ')
    

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
        # add pinyin to valid titles and setup auto correction behaviors
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
        if not command or not command.strip():
            return
        parsed = self._parse_command(command)
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
        """Parses the command and split it up into command head, subject
        title, and other trailing information
        """
        splitted = command.strip().split(None, 1)
        if (len(splitted) == 1):
            return splitted
        else:
            head, tail = splitted
            iterator = re.finditer('\s+', tail, flags=re.UNICODE)
            pos = [i.start() for i in iterator]
            # reverse to matched longest name first
            pos.reverse()
            for idx in pos:
                if tail[:idx] in self._titles:
                    if tail[idx:].strip():
                        return [head, tail[:idx], tail[idx:].strip()]
                    else:
                        return [head, tail[:idx]]
            return [head, tail.strip()]
        
    
    def _update_titles(self):
        """update valid titles
        """
        for coll in self._colls:
            sub = coll.subject
            names = ([sub.title, sub.ch_title] +
                     sub.other_info.get('aliases', []))
            for name in names:
                if name and name not in self._titles:
                    self._titles.add(name)
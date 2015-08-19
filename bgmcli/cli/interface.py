from __future__ import unicode_literals
import os
from prompt_toolkit import AbortAction
from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import History
from prompt_toolkit.contrib.completers import WordCompleter
from bgmcli.cli.exception import ConfigError
from bgmcli.cli.backend import CLIBackend
from bgmcli.cli.exception import CommandError


def read_config():
    home = os.path.expanduser('~')
    config_file = os.path.join(home, '.bgmcli-config')
    if not os.path.exists(config_file):
        raise ConfigError("Config file not found")
    with open(config_file, 'rb') as f:
        email = f.readline().strip()
        password = f.readline().strip()

    return email, password


def get_completer(words):
    completer = WordCompleter(words)
    return completer


def run():
    backend = CLIBackend(*read_config())
    history = History()
    completer = get_completer(backend.get_completion_list())
    user_id = backend.get_user_id()
    while True:
        try:
            text = get_input(user_id + '> ', completer=completer,
                             history=history, on_abort=AbortAction.RETRY)
        except EOFError:
            # Control-D pressed.
            break
        else:
            try:
                backend.execute_command(text)
            except CommandError as e:
                print e


if __name__ == '__main__':
    run()
    
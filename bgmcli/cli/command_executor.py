from __future__ import unicode_literals
from itertools import izip_longest
from .exception import WrongCommandExcecutorError, InvalidCommandError
from bgmcli.api.collection import BangumiDummySubjectCollection


class CommandExecutorIndex(object):
    """A index class that finds returns the right subclass of
    BaseCommandExecutor
    
    Note:
        This only serves as a factory class and is NOT supposed to be
        instantiated
        
    Attributes:
        command_executors_map (dict): map from command head to subclass name
            that deals with this type of command
    """

    command_executors_map = {}
    valid_commands = []
    
    @classmethod
    def get_command_executor(cls, command_head):
        """Get the class correct class given command_head
        
        Args:
            command_head (str or unicode): the first word in a command
            
        Returns:
            CommandExecutorMeta: a subclass of BaseCommandExecutor
        """
        executor_class = cls.command_executors_map[command_head]
        return executor_class


class CommandExecutorMeta(type):
    """Meta class for BaseCommandExecutor, registers subclasses of
    BaseCommandExecutor in CommandExecutorFactory
    """
    def __new__(meta, name, bases, class_dict):  # @NoSelf
        cls = type.__new__(meta, name, bases, class_dict) 
        for key in class_dict['_VALID_COMMANDS']:
            CommandExecutorIndex.command_executors_map.update({key: cls})
        (CommandExecutorIndex.valid_commands
         .extend(class_dict['_VALID_COMMANDS']))
        return cls


class BaseCommandExecutor(object):

    __metaclass__ = CommandExecutorMeta
    _VALID_COMMANDS = []
    _MAX_COMMAND_LEN = 3
    _MIN_COMMAND_LEN = 1 

    def __init__(self, parsed, collections):
        if parsed[0] not in self._VALID_COMMANDS:
            raise WrongCommandExcecutorError("{0} does not support command {1}"
                                             .format(self.__class__.__name__,
                                                     parsed[0]))
        self._parsed = parsed
        self._length = len(parsed)
        self._collections = collections
        self._validate_command()
        
    def execute(self):
        raise NotImplementedError
        
    def _validate_command(self):
        if (self._length < self._MIN_COMMAND_LEN or
            self._length > self._MAX_COMMAND_LEN):
            raise InvalidCommandError("Must have {0} to {1} arguments, got {2}"
                                      .format(self._MIN_COMMAND_LEN - 1,
                                              self._MAX_COMMAND_LEN - 1,
                                              self._length - 1))


class SubjectCommandMixin(object):
    def _find_collection(self, name):
        """Get subject collection that matches provided name
        
        Returns:
            BangumiSubjectCollection: the first subject collection that
                matches provided name, None if not found
        """
        for coll in self._collections:
            sub = coll.subject
            names = ([sub.title, sub.ch_title] +
                     sub.other_info.get('aliases', []))
            if name in names:
                return self._update_collection(coll)
        raise InvalidCommandError("Subject name {0} not found".format(name))
    
    def _update_collection(self, coll):
        if (isinstance(coll, BangumiDummySubjectCollection) and
            coll in self._collections):
            new_coll = coll.to_regular_collection()
            self._collections.remove(coll)
            self._collections.append(new_coll)
            return new_coll
        else:
            return coll


class ListCommandMixin(object):
    def _produce_output(self, data):
        n_cols = 5
        rows = [data[x:x+n_cols] for x in range(0, len(data), n_cols)]
        if len(rows[-1]) < n_cols:
            rows[-1] += [''] * (n_cols - len(rows[-1]))
        cols = izip_longest(*rows, fillvalue='')
        max_widths = [max(len(elem) for elem in col) for col in cols]
        format_str = ''.join(['{{{1}:<{0}}}'.format(width+2, i)
                              for i, width in enumerate(max_widths)])
        
        return '\n'.join([format_str.format(*row) for row in rows])


class WatchedCommandExecutor(BaseCommandExecutor, SubjectCommandMixin):

    _VALID_COMMANDS = ['watched', 'kanguo']
    _MAX_COMMAND_LEN = 3
    _MIN_COMMAND_LEN = 2 
    
    def __init__(self, parsed, collections):
        super(WatchedCommandExecutor, self).__init__(parsed, collections)
        
    def execute(self):
        coll = self._find_collection(self._parsed[1])

        if self._length == 2:
            coll.c_status = 2
            coll.sync_collection()
        else:
            ep_coll = coll.find_ep_coll(self._parsed[2])
            if not ep_coll:
                raise InvalidCommandError("Episode name {0} not found"
                                          .format(self._parsed[2]))
            ep_coll.c_status = 'watched'
            ep_coll.sync_collection()
            
    
class WatchedUpToCommandExecutor(BaseCommandExecutor, SubjectCommandMixin):

    _VALID_COMMANDS = ['watchedupto', 'kandao']
    _MAX_COMMAND_LEN = 3
    _MIN_COMMAND_LEN = 3
    
    def __init__(self, parsed, collections):
        super(WatchedUpToCommandExecutor, self).__init__(parsed, collections)
        
    def execute(self):
        coll = self._find_collection(self._parsed[1])
        ep_coll = coll.find_ep_coll(self._parsed[2])
        if not ep_coll:
            raise InvalidCommandError("Episode name {0} not found"
                                      .format(self._parsed[2]))
        ep_coll.c_status = 'watched_up_to'
        ep_coll.sync_collection()
        
        
class ListWatchingCommandExecutor(BaseCommandExecutor, ListCommandMixin):
    _VALID_COMMANDS = ['lswatching', 'lszaikan']
    _MAX_COMMAND_LEN = 1
    _MIN_COMMAND_LEN = 1
    
    def __init__(self, parsed, collections):
        super(ListWatchingCommandExecutor, self).__init__(parsed, collections)
        
    def execute(self):
        ch_titles = [coll.subject.ch_title for coll in self._collections]
        print self._produce_output(ch_titles)
        
        
class ListEpsCommandExecutor(BaseCommandExecutor, ListCommandMixin,
                             SubjectCommandMixin):
    _VALID_COMMANDS = ['lseps']
    _MAX_COMMAND_LEN = 2
    _MIN_COMMAND_LEN = 2
    
    def __init__(self, parsed, collections):
        super(ListEpsCommandExecutor, self).__init__(parsed, collections)
        
    def execute(self):
        coll = self._find_collection(self._parsed[1])
        statuses = [self._resolve_status(ep_coll.c_status,
                                         ep_coll.episode.status)
                    for ep_coll in coll.ep_collections]
        ep_type_nums = ['{0}{1}'.format(ep_coll.episode.ep_type, 
                                        ep_coll.episode.ep_num)
                        for ep_coll in coll.ep_collections]
        ep_displays = ['{1}[{0}{2}\033[0m]'.format(self._status_color(status),
                                            type_num, status) 
                       for status, type_num in zip(statuses, ep_type_nums)]

        print self._produce_output(ep_displays)
    
    def _resolve_status(self, c_status, air_status):
        if not c_status:
            return air_status
        else:
            return c_status
        
    def _status_color(self, status):
        """
        watched: blue, wish: magenta, drop: white, air: cyan, na: black,
        today: green
        """
        mapping = {'watched': '\033[34m', 'wish': '\033[35m',
                   'drop': '\033[37m', 'air': '\033[36m', 'na': '\033[30m',
                   'today': '\033[32m'}

        return mapping[status]
        
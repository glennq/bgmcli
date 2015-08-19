from __future__ import unicode_literals
from .exception import WrongCommandExcecutorError, InvalidCommandError


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
    
    @classmethod
    def get_command_executor(cls, command_head):
        """Get the class correct class given command_head
        
        Args:
            command_head (str or unicode): the first word in a command
            
        Returns:
            CommandExecutorMeta: a subclass of BaseCommandExecutor
        """
        executor_class = globals()[cls.command_executors_map[command_head]]
        return executor_class
    
    
class CommandExecutorMeta(type):
    """Meta class for BaseCommandExecutor, registers subclasses of
    BaseCommandExecutor in CommandExecutorFactory
    """
    def __new__(meta, name, bases, class_dict):  # @NoSelf
        for key in class_dict['_VALID_COMMANDS']:
            CommandExecutorIndex.command_executors_map.update({key: name})
        cls = type.__new__(meta, name, bases, class_dict) 
        return cls


class BaseCommandExecutor(object):

    __metaclass__ = CommandExecutorMeta
    _VALID_COMMANDS = []

    def __init__(self, parsed, collections):
        if parsed[0] not in self._VALID_COMMANDS:
            raise WrongCommandExcecutorError("{0} does not support command {1}"
                                             .format(self.__class__.__name__,
                                                     parsed[0]))
        self._parsed = parsed
        self._length = len(parsed)
        self._collections = collections
        
    def execute(self):
        raise NotImplementedError
    
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
                return coll
        return None
    
    
class WatchedCommandExecutor(BaseCommandExecutor):

    _VALID_COMMANDS = ['watched', 'kanguo']
    
    def __init__(self, parsed, collections):
        super(WatchedCommandExecutor, self).__init__(parsed, collections)
        
    def execute(self):
        if (self._length < 2 or self._length > 3):
            raise InvalidCommandError("Must have 1 or 2 arguments, got {0}"
                                      .format(self._length))
        coll = self._find_collection(self._parsed[1])
        if not coll:
            raise InvalidCommandError("Subject name {0} not found"
                                      .format(self._parsed[1]))
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
            
    

        
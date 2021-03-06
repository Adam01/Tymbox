from enum import IntEnum, Enum

from PyQt5.QtCore import QObject
from termcolor import colored

class LogLevel(IntEnum):
    Off         = 0
    Fatal       = 1
    Errors      = 2
    Warnings    = 3
    Info        = 4
    Debug       = 5
    ExtraDebug  = 6

class LogColour(Enum):
    Off         = (None,    [])
    Fatal       = ("red",   ["bold"])
    Errors      = ("red",   [])
    Warnings    = ("yellow",[])
    Info        = (None,    [])
    Debug       = (None,    ["dark"])
    ExtraDebug  = (None,    ["dark"])

class LogHelper(object):
    def __init__(self, name=None):
        self.__level = LogLevel.ExtraDebug
        self.__name = repr(self) if name is None else name
        self.__qobject_name = False

        if isinstance(self, QObject):
            if name is not None:
                self.__qobject_name = True
                self.objectNameChanged.connect(self.__on_qobject_name_changed)


    def __on_qobject_name_changed(self, name: str):
        if self.__qobject_name:
            self.__name = self.objectName()

    def set_log_level(self, level: LogLevel):
        self.__level = level

    def get_log_level(self):
        return self.__level

    def set_log_name(self, name: str):
        self.__name = name
        self.__qobject_name = False

    def log_fatal(self, *args, **kwargs):
        self.log_msg(LogLevel.Fatal, *args, **kwargs)

    def log_error(self, *args, **kwargs):
        self.log_msg(LogLevel.Errors, *args, **kwargs)

    def log_warning(self, *args, **kwargs):
        self.log_msg(LogLevel.Warnings, *args, **kwargs)

    def log_info(self, *args, **kwargs):
        self.log_msg(LogLevel.Info, *args, **kwargs)

    def log_debug(self, *args, **kwargs):
        self.log_msg(LogLevel.Debug, *args, **kwargs)

    def log_extra_debug(self, *args, **kwargs):
        self.log_msg(LogLevel.ExtraDebug, *args, **kwargs)

    def get_qobject_path_prefix(self):
        if isinstance(self, QObject):
            object_path = []
            parent = self.parent() # type: QObject
            while parent is not None:
                if isinstance(parent, LogHelper):
                    object_path.insert(0, parent.__name)
                else:
                    object_path.insert(0, parent.objectName())
                parent = parent.parent()

            if len(object_path) > 0:
                return ":".join(object_path) + ":"
        return ""

    def log_msg(self, level: LogLevel, *args, **kwargs):
        # TODO integrate with python logging
        if self.__level >= level:
            log_colour, log_attrs = LogColour.__dict__["_member_map_"][level.name].value
            object_prefix = self.get_qobject_path_prefix()
            name_length = len(object_prefix) + len(self.__name) + 4
            object_name = object_prefix + colored(self.__name, color="blue", attrs=["bold"])
            if len(args):
                str_args = [str(v) for v in args]
                print(object_name, colored(" ".join(str_args), color=log_colour, attrs=log_attrs))
                if len(kwargs):
                    print("".join([ "%s%s=%s\n" % ("".rjust(name_length),
                                                    colored(name, color="blue", attrs=["bold"]),
                                                    colored(repr(value), color="white", attrs=[]))
                                    for name, value in kwargs.items()]))
            elif len(kwargs):
                print(object_name, ":", " ".join(["%s=%s\n" % (colored(name, color="blue", attrs=["bold"]),
                                                               colored(repr(value), color="white", attrs=[]))
                                                  for name, value in kwargs.items()]))

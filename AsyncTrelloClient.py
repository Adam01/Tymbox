from __future__ import unicode_literals

import trello
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject
from TrelloConfig import TrelloConfig


trello.Organization.TIMEZONE = "UTC"

class GenericMethodThread(QThread):

    sig_data = pyqtSignal(object, name="sig_data")

    def __init__(self, method, parent=None):
        QThread.__init__(self, parent)
        self.method = method

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        if "slot_callback" in kwargs:
            self.sig_data.connect(kwargs["slot_callback"], Qt.QueuedConnection)
            del kwargs["slot_callback"]
        self.start()

    def run(self):
        self.sig_data.emit(self.method(*self.args, **self.kwargs))


# noinspection PyAbstractClass
class AsyncTrelloClient(trello.TrelloClient, QObject):
    def __init__(self, trello_config: TrelloConfig, parent=None):
        QObject.__init__(self, parent)
        self.client = trello.TrelloClient(**trello_config.client_config)

    def __getattribute__(self, item):
        attr = super(AsyncTrelloClient, self).__getattribute__("client").__getattribute__(item)
        if attr is not None:
            if callable(attr):
                return GenericMethodThread(attr, self)
            else:
                return attr
        return super(AsyncTrelloClient, self).__getattribute__(item)


# noinspection PyAbstractClass
class AsyncTrelloWrapper(QObject):
    def __init__(self, trello_obj, parent=None):
        QObject.__init__(self, parent)
        self.trello_obj = trello_obj

    def __getattribute__(self, item):
        attr = super(AsyncTrelloWrapper, self).__getattribute__("trello_obj").__getattribute__(item)
        if attr is not None:
            if callable(attr):
                return GenericMethodThread(attr, self)
            else:
                return attr
        return super(AsyncTrelloWrapper, self).__getattribute__(item)
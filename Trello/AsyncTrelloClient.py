from __future__ import unicode_literals

import trello
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject
from Trello.TrelloConfig import TrelloConfig


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
        try:
            self.sig_data.emit(self.method(*self.args, **self.kwargs))
        except:
            self.sig_data.emit(None)


# noinspection PyAbstractClass
class AsyncTrelloClient(trello.TrelloClient, QObject):

    config_updated = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.client = None

    def load_from_file(self, config_file):
        config = TrelloConfig()
        if config.load_from_file(config_file):
            self.setup_from_config(config)

    def setup_from_config(self, config: TrelloConfig):
        self.client = trello.TrelloClient(**config.client_config)
        self.config_updated.emit()

    def __getattribute__(self, item):
        client_obj = super(AsyncTrelloClient, self).__getattribute__("client")
        attr = client_obj.__getattribute__(item) if client_obj is not None else None
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
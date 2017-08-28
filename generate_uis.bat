@echo off
SET PATH=%PATH%;C:\Python35\Lib\site-packages\PyQt5

pyuic5 Views\Tymbox\TymBox.ui > Views\Generated\TymBox.py & echo Generated TymBox.ui
pyuic5 Views\Tymbox\TymBoxTaskView.ui > Views\Generated\TymBoxTaskView.py & echo Generated TymBoxTaskView.ui
pyuic5 Views\Debug\DebugTableView.ui > Views\Generated\DebugTableView.py & echo Generated DebugTableView.ui
@echo off
SET PATH=%PATH%;C:\Python35\Lib\site-packages\PyQt5

pyuic5 Views\Tymbox\TymBox.ui > Views\Generated\TymBox.py & echo Generated TmyBox.ui
pyuic5 Views\Debug\DebugTableView.ui > Views\Generated\TableView.py & echo Generated DebugTableView.ui
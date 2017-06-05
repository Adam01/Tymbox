@echo off
SET PATH=%PATH%;C:\Python35\Lib\site-packages\PyQt5

pyuic5 TymBox.ui > ui_TymBox.py & echo Generated TmyBox.ui
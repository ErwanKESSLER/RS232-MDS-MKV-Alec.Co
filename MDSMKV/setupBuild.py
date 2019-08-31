import sys
from cx_Freeze import setup, Executable


build_exe_options = {"packages": ["os","logging","PySimpleGUI","datetime","threading","sys","serial","time","PIL","calendar","glob","io","base64"]}
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "MDSMKV",
        version = "0.1",
        description = "Tool to communication with Alec Co sensor",
        options = {"build_exe": build_exe_options},
        executables = [Executable("main.py", base=base)])
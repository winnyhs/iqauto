# -*- coding: utf-8 -*-
from distutils.core import setup
import py2exe

setup(
    options={
        "py2exe": {
            "bundle_files": 1,
            "compressed": True,
            "optimize": 2,
            "dll_excludes": ["w9xpopen.exe"],
        }
    },
    zipfile=None,
    windows=[{"script": "detect_arrow_gui.py"}],
)

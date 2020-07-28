#!/usr/bin/env python
# https://python-packaging-tutorial.readthedocs.io/en/latest/setup_py.html
from setuptools import setup

setup(name             = 'attnmgr',
      version          = '1.0',
      # list folders, not files
      packages         = ['attnmgr'],
      scripts          = ['attnmgr/bin/attnmgr.py', 'attnmgr/bin/reqattn.py'],
      # package_data     = {'attnmgr': ['data/shell.zsh']},
      data_files       = [('share/attmgr', ['attnmgr/data/shell.zsh'])],
      install_requires = [])
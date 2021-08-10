#!/usr/bin/env python
# https://python-packaging-tutorial.readthedocs.io/en/latest/setup_py.html
from setuptools import setup

setup(name             = 'attnmgr',
      version          = '1.0',
      # list folders, not files
      # packages         = ['attnmgr'],
      scripts          = ['bin/attnmgr', 'bin/reqattn'],
      # package_data     = {'attnmgr': ['data/shell.zsh']},
      data_files       = [('share/attnmgr', ['share/attnmgr-hook.zsh'])],
      package_dir={"": "src"},
      packages=setuptools.find_packages(where="src")
      install_requires = [])

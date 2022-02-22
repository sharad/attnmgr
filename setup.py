#!/usr/bin/env python
# https://python-packaging-tutorial.readthedocs.io/en/latest/setup_py.html
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name             = 'attnmgr',
                 version          = '3.0',
                 # list folders, not files
                 # packages         = ['attnmgr'],
                 scripts          = ['bin/attnmgr', 'bin/reqattn'],
                 # package_data     = {'attnmgr': ['data/shell.zsh']},
                 data_files       = [('share', ['share/attnmgr-hook.zsh'])],
                 package_dir={"": "src"},
                 packages=setuptools.find_packages(where="src"),
                 install_requires = [])

#!/usr/bin/env python

from distutils.core import setup
import os
from setuptools import find_packages

name = 'Mikko Korpela'
# I might be just a little bit too much afraid of those bots..
address = name.lower().replace(' ', '.')+chr(64)+'gmail.com'

setup(name='robpy',
      version='0.1',
      description='Test runner - Robot Framework pure Python runner',
      author=name,
      author_email=address,
      url='https://github.com/mkorpela/robpy',
      packages=find_packages(),
      scripts = [os.path.join('scripts', 'robpy'), os.path.join('scripts', 'robpy.bat')],
      license='Apache License, Version 2.0',
      install_requires = ['robotframework'])

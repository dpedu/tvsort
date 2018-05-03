#!/usr/bin/env python3
from setuptools import setup

setup(name='tvsort',
      version='0.0.2',
      description='CLI tool to sort tv shows into directories',
      url='http://gitlab.xmopx.net/dave/tvsort',
      author='dpedu',
      author_email='dave@davepedu.com',
      packages=['tvsort'],
      entry_points={
          'console_scripts': [
              'tvsort = tvsort.cli:main'
          ]
      },
      zip_safe=True)

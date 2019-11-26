#!/usr/bin/env python3
"""
Created on Mon Nov 25 17:31:20 2019

@author: mikhail-matrosov
"""

from distutils.core import setup


try:
    LONG_DESCRIPTION = open('README.rst').read()
except:
    LONG_DESCRIPTION = ''

setup(
  name = 'pycoercer',
  packages = ['pycoercer'],
  version = '0.1',
  license = 'MIT',
  description = 'Fast Python JSON schema validation and normalization',
  long_description = LONG_DESCRIPTION,
  author = 'Mikhail Matrosov',
  author_email = 'mm@tardis3d.ru',
  url = 'https://github.com/mikhail-matrosov/pycoercer',
  download_url = 'https://github.com/mikhail-matrosov/pycoercer/releases/download/0.1/pycoercer-0.1.tar.gz',
  keywords = ['validation', 'schema', 'json', 'normalization', 'coercion'],
  install_requires = [],
  platforms=["any"],
  tests_require=["pytest"],

  classifiers = [
    'Development Status :: 3 - Alpha',  # 3 - Alpha, 4 - Beta or 5 - Production/Stable
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ]
)

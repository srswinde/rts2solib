#!/usr/bin/env python


from setuptools import setup, find_packages

setup(name='rts2solib',
      version='1.0',
      description='RTS2 python library for steward observatory',
      author='Scott Swindell',
      author_email='scottswindell@email.arizona.edu',
      scripts = ['scripts/targetscript.py'],
      packages = find_packages(),
     )


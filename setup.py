#!/usr/bin/env python3

from setuptools import setup, find_packages
from specfrompypi import __version__ as version

print(find_packages('.'))

setup(
    name='specfrompypi',
    version=version,
    install_requires=['Jinja2>=2.8',
                      'click',
                      'requirements-parser>=0.0.4',
                      'requests>=2.7.0'],
    description='Python utility to create spec files from pypi',
    author='Juliano Martinez',
    packages=find_packages('.'),
    package_data={'specfrompypi': ['templates/python-spec.tmpl']},
    entry_points = {
        'console_scripts': ['spec-from-pypi=specfrompypi:run'],
    }
)

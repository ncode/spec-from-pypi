# spec-from-pypi - Python utility to create spec files from pypi 

### Install:
  
    $ python setup.py build
    $ python setup.py install

### Usage:

    $ spec-from-pypi package-name

### Depends:
* Jinja2 (>=2.8)
* requirements-parser (>=0.0.4)
* requests (>=2.7.0)

### Compatibility
Python2 and Python3

### Todo
* Automatically create spec files for the dependencies
* Detect scripts and console scripts from setup.py

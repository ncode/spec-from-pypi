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

#### Acknowledgment

Specfrompypi was originally developed for [Booking.com](http://www.booking.com).
With approval from [Booking.com](http://www.booking.com), the code and
specification were generalized and published as Open Source on github, for
which the authors would like to express their gratitude.

#### Copyright and License

Copyright (C) 2015 by Juliano Martinez

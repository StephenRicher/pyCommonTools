#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

from setuptools import setup, find_packages, Command
import sys, re, os, io
from shutil import rmtree

# Package meta-data.
NAME = 'pyCommonTools'
DESCRIPTION = ('Set of tools to perform common tasks across bioinformatics '
               'tools. These include reading/writing SAM/BAM/GZIP files '
               'and exception logging.')
URL = 'https://github.com/StephenRicher/common_tools'
EMAIL = 'sr467@bath.ac.uk'
AUTHOR = 'Stephen Richer'
REQUIRES_PYTHON = '>=3.6.0'
SCRIPTS = []
REQUIRED = []

here = os.path.abspath(os.path.dirname(__file__))

def get_version():
    try:
        with io.open(os.path.join(here, f'{NAME}/_version.py'), 
                encoding='utf-8') as f:
            for line in f:
                mo = re.match("__version__ = '([^']+)'", line)
                if mo:
                    ver = mo.group(1)
                    return ver
        return None
    except FileNotFoundError:
        return None

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, 'README.md'), 
            encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system(f'git tag v{get_version()}')
        os.system('git push --tags')

        sys.exit()

setup(name = NAME,
    version = get_version(),
    description = DESCRIPTION,
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = AUTHOR,
    author_email = EMAIL,
    python_requires = REQUIRES_PYTHON,
    url = URL,
    license = 'MIT',
    packages = find_packages(),
    install_requires = REQUIRED,
    scripts = SCRIPTS,
    setup_requires = ['pytest-runner'],
    tests_require = ['pytest'],
    zip_safe = False,
    # $ python setup.py upload
    cmdclass={
        'upload': UploadCommand,
    }
)

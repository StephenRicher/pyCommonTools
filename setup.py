#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Module of commononly used functions, classes and tools for research
    software development.
"""

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

from setuptools import setup, find_packages, Command
from shutil import rmtree
import sys
import re
import os
import io


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
        os.system(f'{sys.executable} setup.py sdist bdist_wheel --universal')

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system(f'git tag v{get_version()}')
        os.system('git push --tags')

        sys.exit()


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


version = {}
with open('version.py') as fp:
    exec(fp.read(), version)

setup(
    name='pyCommonTools',
    author='Stephen Richer',
    author_email='sr467@bath.ac.uk',
    url='https://github.com/StephenRicher/pyCommonTools',
    python_requires='>=3.6.0',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
    ],
    version=version['__version__'],
    description=__doc__,
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    py_modules=['pyCommonTools'],
    zip_safe=False,
    # $ python setup.py upload
    cmdclass={
        'upload': UploadCommand,
    }
)

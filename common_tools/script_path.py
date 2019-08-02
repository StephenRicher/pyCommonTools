#!/usr/bin/env python3

"""
Retrieve absolute directory of python3 script. Useful for calling bash scripts
from python3 that are stored in the same directory as the python3 script.
"""

import os, sys, logging

def directory(path):
    
    """ Return absolute directory of python3 script. """
    
    fun_name = sys._getframe().f_code.co_name
    log = logging.getLogger(f'{__name__}.{fun_name}')
    
    try:
        dirname = os.path.dirname(os.path.realpath(path)) + '/'
    except NameError:
        log.exception(f'{path} is not defined.')
        raise
    
    return dirname

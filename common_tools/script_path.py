#!/usr/bin/env python3

"""
Retrieve absolute directory of python3 script. Useful for calling bash scripts
from python3 that are stored in the same directory as the python3 script.
"""

import os, sys, logging

def script_path():
    
    """ Return absolute directory of python3 script. """
    
    fun_name = sys._getframe().f_code.co_name
    log = logging.getLogger(f'{__name__}.{fun_name}')
    
    try:
        path = '/'.join(os.path.realpath(__file__).split('/')[0:-1]) + '/'
    except NameError:
        log.error('Function was not called from python3 script.')
        raise
    
    return path

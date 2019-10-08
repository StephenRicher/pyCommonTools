#!/usr/bin/env python3

import sys, logging

def create_logger():
    # Get name of function that called create_logger()
    function_name = sys._getframe(1).f_code.co_name
    return logging.getLogger(f'{__name__}.{function_name}')
    
def initiliase_logger(
        log_output = None,
        log_level = logging.DEBUG,
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'):

    (logging.basicConfig(
        filename = log_output,
        format = log_format,
        level = log_level))
    sys.excepthook = log_uncaught_exception

def log_uncaught_exception(exc_type, exc_value, exc_traceback):

    ''' Redirect uncaught exceptions (excluding KeyboardInterrupt) 
        through the logging module. 
    '''

    log = create_logger()

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    (log.critical(
        "Uncaught exception",
        exc_info = (exc_type, exc_value, exc_traceback)))

from distutils import dir_util
from random import choice
import os
import re
import io
import sys
import contextlib
import subprocess
import logging
import binascii
import stat
import gzip
import argparse
import pytest
import inspect
import time
import builtins

# --------- Testing --------- #


@pytest.fixture
def datadir(tmpdir, request):

    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely. datadir can be used just like tmpdir.

    def test_foo(datadir):
        expected_config_1 = datadir.join('hello.txt')
        a = expected_config_1.read())

    '''

    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir

# --------- Logging --------- #


def create_logger(
        initialise=False, output=None, level=logging.DEBUG,
        log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):

    # Get function name that called create_logger().
    function_name = inspect.stack()[1][3]
    # Get module name that called create_logger().
    module_name = inspect.getmodule(inspect.stack()[1][0]).__name__

    log = logging.getLogger(f'{module_name}.{function_name}')

    if initialise:
        logging.basicConfig(
            filename=output, format=log_format, level=level)
        sys.excepthook = _log_uncaught_exception

    return log

def _log_uncaught_exception(exc_type, exc_value, exc_traceback):

    ''' Redirect uncaught exceptions (excluding KeyboardInterrupt)
    through the logging module.
    '''

    log = create_logger()

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.critical(
        fancy('Uncaught exception', colour='red'),
        exc_info=(exc_type, exc_value, exc_traceback))


# --------- File Opening --------- #


@contextlib.contextmanager
def open(filename: str = None, mode: str = 'r',
        stderr: bool = False, *args, **kwargs):

    """ Wrapper to 'open()' that interprets '-' as stdout or stdin.
        Ref: https://stackoverflow.com/a/45735618
    """

    if not filename: filename = '-'

    if filename == '-':
        if 'r' in mode:
            stream = sys.stdin
        else:
            if stderr:
                stream = sys.stderr
            else:
                stream = sys.stdout
        if 'b' in mode:
            fh = stream.buffer
        else:
            fh = stream
    else:
        fh = builtins.open(filename, mode, *args, **kwargs)

    try:
        yield fh
    finally:
        if filename != '-':
            fh.close()

# --------- Classes --------- #


class cached_property(object):
    '''Decorator for read-only properties evaluated once within TTL period.

    https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties

    It can be used to create a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 300 seconds (5 minutes). Set the TTL to
    zero for the cached value to never expire.

    To expire a cached property value manually just do::

        del instance._cache[<property name>]

    '''
    def __init__(self, ttl=0):
        self.ttl = ttl

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, now)
        return value

# --------- Class input validation --------- #


class IntRange():
    """ Descriptor to validate attribute format with custom
    integer range.

    e.g.
    class Person()
        age = IntRange(0, 100)
    """

    def __init__(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError(f'Error: {self.name} must be integer.')
        elif not self.minimum <= value <= self.maximum:
            raise ValueError(f'Error: {self.name} out of range.')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class RegexMatch():
    """ Descriptor to validate attribute format with custom
    regular expression.

    e.g.
    class Person()
        name = RegexMatch(r'^[!-?A-~]+$')
    """

    def __init__(self, regex):
        self.regex = re.compile(regex)

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError(f'Error: {self.name} must be string.')
        elif not re.match(self.regex, value):
            raise ValueError(f'Invalid format in {self.name}.')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


# --------- Command line arguments --------- #

def make_parser(
        prog = None, verbose = False, description = None,
        infile = False, nargs = '?', in_type = 'INFILE', version = None,
        epilog = 'Stephen Richer, University of Bath, Bath, UK (sr467@bath.ac.uk)',
        formatter_class = argparse.HelpFormatter):

    if not description:
        module = inspect.getmodule(inspect.stack()[1][0])
        description = inspect.getdoc(module)

    parents = []
    parents.append(get_base_args(
        formatter_class, version = version, verbose = verbose))
    if infile:
        parents.append(get_in_arg(
			formatter_class, nargs=nargs, in_type=in_type))

    return argparse.ArgumentParser(
        prog=prog, parents=parents, description=description,
        formatter_class=formatter_class, epilog=epilog)

def get_in_arg(
	formatter_class=argparse.HelpFormatter, in_type = 'INFILE', nargs = '?'):

    inout = argparse.ArgumentParser(
        formatter_class=formatter_class,
        add_help=False)
    inout.add_argument(
        'infile', nargs=nargs, metavar = in_type.upper(),
        help='(default: stdin)')

    return inout

def get_base_args(formatter_class=argparse.HelpFormatter,
        version = None, verbose = True):

    base = argparse.ArgumentParser(
        formatter_class=formatter_class,
        add_help=False)
    if verbose:
        base.add_argument(
            '--verbose', action='store_true',
            help='Verbose logging for debugging.')
    if version:
        base.add_argument(
            '--version', action='version', version=f'%(prog)s {version}')

    return base

def make_subparser(parser):
    """ Creates default arguments for all command line subparsers.
    Returns a subparser configuration and base arguments.
    """

    return parser.add_subparsers(
        title='required commands',
        description='',
        dest='command',
        metavar='Commands',
        help='Description:')


def execute(parser):
    """ Use in conjunction with pct.mark_parser() to execute
    specific command.
    """

    args = parser.parse_args()

    try:
        func = args.function
    except AttributeError:
        parser.print_help()
        sys.exit(1)

    level = logging.DEBUG if args.verbose else None
    log = create_logger(initialise=True, level=level)

    args_dict = vars(args)

    [args_dict.pop(key) for key in ['function', 'verbose']]
    try:
        args_dict.pop('command')
    except KeyError:
        pass

    return func(**vars(args))


def positive_int(value):
    ''' Custom argparse type for positive integer. '''

    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            f'{value} is not a positive integer.')

    return ivalue


def interval(value):
    ''' Custom argparse type for float between 0 and 1. '''

    ivalue = float(value)
    if 0 >= ivalue > 1:
        raise argparse.ArgumentTypeError(
            f'{value} is not within interval: 0 > x <= 1.')

    return ivalue


# --------- GFF3 processing --------- #

class GFF3:

    def __init__(self, record):
        self.record = record.strip().split('\t')

    def __repr__(self):
        return '\t'.join(self.record)

    def split_tags(self, tags: str):
        attributes = {}
        tags = [i.split('=') for i in tags.split(';')]
        for tag in tags:
            if tag:
                attributes[tag[0]] = tag[1]
        return attributes

    @property
    def seqname(self):
        return self.record[0]

    @property
    def source(self):
        return self.record[1]

    @property
    def feature(self):
        return self.record[2]

    @property
    def start(self):
        return self.record[3]

    @property
    def end(self):
        return self.record[4]

    @property
    def score(self):
        return self.record[5]

    @property
    def strand(self):
        return self.record[6]

    @property
    def frame(self):
        return self.record[7]

    @property
    def attributes(self):
        return self.split_tags(self.record[8])

# --------- SAM/BAM processing --------- #


@contextlib.contextmanager
def open_sam(filename: str = '-', mode: str = 'r', header: bool = True,
             samtools: str = 'samtools'):

    """ Custom context manager for reading and writing SAM/BAM files. """

    log = create_logger()

    if mode not in ['r', 'w', 'wt', 'wb', 'rt', 'rb']:
        log.error(f'Invalid mode {mode} for open_sam.')
        sys.exit(1)
    elif named_pipe(filename):
        log.error(f'Input file {filename} is a named pipe. open_sam() cannot '
                   'read files passed by process substitution.')
        sys.exit(1)

    if 'r' in mode:
        command = ['samtools', 'view', filename]
        if header:
            command.insert(2, '-h')
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, encoding='utf8')
        fh = p.stdout

    else:
        command = ['samtools', 'view', '-o', filename]
        if 'b' in mode:
            command.insert(2, '-b')
        if header:
            command.insert(2, '-h')
        p = subprocess.Popen(
            command, stdin=subprocess.PIPE, encoding='utf8')
        fh = p.stdin

    try:
        yield fh
    finally:
        fh.close()


class Sam:

    def __init__(self, record):
        record = record.strip().split('\t')
        self.qname = record[0]
        self.flag = int(record[1])
        self.rname = record[2]
        self.left_pos = int(record[3])
        self.mapq = int(record[4])
        self.cigar = record[5]
        self.rnext = record[6]
        self.pnext = int(record[7])
        self.tlen = int(record[8])
        self.seq = record[9]
        self.qual = record[10]
        self.optional = self.read_opt(record[11:])

    def read_opt(self, all_opts):
        """ Process optional SAM files into a dictionary """
        d = {}
        for opt in all_opts:
            tag_and_type = opt[0:opt.rindex(':')]
            type_ = opt.split(':')[1]
            value = opt[opt.rindex(':') + 1:]
            if type_ == 'i':
                value = int(value)
            elif type_ == 'f':
                value = float(value)
            d[tag_and_type] = value
        return d

    def get_opt(self, opt):
        """ Output optional SAM fields as tab-delimated string """
        opt_out = ""
        for tag_and_type, value in opt.items():
            opt_out += f'{tag_and_type}:{value}\t'
        return opt_out.strip()

    @cached_property()
    def is_reverse(self):
        return True if (self.flag & 0x10 != 0) else False

    @cached_property()
    def is_read1(self):
        return True if (self.flag & 0x40 != 0) else False

    @cached_property()
    def is_paired(self):
        return True if (self.flag & 0x1 != 0) else False

    @cached_property()
    def reference_length(self):
        cigar_split = re.findall(r'[A-Za-z]+|\d+', self.cigar)
        length = 0
        for idx, val in enumerate(cigar_split):
            if idx & 1 and val not in ["I", "S", "H", "P"]:
                length += int(cigar_split[idx-1])
        return length

    @cached_property()
    def right_pos(self):
        return self.left_pos + (self.reference_length - 1)

    @cached_property()
    def five_prime_pos(self):
        if self.is_reverse:
            return self.right_pos
        else:
            return self.left_pos

    @cached_property()
    def three_prime_pos(self):
        return self.left_pos if self.is_reverse else self.right_pos

    @cached_property()
    def middle_pos(self):
        return round((self.right_pos + self.left_pos)/2)

    def get_record(self):
        return (f'{self.qname}\t{self.flag}\t{self.rname}\t{self.left_pos}\t'
                f'{self.mapq}\t{self.cigar}\t{self.rnext}\t{self.pnext}\t'
                f'{self.tlen}\t{self.seq}\t{self.qual}\t'
                f'{self.get_opt(self.optional)}\n')


# --------- Formatting --------- #


def fancy(string: str = '', colour: str = 'black', multi: bool = False,
          bold: bool = True, underline: bool = False):

    log = create_logger()

    colours = {
        'black': '',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'darkcyan': '\033[36m',
        'blue': '\033[94m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
    }

    if colour not in colours:
        log.error(f'{colour} is not a valid colour - setting to black.'
                  f' Please choose from {list(colours.keys())}.')
        colour = 'black'

    b = '\033[1m' if bold else ''
    u = '\033[4m' if underline else ''

    if multi:
        # Back text not included in multi colour text.
        colours.pop('black')
        chars = []
        for char in string:
            random_colour = colours[choice(list(colours))]
            chars.append(f'{random_colour}{b}{u}{char}\033[0m')
        fancy_string = ''.join(chars)
    else:
        colour = colours[colour]
        fancy_string = f'{colour}{b}{u}{string}\033[0m'

    return fancy_string

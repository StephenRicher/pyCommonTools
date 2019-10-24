from distutils import dir_util
from pytest import fixture
import os

@fixture
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

import pytest
from mock import MarlinProc


@pytest.fixture()
def port():
    class Port:
        def __init__(self):
            self.outq = b''

        def read(self, count):
            return b'K'

        def write(self, data):
            self.outq += data

    return Port()


def test_1(port):
    assert port.read(1) == b'K'


def test_write(port):
    port.write(b'abc')
    assert port.outq == b'abc'


def test_decode(port):
    proc = MarlinProc(port)
    assert proc._decode(b'M20') == (b'M20', {})
    assert proc._decode(b'M28 abc.g') == (b'M28', {'@': b'abc.g'})
    assert proc._decode(b'M28 B1 abc.g') == (b'M28', {'@': b'abc.g', 'B': b'1'})


def test_sd_write(port):
    filename = 'abc.g'
    proc = MarlinProc(port)
    proc._start_sd_write({'@': filename})
    proc._sd_append(filename, b'G29\n')
    proc._stop_sd_write()
    assert proc.get_file(filename) == b'G29\n'

def test_run(port):
    pass
    

if __name__ == '__main__':
    pytest.main(['./tests.py'])

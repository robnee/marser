import pytest
from mock import Buffer, Port, MarlinProc


@pytest.fixture()
def port():
    return Port()


def test_read(port):
    port.inq = Buffer(b'K')
    assert port.read(1) == b'K'


def test_write(port):
    port.write(b'abc')
    assert port.outq.value() == b'abc'


def test_decode(port):
    proc = MarlinProc(port)
    assert proc._decode(b'M20') == ('M20', {})
    assert proc._decode(b'M28 abc.g') == ('M28', {'@': 'abc.g'})
    assert proc._decode(b'M28 B1 abc.g') == ('M28', {'@':  'abc.g', 'B': '1'})


def test_sd_write(port):
    filename = 'abc.g'
    proc = MarlinProc(port)
    proc._start_sd_write({'@': filename})
    proc._sd_append(filename, b'G29\n')
    proc._stop_sd_write()
    assert proc.get_file(filename) == b'G29\n'


def test_sd_delete(port):
    filename = 'abc.g'
    proc = MarlinProc(port)
    proc._start_sd_write({'@': filename})
    proc._sd_append(filename, b'G29\n')
    proc._stop_sd_write()
    proc._delete_sd_file({'@': filename})
    with pytest.raises(KeyError):
        proc.get_file(filename)
    
def test_run(port):
    filename = 'abc.g'
    port.inq = Buffer(b'M28 abc.g\nG29\nM29\n')
    proc = MarlinProc(port)
    proc.run()
    assert proc.get_file(filename) == b'G29\n'
   

if __name__ == '__main__':
    pytest.main(['./tests.py'])
 
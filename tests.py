import pytest
from mock import Buffer, Port, MarlinProc, MarlinError


@pytest.fixture()
def port():
    return Port()


@pytest.fixture()
def proc():
    return MarlinProc(Port())


@pytest.fixture()
def procfile():
    proc = MarlinProc(Port())
    save_file(proc, 'abc.g', b'G29\n')
    return proc


def save_file(proc, filename, data):
    proc._start_sd_write({'@': filename})
    proc._sd_append(filename, data)
    proc._stop_sd_write()
    

def test_read(port):
    port.inq = Buffer(b'K')
    assert port.read(1) == b'K'


def test_write(port):
    port.write(b'abc')
    assert port.outq.value() == b'abc'


def test_dtr(port):
    assert port.dtr is False
    port.dtr = True
    assert port.dtr is True
    port.reset()
    assert port.dtr is False


def test_close(port):
    port.write(b'abc')
    port.close()
    assert port.outq.value() == b''


def test_reset(port):
    port.write(b'abc')
    port.reset()
    assert port.outq.value() == b''


def test_host_port(port):
    host_port = port.get_host_port()
    assert port.inq == host_port.outq
    assert port.outq == host_port.inq


def test_decode(port):
    proc = MarlinProc(port)
    assert proc._decode(b'M20') == ('M20', {})
    assert proc._decode(b'M28 abc.g') == ('M28', {'@': 'abc.g'})
    assert proc._decode(b'M28 B1 abc.g') == ('M28', {'@':  'abc.g', 'B': '1'})


def test_sd_write(proc):
    filename = 'abc.g'
    with pytest.raises(MarlinError):
        proc._start_sd_write({})
    proc._start_sd_write({'@': filename})
    proc._sd_append(filename, b'G29\n')
    proc._stop_sd_write()
    assert proc.get_file(filename) == b'G29\n'


def test_sd_delete(proc):
    filename = 'abc.g'
    proc._start_sd_write({'@': filename})
    proc._sd_append(filename, b'G29\n')
    proc._stop_sd_write()
    with pytest.raises(MarlinError):
        proc._delete_sd_file({})
    with pytest.raises(MarlinError):
        proc._delete_sd_file({'@': 'missing'})
    proc._delete_sd_file({'@': filename})
    with pytest.raises(KeyError):
        proc.get_file(filename)


def test_run(port):
    filename = 'abc.g'
    port.inq = Buffer(b'M28 abc.g\nG29\nM29\n')
    proc = MarlinProc(port)
    proc.run()
    assert proc.get_file(filename) == b'G29\n'
    

def test_list_sd_card(port):
    filename, data = 'abc.g', b'G29\n'
    out = f'Begin file list\n{filename} {len(data)}\nEnd file list\n'.encode()
    proc = MarlinProc(port)
    save_file(proc, filename, data)
    proc._list_sd_card()
    assert port.outq.value() == out


def test_sd_print(procfile):
    filename = 'abc.g'
    with pytest.raises(MarlinError):
        procfile._start_sd_print({})
    with pytest.raises(MarlinError):
        procfile._select_sd_file({})
    with pytest.raises(MarlinError):
        procfile._select_sd_file({'@': 'missing'})
    procfile._select_sd_file({'@': filename})
    procfile._start_sd_print({})


def test_report_sd_print_status(procfile):
    filename = 'abc.g'
    with pytest.raises(MarlinError):
        procfile._report_sd_print_status({})
    procfile._report_sd_print_status({'S': '30'})
    assert procfile.sd_status_interval == 30

    procfile._select_sd_file({'@': filename})
    procfile._start_sd_print({})
    procfile._report_sd_print_status({})


if __name__ == '__main__':
    pytest.main(['./tests.py'])


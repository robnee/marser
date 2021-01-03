import time
import pytest
from mock import Buffer, Port, MarlinProc, MarlinError, MarlinHost
from client import MarlinClient


@pytest.fixture()
def port():
    return Port()


@pytest.fixture()
def proc():
    return MarlinProc()


@pytest.fixture()
def host():
    return MarlinHost()


@pytest.fixture()
def procfile():
    proc = MarlinProc()
    proc.save_file('abc.g', b'G29\n')
    return proc


def test_read(port):
    port.inq = Buffer(b'K')
    assert port.read(1) == b'K'


def test_readline(port):
    port.inq = Buffer(b'hello\nthere\n')
    assert port.readline() == b'hello\n'
    port.inq = Buffer(b'hello')
    assert port.readline() == b'hello'


def test_write(port):
    port.write(b'abc')
    assert port.outq.value() == b'abc'


def test_dtr(port):
    assert port.dtr is False
    port.dtr = True
    assert port.dtr is True
    port.reset()
    assert port.dtr is False


def test_noise(port):
    data = b'123'
    port.error_prob['write'] = 1.0
    assert port._add_noise(data, 'read') == data
    assert port._add_noise(data, 'write') != data


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


# Proc tests


def test_decode(proc):
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
    assert proc.sd_write_filename is None


def test_sd_delete(proc):
    filename = 'abc.g'
    proc.save_file(filename, b'G29\n')
    with pytest.raises(MarlinError):
        proc._delete_sd_file({})
    with pytest.raises(MarlinError):
        proc._delete_sd_file({'@': 'missing'})
    proc._delete_sd_file({'@': filename})
    with pytest.raises(KeyError):
        proc.get_file(filename)


def test_run(proc):
    filename = 'abc.g'
    port = Port()
    assert port.outq.value() == b''
    port.inq = Buffer(b'M28 abc.g\nG29\nM29\n')
    proc.run(port)
    assert port.outq.value() == f'Writing to file: {filename}\nok\nDone saving file.\n'.encode()
    assert proc.get_file(filename) == b'G29\n'

    port.reset()
    port.inq = Buffer(b'G12345\n')
    proc.run(port)
    assert port.outq.value() == b'Unknown command: G12345\nok\n'


def test_list_sd_card(proc):
    filename, data = 'abc.g', b'G29\n'
    expected = f'Begin file list\n{filename} {len(data)}\nEnd file list\n'
    proc.save_file(filename, data)
    assert proc._list_sd_card() == expected


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


def test_print_time(procfile):
    filename = 'abc.g'
    assert procfile._print_time() == f"echo:0 min, 0 sec\n"
    procfile._select_sd_file({'@': filename})
    procfile._start_sd_print({})
    time.sleep(2)
    assert procfile._print_time() == f"echo:0 min, 2 sec\n"


def test_report_sd_print_status(procfile):
    filename = 'abc.g'
    with pytest.raises(MarlinError):
        procfile._report_sd_print_status({})
    procfile._report_sd_print_status({'S': '30'})
    assert procfile.sd_status_interval == 30

    procfile._select_sd_file({'@': filename})
    procfile._start_sd_print({})
    procfile._report_sd_print_status({})


def test_report_temperatures(proc):
    assert proc._report_temperatures() == 'T:20 E:0 B:20\n'


def test_host(host):
    host.write(b'M115')
    assert host.in_waiting == 33
    assert host.readline() == b'FIRMWARE NAME:MarlinProc V1.0\n'
    assert host.read(1) == b'o'

    host.reset()
    host.write(b'M28 xyz.g\n')
    host.write(b'G29\n')
    host.write(b'M29\n')
    assert host.readline() == b'Writing to file: xyz.g\n'

    host.reset()
    host.write(b'M30 xyz.g\n')
    assert host.readline() == b'File deleted:xyz.g\n'
    host.reset()
    host.write(b'M20')
    assert host.readline() == b'Begin file list\n'
    assert host.readline() == b'End file list\n'


def test_client(host):
    filename, data = 'xyz.gco', b'G0\nG1\n'
    client = MarlinClient(host)

    assert client.print_time() == b'echo:0 min, 0 sec\nok\n'

    client.save_file(filename, data)

    files = client.list_sd_card()
    assert files == {filename: len(data)}

    with pytest.raises(ValueError):
        client.delete_sd_file('abc.gco')
    assert client.delete_sd_file(filename) is None


if __name__ == '__main__':
    pytest.main(['-v', './tests.py'])

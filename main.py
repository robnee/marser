import sys
from argparse import ArgumentParser
from mock import MarlinError, MarlinHost

VERSION = 'V1'
DEFAULT_BAUD = 115200
DEFAULT_PORT = 'mock'


def parse_args(argv):
    parser = ArgumentParser(prog='pyload', description='pyload Bload bootloader tool.')
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, help=f'serial device ({DEFAULT_PORT})')
    parser.add_argument('-b', '--baud', default=DEFAULT_BAUD, help='baud rate')
    parser.add_argument('-x', '--reset', action='store_true', help='Reset target and exit')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('filename', default=None, nargs='?', action='store', help='gcode filename')

    return parser.parse_args(args=argv)

    
def main(argv):
    args = parse_args(argv)
    print(args)

    if args.port == 'mock':
        host = MarlinHost()
    else:
        # todo: pyserial
        import serial

        host = serial.Serial(args.port, baudrate=args.baud, bytesize=8, timeout=0)

    host.write(b'M31')
    response = host.read(host.in_waiting)
    print(response)
    assert response == b'echo:0 min, 0 sec\nok\n'

    host.proc.save_file('abc.gco', b'G0\n')
    
    host.write(b'M20')
    response = host.read(host.in_waiting)
    print(response)
    assert response == b'Begin file list\nabc.gco 3\nEnd file list\nok\n'

    host.reset()
    host.write(b'M30 xyz.g\n')
    response = host.read(host.in_waiting)
    print(response)
    assert response == b'Deletion failed, File: xyz.g\nok\n'
    host.reset()
    host.write(b'M20')
    response = host.read(host.in_waiting)
    print(response)
    assert response == b'Begin file list\nabc.gco 3\nEnd file list\nok\n'


if __name__ == "__main__":
    main(sys.argv[1:])

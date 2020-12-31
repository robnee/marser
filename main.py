import sys
import time
from argparse import ArgumentParser
from mock import MarlinProc, MarlinError, MarlinHost

VERSION = 'V1'
DEFAULT_BAUD = 115200
DEFAULT_PORT = 'mock'


def parse_args(argv=None):
    parser = ArgumentParser(prog='pyload', description='pyload Bload bootloader tool.')
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, help=f'serial device ({DEFAULT_PORT})')
    parser.add_argument('-b', '--baud', default=DEFAULT_BAUD, help='baud rate')
    parser.add_argument('-x', '--reset', action='store_true', help='Reset target and exit')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('filename', default=None, nargs='?', action='store', help='gcode filename')

    return parser.parse_args(args=argv if argv else sys.argv[1:])

    
def main():
    args = parse_args()
    print(args)
    
    if args.port == 'mock':
        host = MarlinHost()
    else:
        # todo: pyserial
        import serial

        host = serial.Serial(args.port, baudrate=args.baud, bytesize=8, timeout=0)

    host.save_file('abc.gco', b'G0\n')
    
    host.write(b'M20')
    #response = host.read(host.in_waiting)
    #print(response)
    assert host.readline() == b'Begin file list\n'
    assert host.readline() == b'abc.gco 3\n'

    host.reset()
    host.write(b'M30 xyz.g\n')
    assert host.readline() == b'File deleted:xyz.g\n'
    host.reset()
    host.write(b'M20')
    assert host.readline() == b'Begin file list\n'
    assert host.readline() == b'End file list\n'


if __name__ == "__main__":
    main()
    # this help debug in Pythonista
    # import pyload
    # pyload.run(['--port', 'mock', 'x.hex'])

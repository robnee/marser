import sys
import time
from argparse import ArgumentParser
from client import MarlinClient

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
        import mock
        port = mock.MarlinHost()
    else:
        import serial

        port = serial.Serial(args.port, baudrate=args.baud, bytesize=8, timeout=0)

    client = MarlinClient(port)

    client.set_bed_temperature(60)
    for _ in range(10):
        time.sleep(1)
        print(client.readall())


if __name__ == "__main__":
    main(sys.argv[1:])

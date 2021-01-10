#! /usr/bin/env python3

import sys
import time
from argparse import ArgumentParser
from client import MarlinClient

VERSION = 'V1'
DEFAULT_BAUD = 115200
DEFAULT_PORT = 'mock'


def parse_args(argv):
    parser = ArgumentParser(prog='marser', description='Marlin upload server')
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, help=f'serial device ({DEFAULT_PORT})')
    parser.add_argument('-b', '--baud', default=DEFAULT_BAUD, help='baud rate')
    parser.add_argument('-x', '--reset', action='store_true', help='Reset target and exit')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('watchdir', default=None, action='store', help='upload directory')

    return parser.parse_args(args=argv)


def main(argv):
    args = parse_args(argv)

    client = MarlinClient()

    if args.port == 'mock':
        import mock
        port = mock.MarlinHost()
    else:
        import serial

        port = serial.Serial(args.port, baudrate=args.baud, bytesize=8)

    client.connect(port)
    print('connected...')

    print(client.firmware_info())

    filename = 'TEST.GCO'
    with open(filename, 'rb') as f:
        gcode = f.read()

    print(client.save_file(filename, gcode))


if __name__ == "__main__":
    main(sys.argv[1:])

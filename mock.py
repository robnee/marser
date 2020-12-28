

"""
Upload a gcode file to a Marlin host and start a print job

Mock Marlin interface for testing.  Implements the serial port protocol that can be wrapped 
in a Comm object.

Attempting to create a state machine that runs on every call to the serial port read API and 
reads and writes to and from the input and output queue until the state machine blocks on a
serial read for the next icsp command byte.  At that point the inbound request can be 
satisfied from one of the two queues.

How to do that?  Perhaps this is an example of coroutine programming with yield?  That might simplify the handoff
in and out of the state machine.  Not sure how to yield out of the state machine without creating a call chain that
goes deeper and deeper.

"""

import time
import random
import logging


class Buffer:
    def __init__(self):
        self.buf = bytes()

    def __len__(self):
        return len(self.buf)

    def reset(self):
        self.buf = bytes()

    def write(self, data: bytes):
        self.buf += data

    def read(self, num_bytes: int):
        """read data"""
        if len(self.buf) < num_bytes:
            logging.info(f'{self.buf} < {num_bytes}')

        ret, self.buf = self.buf[:num_bytes], self.buf[num_bytes:]
        logging.debug(f'read: {num_bytes} {ret} buf: {self.buf}')

        return ret

    def readline(self):
        if len(self.buf) < 1:
            logging.info(f'readline: buf: {self.buf}')

        nl = self.buf.find(b'\n')
        if nl < 0:
            ret, self.buf = self.buf, bytes()
        else:
            ret, self.buf = self.buf[: nl + 1], self.buf[nl + 1:]

        return ret


class Port:
    """implements a pySerial serial.Serial object that can be connected to a mock host for
    simulation and testing.  can be configured to introduce noise into the communications for 
    error recovery testing"""

    def __init__(self):
        self._dtr = False
        self.inq = Buffer()
        self.outq = Buffer()
        self.error_prob = {'write': 0.0, 'read': 0.0}

    def _add_noise(self, data: bytes, op: str) -> bytes:
        """return data passed in with simulated transmission errors"""
        if data and random.random() < self.error_prob[op]:
            num_bytes = len(data)
            index = random.randrange(num_bytes)
            noise = bytes([random.randrange(256)])
            data = data[:index] + noise + data[index + 1:]
            logging.info(f'data error {op} {num_bytes}')

        return data

    def _clear(self):
        self.reset_input_buffer()
        self.reset_output_buffer()

    def reset(self):
        """reset the port.  typically overridden by Host"""
        self._clear()

    def get_host_port(self):
        """create a host-side port for the mock to talk to the client"""

        host_port = Port()
        host_port.inq = self.outq
        host_port.outq = self.inq

        return host_port

    @property
    def port(self):
        return 'mock'

    @property
    def dtr(self):
        return self._dtr

    @dtr.setter
    def dtr(self, state: bool):
        # detect dtr reset
        if self.dtr and not state:
            self.reset()

        self._dtr = state

    @property
    def rts(self):
        """return state of RTS output line"""
        return False

    @property
    def dsr(self):
        """return state of DSR input line"""
        return False

    @property
    def cts(self):
        """return state of CTS input line"""
        return False

    @property
    def in_waiting(self):
        return len(self.inq)

    def reset_input_buffer(self):
        self.inq.reset()

    def reset_output_buffer(self):
        self.outq.reset()

    def write(self, data: bytes):
        self.outq.write(self._add_noise(data, 'write'))

    def read(self, num_bytes: int):
        return self._add_noise(self.inq.read(num_bytes), 'read')

    def readline(self):
        return self._add_noise(self.inq.readline(), 'read')

    def send_break(self, duration: int):
        time.sleep(duration)
        self._clear()

    def open(self):
        self._clear()

    def close(self):
        pass


class Gcode:
    pass


class MarlinProc:
    """
    ;   Commands:
    ;
    ;   Gnnn
    ;
    ;   M20: list sd card:
    ;   M23: select sd file: filename
    ;   M24: start or resume sd print: [S<pos>] [T<time>]
    ;   M27: report sd print status: [C] [S<seconds>]
    ;   M28: start sd write: [B1] filename
    ;   M29: stop sd write:
    ;   M30: delete sd file: filename
    ;   M31: print time:
    ;   M115: get firmware info:
    ;
    """

    def __init__(self, port: Port):
        self.port = port
        self.clock = time.time()
        self.sd_status_interval = 1
        self.sd_filename = None
        self.files = dict()

    def reset(self):
        """reset ICSP host"""
        self.clock = time.time()

    def _decode(self, g: bytes):
        tokens = g.split()

        args = dict()
        for token in tokens[1:]:
            reg = token[:1].decode()
            print('reg', reg)
            if reg.isalpha() and reg.isupper():
                args[reg] = token[1:]
            else:
                args['@'] = token

        return tokens[0].upper(), args

    def _tick(self):
        # if enough time has passed generate some async outpout
        if time.time() - self.clock > self.sd_status_interval:
            self.clock = time.time()
            self.port.write(b'NORMAL MODE: Percent done: 90; print time remaining in mins: 24\n')

    def _sd_append(self, filename, gcode):
        self.files[filename] += gcode

    def _list_sd_card(self):
        self.port.write(b'Begin file list\n')
        for filename, data in self.files.items():
            self.port.write(f'{filename} {len(data)}\n'.encode())
        self.port.write(b'End file list\n')

    def _select_sd_file(self, args):
        self.sd_filename = args

    def _report_sd_print_status(self, args):
        if 'S' in args:
            self.sd_status_interval = int(args['S'])
        else:
            self.port.write(b'report sd_print_status')

    def _start_sd_write(self, args):
        if '@' in args:
            self.sd_write_flag = True
            self.sd_filename = args['@']
        else:
            self.port.write(b'no filename')

    def _stop_sd_write(self):
        self.sd_write_flag = False
        self.sd_filename = False

    def _delete_sd_file(self, args):
        pass

    def _print_time(self):
        self.port.write(b'print time')

    def _firmware_info(self):
        self.port.write(b'firmware info')

    def run(self):
        """process anything in the input buffer and produce output in the out buffer"""

        time.sleep(2)

        # generate asynchronous output
        self._tick()

        # process input buffer
        while self.port.in_waiting:
            time.sleep(0.002)

            # command
            g = self.ser_readline()

            # decode
            cmd, args = self._decode(g)

            # are we writing to the sd card
            if self.sd_filename and self.sd_write_flag:
                self._sd_append(self.sd_filename, g)
            else:
                # dispatch
                if cmd == b'M20':  # read config words
                    self._list_sd_card()
                elif cmd == b'M23':
                    self._select_sd_file(args)
                elif cmd == b'M27':
                    self._report_sd_print_status(args)
                elif cmd == b'M28':
                    self._start_sd_write(args)
                elif cmd == b'M29':
                    self.port.write(b'not writing to sd')
                elif cmd == b'M30':
                    self._delete_sd_file(args)
                elif cmd == b'M31':
                    self._print_time()
                elif cmd == b'M115':
                    self._firmware_info()
                else:
                    self.port.write(b'Unknown code: {cmd}')

            self.port.write(b'ok')


class MarlinHost(Port):

    def __init__(self):
        Port.__init__(self)
        self.proc = MarlinProc(self.get_host_port())

    def _run(self):
        self.proc.run()

    @property
    def in_waiting(self) -> int:
        """intercept incoming call so Proc can process its input buffer first"""
        self._run()
        return super().in_waiting

    def read(self, num_bytes: int = 1) -> bytes:
        """intercept incoming call so Proc can process its input buffer first"""

        self._run()
        return super().read(num_bytes)

    def readline(self) -> bytes:
        """intercept incoming call so Proc can process its input buffer first"""

        self._run()
        return super().readline()


def main():
    port = MarlinHost()
    print(port.readline())


if __name__ == "__main__":
    main()
    # this help debug in Pythonista
    # import pyload
    # pyload.run(['--port', 'mock', 'x.hex'])

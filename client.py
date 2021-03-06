
import time


class MarlinClient:
    FILTERS = [
        b'echo:busy: processing',
        b'echo:Now fresh file:',
    ]

    def __init__(self):
        self.port = None
        self.bed_temp = 0
        self.hotend_temp = 0

    def _process_line(self, line: bytes):
        line.replace(b'\r', b'')
        if line.startswith(b'T:'):
            return
        elif any(line.startswith(x) for x in self.FILTERS):
            return

        return line

    def connect(self, port):
        self.port = port

        # look for start
        self.port.timeout = 2
        response = self.port.readline()
        if response != b'start\n':
            raise RuntimeError(f'start expected: {response}')
        # self.port.timeout = 0.25

        while response != b'echo:SD card ok\r\n':
            response = self.port.readline()

        # wait to settle down
        time.sleep(0.5)
        port.reset_input_buffer()

    def readall(self):
        out_data = b''

        while True:
            line = self.port.readline()
            pline = self._process_line(line)
            print(f"LINE: {repr(line)} PLINE: {repr(pline)}")
            if pline:
                out_data += pline
            elif line:
                # if we filtered something then retry
                continue

            if not self.port.in_waiting:
                break

        print(f'readall: {out_data}')
        return out_data

    def save_file(self, filename: str, data: bytes):
        self.port.reset_input_buffer()
        self.port.write(f'M23 {filename}\n'.encode())
        response = self.readall()
        if response.decode() not in (f'ok\n', f'Open failed, File: {filename}.\n\nok\n'):
            raise ValueError(response)

        self.port.write(f'M28\n'.encode())
        response = self.readall()
        if response != f'Writing to file: {filename}\nok\n'.encode():
            raise ValueError(response)

        self.port.write(data)
        if self.port.in_waiting:
            response = self.readall()
            raise ValueError(response)

        self.port.write(b'M29\n')
        response = self.readall()
        if response != b'Done saving file.\n':
            raise ValueError(response)

    def list_sd_card(self):
        self.port.write(b'M20')
        response = self.readall()
        files = {}
        for line in response.strip().split(b'\n'):
            if line in (b'Begin file list', b'End file list', b'ok'):
                continue
            filename, size = line.decode().split()
            files[filename] = int(size)

        return files

    def delete_sd_file(self, filename: str):
        self.port.write(f'M30 {filename}\n'.encode())
        response = self.readall()
        if response != f'File deleted:{filename}\nok\n'.encode():
            raise ValueError(response)

    def start_print(self, filename):
        self.port.write(f'M23 {filename}\n'.encode())
        response = self.readall()
        if response != b'Writing to file: abc.gco\nok\n':
            raise ValueError(response)

    def print_time(self):
        self.port.write(f'M31\n'.encode())
        response = self.readall()

        return response

    def firmware_info(self):
        self.port.write(f'M115\n'.encode())
        response = self.readall()

        return response

    def set_hotend_temperature(self, temp: int):
        self.port.write(f'M104 S{temp}\n'.encode())

    def set_bed_temperature(self, temp: int):
        self.port.write(f'M140 S{temp}\n'.encode())

    def preheat(self, material):
        pass



class MarlinClient:
    def __init__(self, port):
        self.port = port

    def readall(self):
        # todo: add code to strip out time and temp messages
        return self.port.read(self.port.in_waiting)

    def save_file(self, filename: str, data: bytes):
        self.port.write(f'M28 {filename}\n'.encode())
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

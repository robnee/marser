

class MarlinClient:
    def __init__(self, port):
        self.port = port

    def save_file(self, filename: str, data: bytes):
        self.port.write(f'M28 {filename}\n'.encode())
        response = self.port.read(self.port.in_waiting)
        if response != f'Writing to file: {filename}\nok\n'.encode():
            raise ValueError(response)

        self.port.write(data)
        if self.port.in_waiting:
            response = self.port.read(self.port.in_waiting)
            raise ValueError(response)

        self.port.write(b'M29\n')
        response = self.port.read(self.port.in_waiting)
        if response != b'Done saving file.\n':
            raise ValueError(response)

    def list_sd_card(self):
        self.port.write(b'M20')
        response = self.port.read(self.port.in_waiting)
        files = {}
        for line in response.strip().split(b'\n'):
            if line in (b'Begin file list', b'End file list', b'ok'):
                continue
            filename, size = line.decode().split()
            files[filename] = int(size)

        return files

    def start_print(self, filename):
        self.port.write(f'M23 {filename}\n'.encode())
        response = self.port.read(self.port.in_waiting)
        if response != b'Writing to file: abc.gco\nok\n':
            raise ValueError(response)

    def preheat(self, material):
        pass

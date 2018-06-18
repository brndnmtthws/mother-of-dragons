"""Firmware handler."""

import os
import shutil
from urllib.parse import urlparse
import requests
from tempfile import NamedTemporaryFile


class Firmware:
    """Class for handling firmware files."""

    def __init__(self, firmwares_path):
        self.firmwares = {}
        self.firmwares_path = firmwares_path
        if not os.path.exists(self.firmwares_path):
            os.makedirs(self.firmwares_path)

    def get_firmware_path(self, url):
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if filename in self.firmwares:
            return self.firmwares[filename]
        else:
            # file doesn't exist locally, fetch it
            return self._fetch_firmware(url, filename)

    def _fetch_firmware(self, url, filename):
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with NamedTemporaryFile() as f:
            for chunk in r.iter_content(1024 * 60):
                f.write(chunk)
            f.flush()
            os.sync()
            path = os.path.join(self.firmwares_path, filename)
            shutil.copyfile(f.name, path)
            print('Saved filename={} firmware to path={}'.format(filename,
                                                                 path))
            self.firmwares[filename] = path
            return self.firmwares[filename]

from pytest import fixture
from mother_of_dragons.firmware import Firmware
import tempfile
import os


@fixture
def tempdir():
    return os.path.join(tempfile.gettempdir(), 'test_firmware_fetch')


def test_firmware_fetch(tempdir):
    f = Firmware(tempdir)
    url = 'https://www.google.com/robots.txt'
    filename = 'robots.txt'
    path = f.get_firmware_path(url)
    assert os.path.isfile(path)
    assert filename in f.firmwares
    assert f.firmwares[filename] == path

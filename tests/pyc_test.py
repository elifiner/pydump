import os
import sys
from shutil import copyfile


class PycTest:
    def __init__(self):
        self.workspace = os.path.dirname(os.path.abspath(__file__))
        self.base_pyc_filename = "pyc_error{}.pyc"
        self.py_filename = "pyc_error.py"

    def _get_src_and_dst(self, filename):
        src = os.path.join(self.workspace, "pyc_source", filename)
        dst = os.path.join(self.workspace, filename)
        return src, dst

    def _init_py_file(self):
        src, dst = self._get_src_and_dst(self.py_filename)
        copyfile(src, dst)

    def _get_pycache_filename(self):
        major = sys.version_info.major
        minor = sys.version_info.minor
        pycache_filename = self.base_pyc_filename.format(
            ".cpython-{0}{1}".format(major, minor))
        return pycache_filename

    def _get_test_pyc_filename(self):
        return self.base_pyc_filename.format("")

    def _create_pycache_file(self):
        from tests import pyc_error
        python_version = sys.version_info.major
        if python_version == 3:
            pycache_filename = self._get_pycache_filename()
            pycache_file_path = os.path.join(self.workspace, "__pycache__",
                                             pycache_filename)
            pyc_filename = self._get_test_pyc_filename()
            src, pyc_file_path = self._get_src_and_dst(pyc_filename)
            copyfile(pycache_file_path, pyc_file_path)

    def _remove_dst_py_file(self):
        _, dst = self._get_src_and_dst(self.py_filename)
        return os.remove(dst)

    def init_pyc_test(self):
        self._init_py_file()
        self._create_pycache_file()
        self._remove_dst_py_file()

    def get_py_source_path(self):
        pyc_filename = self._get_test_pyc_filename()
        src, _ = self._get_src_and_dst(pyc_filename)
        return os.path.dirname(src)

    @staticmethod
    def run_pyc_file():
        from tests.pyc_error import error
        error()

    def remove_dst_pyc_file(self):
        pyc_filename = self._get_test_pyc_filename()
        _, dst = self._get_src_and_dst(pyc_filename)
        return os.remove(dst)

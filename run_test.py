import pydump
from tests.folderA.multiple_layout_test import multiple_layout_test
from tests.pyc_test import PycTest


def save_pydump(func, dump_filename, extend_command=""):
    try:
        func()
    except Exception:
        filename = dump_filename + ".dump"
        print("Exception caught, writing {}".format(filename))
        pydump.save_dump(filename)
        print("Run 'python -m pydump {0}{1}' to debug".format(
            filename, extend_command))


def run_pyc_test():
    pyc_test = PycTest()
    pyc_test.init_pyc_test()
    py_source_path = pyc_test.get_py_source_path()
    extend_command = " --directory {}".format(py_source_path)
    save_pydump(pyc_test.run_pyc_file, "pyc_test", extend_command)
    pyc_test.remove_dst_pyc_file()


def run_multiple_layout_test():
    save_pydump(multiple_layout_test, "multiple_layout")


if __name__ == "__main__":
    run_pyc_test()
    run_multiple_layout_test()

from .metadata import Metadata, InformationMissingError
import json
import tempfile
import unittest


class StubMetadata:
    def __init__(self):
        self.information = [1, 2, 3]

class TestMetadataClass(unittest.TestCase):
    def test_module_identifier(self):
        m = Metadata()
        self.assertEqual(m.get_module(), 'main')
        m.set_module("test-module")
        self.assertEqual(m.get_module(), 'test-module')
        m = Metadata('test-module')
        self.assertEqual(m.get_module(), 'test-module')
        with self.assertRaises(Exception):
            m.get("version")

    def test_add_file(self):
        m = Metadata('test-module')
        m.add_file("testfile", StubMetadata())
        self.assertEqual(m.metadata["files"]["0"]["uid"], "0")
        self.assertEqual(m.metadata["files"]["0"]["filename"], "testfile")
        self.assertEqual(m.metadata["files"]["0"]["metadata"],
                         {'information': [1, 2, 3]})

    def test_write(self):
        tmpfile = tempfile.NamedTemporaryFile(mode='w+')
        m =  Metadata()
        with self.assertRaises(InformationMissingError):
            m.write(tmpfile)
        m = Metadata('test-module')
        m.add_file("testfile", StubMetadata())
        m.write(tmpfile)
        tmpfile.seek(0)
        result = tmpfile.read()
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"testfile", "metadata": {"information": [1, 2, 3]}}}, ' \
                   + '"module": "test-module"}'))
        self.assertEqual(result, expected)

    def test_read(self):
        tmpfile = tempfile.NamedTemporaryFile(mode='w+')
        m = Metadata('test-module')
        m.add_file("testfile", StubMetadata())
        m.write(tmpfile)
        tmpfile.seek(0)

        m2 = Metadata()
        m2.read(tmpfile)
        self.assertEqual(m2.metadata["version"], m.metadata["version"])
        self.assertEqual(m2.metadata["module"], m.metadata["module"])
        self.assertEqual(len(m2.metadata["files"]), 1)
        self.assertEqual(m2.metadata["files"]["0"]["uid"],
                         m.metadata["files"]["0"]["uid"])
        self.assertEqual(m2.metadata["files"]["0"]["filename"],
                         m.metadata["files"]["0"]["filename"])
        self.assertEqual(m2.metadata["files"]["0"]["metadata"],
                         m.metadata["files"]["0"]["metadata"])



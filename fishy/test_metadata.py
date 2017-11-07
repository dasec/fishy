# pylint: disable=missing-docstring
import json
import tempfile
import unittest
from .metadata import Metadata, InformationMissingError


class StubMetadata:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.information = [1, 2, 3]

class TestMetadataClass(unittest.TestCase):
    def test_module_identifier(self):
        meta = Metadata()
        self.assertEqual(meta.get_module(), 'main')
        meta.set_module("test-module")
        self.assertEqual(meta.get_module(), 'test-module')
        meta = Metadata('test-module')
        self.assertEqual(meta.get_module(), 'test-module')
        with self.assertRaises(Exception):
            meta.get("version")

    def test_add_file(self):
        meta = Metadata('test-module')
        meta.add_file("testfile", StubMetadata())
        self.assertEqual(meta.metadata["files"]["0"]["uid"], "0")
        self.assertEqual(meta.metadata["files"]["0"]["filename"], "testfile")
        self.assertEqual(meta.metadata["files"]["0"]["metadata"],
                         {'information': [1, 2, 3]})

    def test_write(self):
        tmpfile = tempfile.NamedTemporaryFile(mode='w+')
        meta = Metadata()
        with self.assertRaises(InformationMissingError):
            meta.write(tmpfile)
        meta = Metadata('test-module')
        meta.add_file("testfile", StubMetadata())
        meta.write(tmpfile)
        tmpfile.seek(0)
        result = tmpfile.read()
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"testfile", "metadata": {"information": [1, 2, 3]}}}, ' \
                   + '"module": "test-module"}'))
        self.assertEqual(result, expected)

    def test_read(self):
        tmpfile = tempfile.NamedTemporaryFile(mode='w+')
        meta = Metadata('test-module')
        meta.add_file("testfile", StubMetadata())
        meta.write(tmpfile)
        tmpfile.seek(0)

        meta2 = Metadata()
        meta2.read(tmpfile)
        self.assertEqual(meta2.metadata["version"], meta.metadata["version"])
        self.assertEqual(meta2.metadata["module"], meta.metadata["module"])
        self.assertEqual(len(meta2.metadata["files"]), 1)
        self.assertEqual(meta2.metadata["files"]["0"]["uid"],
                         meta.metadata["files"]["0"]["uid"])
        self.assertEqual(meta2.metadata["files"]["0"]["filename"],
                         meta.metadata["files"]["0"]["filename"])
        self.assertEqual(meta2.metadata["files"]["0"]["metadata"],
                         meta.metadata["files"]["0"]["metadata"])

# pylint: disable=missing-docstring
"""
This file contains tests against fishy.metadata
"""
import json
import tempfile
import unittest
from fishy.metadata import Metadata, InformationMissingError


class StubMetadata:  # pylint: disable=too-few-public-methods
    """
    stub metadata class to test serialization of hiding technique metadata
    """
    def __init__(self):
        self.information = [1, 2, 3]


class TestMetadataClass(unittest.TestCase):
    """ Tests against metadata class """
    def test_module_identifier(self):
        """ Test if setting and getting the module identifier works """
        # Test get_module without initializing module identifier
        meta = Metadata()
        self.assertEqual(meta.get_module(), 'main')
        # Test changing module identifier after initialization
        meta.set_module("test-module")
        self.assertEqual(meta.get_module(), 'test-module')
        # Test initializing with identifier
        meta = Metadata('test-module')
        self.assertEqual(meta.get_module(), 'test-module')
        # Test changing an already set module identifier
        with self.assertRaises(Exception):
            meta.set_module('should-not-change')

    def test_get_metadata_main(self):
        """ Test if setting and getting values from main context works """
        # Test if we can get and set attributes in main context
        meta = Metadata()
        meta.set("random", "foo")
        self.assertEqual(meta.get("random"), "foo")
        # Test getting a non existing key
        with self.assertRaises(Exception):
            meta.get("non-existing-key")
        # test trying to get attribute from main context, when we are in
        # module context
        meta.set_module("r")
        with self.assertRaises(Exception):
            meta.get("version")
        # Test if we can set attributes when we are in modules context
        with self.assertRaises(Exception):
            meta.set("random", "foo")

    def test_get_nonexisting_file(self):
        """ Test if getting a non existing file entry fails as expected """
        # Test access to a file providing a file_id, that does not exist
        meta = Metadata()
        with self.assertRaises(KeyError):
            meta.get_file("42")

    def test_add_file(self):
        """ Test if adding a file works """
        # Adding a file with filename
        meta = Metadata('test-module')
        meta.add_file("testfile", StubMetadata())
        self.assertEqual(meta.metadata["files"]["0"]["uid"], "0")
        self.assertEqual(meta.metadata["files"]["0"]["filename"], "testfile")
        self.assertEqual(meta.metadata["files"]["0"]["metadata"],
                         {'information': [1, 2, 3]})
        # Adding a file without filename, like stdin supplies
        meta = Metadata('test-module')
        meta.add_file(None, StubMetadata())
        self.assertEqual(meta.metadata["files"]["0"]["uid"], "0")
        self.assertEqual(meta.metadata["files"]["0"]["filename"], "0")
        self.assertEqual(meta.metadata["files"]["0"]["metadata"],
                         {'information': [1, 2, 3]})

    def test_write(self):
        """ Test if serialization of the metadata class works """
        tmpfile = tempfile.NamedTemporaryFile(mode='wb+')
        meta = Metadata()
        # Test writing if module identifier is missing
        with self.assertRaises(InformationMissingError):
            meta.write(tmpfile)
        # Test writing if version is missing. This should not work in reality.
        meta = Metadata('test-module')
        meta.metadata.pop('version')
        with self.assertRaises(InformationMissingError):
            meta.write(tmpfile)
        # Test if writing works
        meta = Metadata('test-module')
        meta.add_file("testfile", StubMetadata())
        meta.write(tmpfile)
        tmpfile.seek(0)
        result = tmpfile.read().decode("utf8")
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"testfile", "metadata": {"information": [1, 2, 3]}}}, ' \
                   + '"module": "test-module"}'))
        self.assertEqual(result, expected)

    def test_read(self):
        """ Test if deserialization from a serialized metadata class works """
        tmpfile = tempfile.NamedTemporaryFile(mode='wb+')
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

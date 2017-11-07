import io
import os
import shutil
import subprocess
import tempfile
import unittest
from .file_slack import FileSlack


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UTILSDIR = os.path.join(THIS_DIR, os.pardir, os.pardir, 'utils')
IMAGEDIR = tempfile.mkdtemp()


class TestFatFileSlack(unittest.TestCase):
    image_paths = [
        os.path.join(IMAGEDIR, 'testfs-fat12-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat16-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat32-stable1.dd'),
        ]

    @classmethod
    def setUpClass(cls):
        # create test filesystems
        cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
              + " -d " + IMAGEDIR + " -t" + "fat" + " -u -s '-stable1'"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)

    @classmethod
    def tearDownClass(cls):
        # remove created filesystem images
        shutil.rmtree(IMAGEDIR)

    def test_find_file(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                result = fatfs._find_file("long_file.txt")
                # check for file attibutes
                self.assertEqual(result.name, b'LONG_F~1')
                self.assertEqual(result.extension, b'TXT')
                self.assertFalse(result.attributes.unused)
                self.assertFalse(result.attributes.device)
                self.assertTrue(result.attributes.archive)
                self.assertFalse(result.attributes.subDirectory)
                self.assertFalse(result.attributes.volumeLabel)
                self.assertFalse(result.attributes.system)
                self.assertFalse(result.attributes.hidden)
                self.assertFalse(result.attributes.readonly)
                self.assertEqual(result.fileSize, 8001)

    def test_file_walk(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                # turn 'onedirectory' into DIR_ENTRY
                entry = fatfs._find_file("onedirectory")
                result = fatfs._file_walk(entry)
                # Assume that we only found 1 file
                self.assertEqual(len(result), 2)
                # unpack that file into result
                result = result[0]
                # check for file attibutes
                self.assertEqual(result.name, b'AFILEI~1')
                self.assertEqual(result.extension, b'TXT')
                self.assertFalse(result.attributes.unused)
                self.assertFalse(result.attributes.device)
                self.assertTrue(result.attributes.archive)
                self.assertFalse(result.attributes.subDirectory)
                self.assertFalse(result.attributes.volumeLabel)
                self.assertFalse(result.attributes.system)
                self.assertFalse(result.attributes.hidden)
                self.assertFalse(result.attributes.readonly)
                self.assertEqual(result.fileSize, 11)

    def test_write_file(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb+') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                # setup raw stream and write testmessage
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    # write testmessage to disk
                    with io.BufferedReader(mem) as reader:
                        result = fatfs.write(reader, ['another'])
                        self.assertEqual(result.clusters, [(3, 512, 28)])
                        with self.assertRaises(IOError):
                            mem.seek(0)
                            fatfs.write(reader, ['no_free_slack.txt'])

    def test_write_file_in_subdir(self):
        # only testing fat12 as resulting cluster_id of different fat
        # versions differs
        img_path = TestFatFileSlack.image_paths[0]
        with open(img_path, 'rb+') as img_stream:
            # create FileSlack object
            fatfs = FileSlack(img_stream)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = fatfs.write(reader,
                                         ['onedirectory/afileinadirectory.txt'])
                    self.assertEqual(result.clusters, [(13, 512, 28)])

    def test_write_file_autoexpand_subdir(self):
        # only testing fat12 as resulting cluster_id of different fat
        # versions differs
        # if user supplies a directory instead of a file path, all files under
        # this directory will recusively added
        img_path = TestFatFileSlack.image_paths[0]
        with open(img_path, 'rb+') as img_stream:
            # create FileSlack object
            fatfs = FileSlack(img_stream)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = fatfs.write(reader,
                                         ['onedirectory'])
                    self.assertEqual(result.clusters, [(15, 512, 28)])

    def test_read_slack(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb+') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                teststring = "This is a simple write test."
                # write content that we want to read
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fatfs.write(reader, ['another'])
                # read content we wrote and compare result with
                # our initial test message
                with io.BytesIO() as mem:
                    fatfs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    self.assertEqual(result.decode('utf-8'), teststring)

    def test_clear_slack(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb+') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                teststring = "This is a simple write test."
                # write content that we want to clear
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fatfs.write(reader, ['another'])
                    fatfs.clear(write_res)
                # clear content we wrote, then read the cleared part again.
                # As it should be overwritten we expect a stream of \x00
                with io.BytesIO() as mem:
                    fatfs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    expected = len(teststring.encode('utf-8')) * b'\x00'
                    self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()

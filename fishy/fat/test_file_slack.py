import unittest
from .file_slack import FileSlack
import os
import io
import subprocess


this_dir = os.path.dirname(os.path.abspath(__file__))
utilsdir = os.path.join(this_dir, os.pardir, os.pardir, 'utils')


class TestFatFileSlack(unittest.TestCase):
    image_paths = [
                    os.path.join(utilsdir, 'testfs-fat12.dd'),
                    os.path.join(utilsdir, 'testfs-fat16.dd'),
                    os.path.join(utilsdir, 'testfs-fat32.dd'),
                  ]

    @classmethod
    def setUpClass(cls):
        # regenerate test filesystems
        cmd = os.path.join(utilsdir, "create_testfs.sh") + " " + utilsdir
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)

    def test_find_file(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb') as f:
                # create FileSlack object
                fs = FileSlack(f)
                result = fs._find_file("long_file.txt")
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
            with open(img_path, 'rb') as f:
                # create FileSlack object
                fs = FileSlack(f)
                # turn 'onedirectory' into DirEntry
                entry = fs._find_file("onedirectory")
                result = fs._file_walk(entry)
                # Assume that we only found 1 file
                self.assertEqual(len(result), 1)
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
            with open(img_path, 'rb+') as f:
                # create FileSlack object
                fs = FileSlack(f)
                # setup raw stream and write testmessage
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    # write testmessage to disk
                    with io.BufferedReader(mem) as reader:
                        result = fs.write(reader, ['another'])
                        self.assertEqual(result.clusters, [(3, 512, 28)])

    def test_write_file_in_subdir(self):
        # only testing fat12 as resulting cluster_id of different fat
        # versions differs
        img_path = TestFatFileSlack.image_paths[0]
        with open(img_path, 'rb+') as f:
            # create FileSlack object
            fs = FileSlack(f)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = fs.write(reader,
                                      ['onedirectory/afileinadirectory.txt'])
                    self.assertEqual(result.clusters, [(9, 512, 28)])

    def test_write_file_autoexpand_subdir(self):
        # only testing fat12 as resulting cluster_id of different fat
        # versions differs
        # if user supplies a directory instead of a file path, all files under
        # this directory will recusively added
        img_path = TestFatFileSlack.image_paths[0]
        with open(img_path, 'rb+') as f:
            # create FileSlack object
            fs = FileSlack(f)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = fs.write(reader,
                                      ['onedirectory'])
                    self.assertEqual(result.clusters, [(9, 512, 28)])

    def test_read_slack(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb+') as f:
                # create FileSlack object
                fs = FileSlack(f)
                teststring = "This is a simple write test."
                # write content that we want to read
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fs.write(reader, ['another'])
                # read content we wrote and compare result with
                # our initial test message
                with io.BytesIO() as mem:
                    fs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    self.assertEqual(result.decode('utf-8'), teststring)

    def test_clear_slack(self):
        for img_path in TestFatFileSlack.image_paths:
            with open(img_path, 'rb+') as f:
                # create FileSlack object
                fs = FileSlack(f)
                teststring = "This is a simple write test."
                # write content that we want to clear
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fs.write(reader, ['another'])
                    fs.clear(write_res)
                # clear content we wrote, then read the cleared part again.
                # As it should be overwritten we expect a stream of \x00
                with io.BytesIO() as mem:
                    fs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    expected = len(teststring.encode('utf-8')) * b'\x00'
                    self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()

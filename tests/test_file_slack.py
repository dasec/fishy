# pylint: disable=missing-docstring, protected-access
import io
import os
import shutil
import subprocess
import tempfile
import unittest
import pytest
from fishy.fat.file_slack import FileSlack


class TestFileWalk:
    def test_file_walk(self, testfs_fat_stable1):
        for img_path in testfs_fat_stable1:
            print("IMAGE:", img_path)
            with open(img_path, 'rb') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                # turn 'onedirectory' into DIR_ENTRY
                entry = fatfs.fatfs.find_file("onedirectory")
                result = []
                for file_entry in fatfs._file_walk(entry):
                    result.append(file_entry)
                # Assume that we only found 1 file
                assert len(result) == 2
                # unpack that file into result
                result = result[0]
                # check for file attibutes
                assert result.parsed.name == b'AFILEI~1'
                assert result.parsed.extension == b'TXT'
                assert not result.parsed.attributes.unused
                assert not result.parsed.attributes.device
                assert result.parsed.attributes.archive
                assert not result.parsed.attributes.subDirectory
                assert not result.parsed.attributes.volumeLabel
                assert not result.parsed.attributes.system
                assert not result.parsed.attributes.hidden
                assert not result.parsed.attributes.readonly
                assert result.parsed.fileSize == 11

    def test_file_walk_nondir(self, testfs_fat_stable1):
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb') as img_stream:
                # create FileSlack object
                fatfs = FileSlack(img_stream)
                entry = fatfs.fatfs.find_file("another")
                next_file = fatfs._file_walk(entry)
                with pytest.raises(AssertionError):
                    next(next_file)

class TestWrite:
    def test_write_file(self, testfs_fat_stable1):
        for img_path in testfs_fat_stable1:
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
                        assert result.clusters, [(3, 512 == 28)]
                        with pytest.raises(IOError):
                            mem.seek(0)
                            fatfs.write(reader, ['no_free_slack.txt'])

    def test_write_file_in_subdir(self, testfs_fat_stable1):
        # only testing fat12 as resulting cluster_id of different fat
        # versions differs
        img_path = testfs_fat_stable1[0]
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
                    assert result.clusters, [(13, 512 == 28)]

    def test_write_file_autoexpand_subdir(self, testfs_fat_stable1):  # pylint: disable=invalid-name
        # only testing fat12 as resulting cluster_id of different fat
        # versions differs
        # if user supplies a directory instead of a file path, all files under
        # this directory will recusively added
        img_path = testfs_fat_stable1[0]
        with open(img_path, 'rb+') as img_stream:
            # create FileSlack object
            fatfs = FileSlack(img_stream)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."*100
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = fatfs.write(reader,
                                         ['onedirectory'])
                    assert result.clusters == [(13, 512, 1536),
                                               (15, 512, 1264)]

class TestRead:
    def test_read_slack(self, testfs_fat_stable1):
        for img_path in testfs_fat_stable1:
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
                    assert result.decode('utf-8') == teststring

class TestClear:
    def test_clear_slack(self, testfs_fat_stable1):
        for img_path in testfs_fat_stable1:
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
                    assert result == expected


if __name__ == '__main__':
    unittest.main()

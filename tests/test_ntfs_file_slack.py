# pylint: disable=missing-docstring, protected-access
"""
This file contains tests against fishy.ntfs.ntfs_file_slack, which implements the
fileslack hiding technique for NTFS filesystems
"""
import io
import pytest
from fishy.ntfs.ntfs_file_slack import NtfsSlack as FileSlack


class TestWrite:
    """ Test writing into the slack space """
    def test_write_file(self, testfs_ntfs_stable2):
        """" Test writing a file into root directory """
        for img_path in testfs_ntfs_stable2:
            with open(img_path, 'rb+') as img:
                # create FileSlack object
                ntfs = FileSlack(img_path, img)
                # setup raw stream and write testmessage
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    # write testmessage to disk
                    with io.BufferedReader(mem) as reader:
                        result = ntfs.write(reader, ['other_file.txt'])
                        assert result.addrs == [(1733632, 28)]
                        with pytest.raises(IOError):
                            mem.seek(0)
                            ntfs = FileSlack(img_path, img)
                            ntfs.write(reader, ['no_free_slack.txt'])

    def test_write_file_autoexpand_subdir(self, testfs_ntfs_stable2):  # pylint: disable=invalid-name
        """ Test if autoexpansion for directories as input filepath works """
        # if user supplies a directory instead of a file path, all files under
        # this directory will recusively added
        for img_path in testfs_ntfs_stable2:
            with open(img_path, 'rb+') as img:
                # create FileSlack object
                ntfs = FileSlack(img_path, img)
                # setup raw stream and write testmessage
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."*100
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    # write testmessage to disk
                    with io.BufferedReader(mem) as reader:
                        result = ntfs.write(reader, ['/'])
                        assert sorted(result.addrs) == sorted([(1733632, 2800)])

class TestRead:
    """ Test reading slackspace """
    def test_read_slack(self, testfs_ntfs_stable2):
        """ Test if reading content of slackspace in a simple case works """
        for img_path in testfs_ntfs_stable2:
            with open(img_path, 'rb+') as img:
                # create FileSlack object
                ntfs = FileSlack(img_path, img)
                teststring = "This is a simple write test."
                # write content that we want to read
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = ntfs.write(reader, ['other_file.txt'])
                # read content we wrote and compare result with
                # our initial test message
                ntfs = FileSlack(img_path, img)
                with io.BytesIO() as mem:
                    ntfs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    assert result.decode('utf-8') == teststring

class TestInfo:
    def test_info_slack(self, testfs_ntfs_stable2):
        """ Test if info works """
        for img_path in testfs_ntfs_stable2:
            with open(img_path, 'rb+') as img:
                # create FileSlack object
                ntfs = FileSlack(img_path, img)
                slack = ntfs.print_info(['/'])
                assert slack == 3072

class TestClear:
    def test_clear_slack(self, testfs_ntfs_stable2):
        """ Test if clearing slackspace of a file works """
        for img_path in testfs_ntfs_stable2:
            with open(img_path, 'rb+') as img:
                # create FileSlack object
                ntfs = FileSlack(img_path, img)
                teststring = "This is a simple write test."
                # write content that we want to clear
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = ntfs.write(reader, ['other_file.txt'])
                    ntfs = FileSlack(img_path, img)
                    ntfs.clear(write_res)
                    ntfs = FileSlack(img_path, img)
                # clear content we wrote, then read the cleared part again.
                # As it should be overwritten we expect a stream of \x00
                with io.BytesIO() as mem:
                    ntfs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    expected = len(teststring.encode('utf-8')) * b'\x00'
                    assert result == expected

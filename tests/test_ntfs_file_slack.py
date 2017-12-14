# pylint: disable=missing-docstring, protected-access
"""
This file contains tests against fishy.ntfs.ntfsSlackSpace, which implements the
fileslack hiding technique for NTFS filesystems
"""
import io
import pytest
from fishy.ntfs.ntfs_file_slack import NtfsSlack as FileSlack


class TestWrite:
    """ Test writing into the slack space """
    def test_write_file(self, testfs_ntfs_stable1):
        """" Test writing a file into root directory """
        for img_path in testfs_ntfs_stable1:
            # create FileSlack object
            ntfs = FileSlack(img_path)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = ntfs.write(reader, ['another'])
                    assert result.addrs == [(82296, 28)]
                    with pytest.raises(IOError):
                        mem.seek(0)
                        ntfs = FileSlack(img_path)
                        ntfs.write(reader, ['no_free_slack.txt'])

    def test_write_file_in_subdir(self, testfs_ntfs_stable1):
        """ Test writing a file into a subdirectory """
        for img_path in testfs_ntfs_stable1:
            # create FileSlack object
            ntfs = FileSlack(img_path)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = ntfs.write(reader,
                                         ['onedirectory/afileinadirectory.txt'])
                    assert result.addrs == [(87456, 28)]

    def test_write_file_autoexpand_subdir(self, testfs_ntfs_stable1):  # pylint: disable=invalid-name
        """ Test if autoexpansion for directories as input filepath works """
        # if user supplies a directory instead of a file path, all files under
        # this directory will recusively added
        for img_path in testfs_ntfs_stable1:
            # create FileSlack object
            ntfs = FileSlack(img_path)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."*129
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = ntfs.write(reader, ['/'])
                    assert sorted(result.addrs) == sorted([(82296, 134), 
                                  (82432, 510), (83392, 62), (83456, 510), 
                                  (87456, 94), (87552, 510), (88536, 38), 
                                  (88576, 510), (90496, 126), (90624, 510), 
                                  (91528, 118), (91648, 490)])

class TestRead:
    """ Test reading slackspace """
    def test_read_slack(self, testfs_ntfs_stable1):
        """ Test if reading content of slackspace in a simple case works """
        for img_path in testfs_ntfs_stable1:
            # create FileSlack object
            ntfs = FileSlack(img_path)
            teststring = "This is a simple write test."
            # write content that we want to read
            with io.BytesIO() as mem:
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                with io.BufferedReader(mem) as reader:
                    write_res = ntfs.write(reader, ['another'])
            # read content we wrote and compare result with
            # our initial test message
            ntfs = FileSlack(img_path)
            with io.BytesIO() as mem:
                ntfs.read(mem, write_res)
                mem.seek(0)
                result = mem.read()
                assert result.decode('utf-8') == teststring

class TestInfo:
    def test_info_slack(self, testfs_ntfs_stable1):
        """ Test if info works """
        for img_path in testfs_ntfs_stable1:
            # create FileSlack object
            ntfs = FileSlack(img_path)
            slack = ntfs.print_info(['/'])
            assert slack == 3632
            
class TestClear:
    def test_clear_slack(self, testfs_ntfs_stable1):
        """ Test if clearing slackspace of a file works """
        for img_path in testfs_ntfs_stable1:
            # create FileSlack object
            ntfs = FileSlack(img_path)
            teststring = "This is a simple write test."
            # write content that we want to clear
            with io.BytesIO() as mem:
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                with io.BufferedReader(mem) as reader:
                    write_res = ntfs.write(reader, ['another'])
                ntfs = FileSlack(img_path)
                ntfs.clear(write_res)
                ntfs = FileSlack(img_path)
            # clear content we wrote, then read the cleared part again.
            # As it should be overwritten we expect a stream of \x00
            with io.BytesIO() as mem:
                ntfs.read(mem, write_res)
                mem.seek(0)
                result = mem.read()
                expected = len(teststring.encode('utf-8')) * b'\x00'
                assert result == expected
# pylint: disable=missing-docstring, protected-access
"""
This file contains tests against fishy.ntfs.ntfs_mft_slack, which implements the
mftslack hiding technique for NTFS filesystems
"""
import io
import pytest
from fishy.ntfs.ntfs_mft_slack import NtfsMftSlack as MftSlack


class TestWrite:
    """ Test writing into the slack space """
    def test_write(self, testfs_ntfs_stable1):
        """" Test hiding data starting at mft root """
        for img_path in testfs_ntfs_stable1:
            # create MftSlack object
            ntfs = MftSlack(img_path)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."*30
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = ntfs.write(reader)
                    assert result.addrs == [(16792, 102), (16896, 510),
                                            (17752, 166), (17920, 62)]
                    with pytest.raises(IOError):
                        mem.seek(0)
                        ntfs = MftSlack(img_path)
                        ntfs.write(reader, 178)

    def test_write_offset(self, testfs_ntfs_stable1):
        """ Test hiding data with offset """
        for img_path in testfs_ntfs_stable1:
            # create MftSlack object
            ntfs = MftSlack(img_path)
            # setup raw stream and write testmessage
            with io.BytesIO() as mem:
                teststring = "This is a simple write test."
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                # write testmessage to disk
                with io.BufferedReader(mem) as reader:
                    result = ntfs.write(reader,36)
                    assert result.addrs == [(18776, 28)]

class TestRead:
    """ Test reading slackspace """
    def test_read_slack(self, testfs_ntfs_stable1):
        """ Test if reading content of slackspace in a simple case works """
        for img_path in testfs_ntfs_stable1:
            # create MftSlack object
            ntfs = MftSlack(img_path)
            teststring = "This is a simple write test."
            # write content that we want to read
            with io.BytesIO() as mem:
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                with io.BufferedReader(mem) as reader:
                    write_res = ntfs.write(reader)
            # read content we wrote and compare result with
            # our initial test message
            ntfs = MftSlack(img_path)
            with io.BytesIO() as mem:
                ntfs.read(mem, write_res)
                mem.seek(0)
                result = mem.read()
                assert result.decode('utf-8') == teststring

class TestInfo:
    def test_info_slack(self, testfs_ntfs_stable1):
        """ Test if info works """
        for img_path in testfs_ntfs_stable1:
            # create MftSlack object
            ntfs = MftSlack(img_path)
            slack = ntfs.print_info()
            assert slack == 59372
    def test_limit_info_slack(self, testfs_ntfs_stable1):
        """ Test if info limited works """
        for img_path in testfs_ntfs_stable1:
            # create MftSlack object
            ntfs = MftSlack(img_path)
            slack = ntfs.print_info(0, 5)
            assert slack == 3100
            
class TestClear:
    def test_clear_slack(self, testfs_ntfs_stable1):
        """ Test if clearing slackspace works """
        for img_path in testfs_ntfs_stable1:
            # create MftSlack object
            ntfs = MftSlack(img_path)
            teststring = "This is a simple write test."
            # write content that we want to clear
            with io.BytesIO() as mem:
                mem.write(teststring.encode('utf-8'))
                mem.seek(0)
                with io.BufferedReader(mem) as reader:
                    write_res = ntfs.write(reader)
                ntfs = MftSlack(img_path)
                ntfs.clear(write_res)
                ntfs = MftSlack(img_path)
            # clear content we wrote, then read the cleared part again.
            # As it should be overwritten we expect a stream of \x00
            with io.BytesIO() as mem:
                ntfs.read(mem, write_res)
                mem.seek(0)
                result = mem.read()
                expected = len(teststring.encode('utf-8')) * b'\x00'
                assert result == expected
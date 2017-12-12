"""
This file contains tests for the NTFS class
"""

import pytest
from fishy.ntfs.ntfs_filesystem.ntfs import NTFS

class TestGetBootsector(object):
    """
    Tests if the bootsectors are parsed correctly
    """
    def test_get_bootsector(self, testfs_ntfs_stable1):
        """ Tests for the main bootsector """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            bootsector = ntfs.get_bootsector()
            assert bootsector.oem_name == b'NTFS    '
            assert bootsector.eos_marker == b'\x55\xaa'

    def test_get_bootsector_copy(self, testfs_ntfs_stable1):
        """ Tests for the bootsector copy """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            bootsector = ntfs.get_bootsector_copy()
            assert bootsector.oem_name == b'NTFS    '
            assert bootsector.eos_marker == b'\x55\xaa'


class TestBasicInformation(object):
    """
    Tests if the basic information of the filesystem
    is parsed correctly
    """
    def test_parse_bootsector(self, testfs_ntfs_stable1):
        """
        Tests if the necessary information from the bootsector
        is parsed correctly
        """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            assert ntfs.cluster_size == 4096
            assert ntfs.record_size == 1024
            assert ntfs.mft_offset == 16384


    def test_mft_info(self, testfs_ntfs_stable1):
        """
        Tests the information about the mft itself
        """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            assert ntfs.mft_runs == [{'length': 77824, 'offset': 16384}]

class TestGetRecord(object):
    """ Tests if getting records works correctly """
    def test_record_alignment(self, testfs_ntfs_stable1):
        """
        Tests if the records start with the correct value
        """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            assert ntfs.get_record(0)[0:4] == b'FILE'
            assert ntfs.get_record(25)[0:4] == b'FILE'
            assert ntfs.get_record(50)[0:4] == b'FILE'
            assert ntfs.get_record(100)[0:4] == b'FILE'

    def test_record_position(self, testfs_ntfs_stable1):
        """
        Tests if the record returned is of the requested position
        """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            assert ntfs.get_record(0)[0xf2:0xfa].decode('utf-16') == '$MFT'
            assert ntfs.get_record(1)[0xf2:0x0102].decode('utf-16') == '$MFTMirr'
            assert ntfs.get_record(8)[0xf2:0x0102].decode('utf-16') == '$BadClus'


class TestGetRecordOfFile(object):
    """ Tests if getting records by filename/-path works correctly """
    def test_get_record_of_file(self, testfs_ntfs_stable1):
        """
        Tests if the correct record is returned for
        the supplied name
        """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            assert ntfs.get_record_of_file('$MFT') == 0
            assert ntfs.get_record_of_file('$MFTMirr') == 1
            assert ntfs.get_record_of_file('$BadClus') == 8
            assert ntfs.get_record_of_file('$Extend/$Reparse') == 26
            assert ntfs.get_record_of_file('notexisting') == None


class TestGetData(object):
    """ Tests if getting the data of a file works correctly """
    def test_get_data(self, testfs_ntfs_stable1):
        """
        Tests if the correct data is returned
        """
        with open(testfs_ntfs_stable1[0], 'rb') as fs:
            ntfs = NTFS(fs)
            record_another = ntfs.get_record_of_file('another')
            record_long_file = ntfs.get_record_of_file('long_file.txt')
            assert ntfs.get_data(record_another) == b'222\n'
            assert ntfs.get_data(record_long_file) == b'1'*8000 + b'\n'

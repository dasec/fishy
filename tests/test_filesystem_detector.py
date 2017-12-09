# pylint: disable=missing-docstring
"""
This file contains tests against fishy.filesystem_detector
"""
import pytest
from fishy.filesystem_detector import get_filesystem_type, UnsupportedFilesystemError


class TestFileSystemDetector(object):

    def test_fat_images(self, testfs_fat_stable1):
        """ Test if FAT images are detected correctly """
        for img in testfs_fat_stable1:
            with open(img, 'rb') as fs_stream:
                result = get_filesystem_type(fs_stream)
                assert result == 'FAT'

    def test_ntfs_images(self, testfs_ntfs_stable1):
        """ Test if NTFS images are detected correctly """
        for img in testfs_ntfs_stable1:
            with open(img, 'rb') as fs_stream:
                result = get_filesystem_type(fs_stream)
                assert result == 'NTFS'

    def test_ext4_images(self, testfs_ext4_stable1):
        """ Test if ext4 images are detected correctly """
        for img in testfs_ext4_stable1:
            with open(img, 'rb') as fs_stream:
                result = get_filesystem_type(fs_stream)
                assert result == 'EXT4'
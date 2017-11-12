# pylint: disable=missing-docstring
import pytest
from fishy.filesystem_detector import get_filesystem_type, UnsupportedFilesystemError


class TestFileSystemDetector(object):

    def test_fat_images(self, testfs_fat_stable1):
        for img in testfs_fat_stable1:
            with open(img, 'rb') as fs_stream:
                result = get_filesystem_type(fs_stream)
                assert result == 'FAT'

    def test_ntfs_images(self, testfs_ntfs_stable1):
        for img in testfs_ntfs_stable1:
            with open(img, 'rb') as fs_stream:
                result = get_filesystem_type(fs_stream)
                assert result == 'NTFS'

    def test_ext4_images(self, testfs_ext4_stable1):
        for img in testfs_ext4_stable1:
            with open(img, 'rb') as fs_stream:
                with pytest.raises(UnsupportedFilesystemError):
                    get_filesystem_type(fs_stream)

"""
This file contains tests against fishy.fat.fat_filesystem.fat_detector
"""
from fishy.fat.fat_filesystem import fat_detector

def test_get_filesystem(testfs_fat_stable1):
    """ Test if specific FAT detection works """
    with open(testfs_fat_stable1[0], 'rb') as img_stream:
        result = fat_detector.get_filesystem_type(img_stream)
        assert result == 'FAT12'
    with open(testfs_fat_stable1[1], 'rb') as img_stream:
        result = fat_detector.get_filesystem_type(img_stream)
        assert result == 'FAT16'
    with open(testfs_fat_stable1[2], 'rb') as img_stream:
        result = fat_detector.get_filesystem_type(img_stream)
        assert result == 'FAT32'

def test_is_fat(testfs_fat_stable1):
    """ Test if general FAT detection works """
    with open(testfs_fat_stable1[0], 'rb') as img_stream:
        result = fat_detector.is_fat(img_stream)
        assert result
    with open(testfs_fat_stable1[1], 'rb') as img_stream:
        result = fat_detector.is_fat(img_stream)
        assert result
    with open(testfs_fat_stable1[2], 'rb') as img_stream:
        result = fat_detector.is_fat(img_stream)
        assert result

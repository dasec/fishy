# pylint: disable=missing-docstring
import os
import io
import shutil
import subprocess
import tempfile
import unittest
from .fat_wrapper import create_fat
from . import fat_12
from . import fat_16
from . import fat_32
from . import fat_detector


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UTILSDIR = os.path.join(THIS_DIR, os.pardir, os.pardir, os.pardir, 'utils')
IMAGE_DIR = tempfile.mkdtemp()


IMAGE_PATHS = [
    os.path.join(IMAGE_DIR, 'testfs-fat12-stable1.dd'),
    os.path.join(IMAGE_DIR, 'testfs-fat16-stable1.dd'),
    os.path.join(IMAGE_DIR, 'testfs-fat32-stable1.dd'),
    ]


def setUpModule():  # pylint: disable=invalid-name
    # create test filesystems
    cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
          + " -d " + IMAGE_DIR + " -t " + "fat" + " -u -s '-stable1'"
    subprocess.call(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)


def tearDownModule():  # pylint: disable=invalid-name
    # remove created filesystem images
    shutil.rmtree(IMAGE_DIR)


class TestFatDetector(unittest.TestCase):

    def test_get_filesystem(self):
        with open(IMAGE_PATHS[0], 'rb') as img_stream:
            result = fat_detector.get_filesystem_type(img_stream)
            self.assertEqual(result, 'FAT12')
        with open(IMAGE_PATHS[1], 'rb') as img_stream:
            result = fat_detector.get_filesystem_type(img_stream)
            self.assertEqual(result, 'FAT16')
        with open(IMAGE_PATHS[2], 'rb') as img_stream:
            result = fat_detector.get_filesystem_type(img_stream)
            self.assertEqual(result, 'FAT32')

    def test_is_fat(self):
        with open(IMAGE_PATHS[0], 'rb') as img_stream:
            result = fat_detector.is_fat(img_stream)
            self.assertEqual(result, True)
        with open(IMAGE_PATHS[1], 'rb') as img_stream:
            result = fat_detector.is_fat(img_stream)
            self.assertEqual(result, True)
        with open(IMAGE_PATHS[2], 'rb') as img_stream:
            result = fat_detector.is_fat(img_stream)
            self.assertEqual(result, True)


class TestFatImplementation(unittest.TestCase):

    def test_parse_predata_region(self):
        with self.subTest(i="FAT12"):
            with open(IMAGE_PATHS[0], 'rb') as img_stream:
                fatfs = fat_12.FAT12(img_stream)
                self.assertEqual(fatfs.pre.sector_size, 512)
                self.assertEqual(fatfs.pre.sectors_per_cluster, 4)
                self.assertEqual(fatfs.pre.reserved_sector_count, 1)
                self.assertEqual(fatfs.pre.fat_count, 2)
                self.assertEqual(fatfs.pre.rootdir_entry_count, 512)
                self.assertEqual(fatfs.pre.sectors_per_fat, 2)
        with self.subTest(i="FAT16"):
            with open(IMAGE_PATHS[1], 'rb') as img_stream:
                fatfs = fat_16.FAT16(img_stream)
                self.assertEqual(fatfs.pre.sector_size, 512)
                self.assertEqual(fatfs.pre.sectors_per_cluster, 4)
                self.assertEqual(fatfs.pre.reserved_sector_count, 4)
                self.assertEqual(fatfs.pre.fat_count, 2)
                self.assertEqual(fatfs.pre.rootdir_entry_count, 512)
                self.assertEqual(fatfs.pre.sectors_per_fat, 52)
        with self.subTest(i="FAT32"):
            with open(IMAGE_PATHS[2], 'rb') as img_stream:
                fatfs = fat_32.FAT32(img_stream)
                self.assertEqual(fatfs.pre.sector_size, 512)
                self.assertEqual(fatfs.pre.sectors_per_cluster, 8)
                self.assertEqual(fatfs.pre.reserved_sector_count, 32)
                self.assertEqual(fatfs.pre.fat_count, 2)
                self.assertEqual(fatfs.pre.sectors_per_fat, 544)
                self.assertEqual(fatfs.pre.free_data_cluster_count, 68599)
                self.assertEqual(fatfs.pre.last_allocated_data_cluster, 12)
                self.assertEqual(fatfs.pre.flags.active_fat, 0)
                self.assertEqual(fatfs.pre.flags.mirrored, False)
                self.assertEqual(fatfs.pre.fsinfo_sector, 1)
                self.assertEqual(fatfs.pre.bootsector_copy_sector, 6)

    def test_get_cluster_value(self):
        with self.subTest(i="FAT12"):
            with open(IMAGE_PATHS[0], 'rb') as img_stream:
                fatfs = fat_12.FAT12(img_stream)
                self.assertEqual(fatfs.get_cluster_value(0), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(1), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(2), 'free_cluster')
                self.assertEqual(fatfs.get_cluster_value(3), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(4), 5)
                self.assertEqual(fatfs.get_cluster_value(5), 6)
                self.assertEqual(fatfs.get_cluster_value(6), 7)
                self.assertEqual(fatfs.get_cluster_value(7), 'last_cluster')
        with self.subTest(i="FAT16"):
            with open(IMAGE_PATHS[1], 'rb') as img_stream:
                fatfs = fat_16.FAT16(img_stream)
                self.assertEqual(fatfs.get_cluster_value(0), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(1), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(2), 'free_cluster')
                self.assertEqual(fatfs.get_cluster_value(3), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(4), 5)
                self.assertEqual(fatfs.get_cluster_value(5), 6)
                self.assertEqual(fatfs.get_cluster_value(6), 7)
                self.assertEqual(fatfs.get_cluster_value(7), 'last_cluster')
        with self.subTest(i="FAT32"):
            with open(IMAGE_PATHS[2], 'rb') as img_stream:
                fatfs = fat_32.FAT32(img_stream)
                self.assertEqual(fatfs.get_cluster_value(0), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(1), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(2), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(3), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(4), 5)
                self.assertEqual(fatfs.get_cluster_value(5), 'last_cluster')
                self.assertEqual(fatfs.get_cluster_value(6), 7)
                self.assertEqual(fatfs.get_cluster_value(7), 'last_cluster')

    def test_get_free_cluster(self):
        with self.subTest(i="FAT12"):
            with open(IMAGE_PATHS[0], 'rb') as img_stream:
                fatfs = fat_12.FAT12(img_stream)
                result = fatfs.get_free_cluster()
                self.assertEqual(result, 17)
        with self.subTest(i="FAT16"):
            with open(IMAGE_PATHS[1], 'rb') as img_stream:
                fatfs = fat_16.FAT16(img_stream)
                result = fatfs.get_free_cluster()
                self.assertEqual(result, 17)
        with self.subTest(i="FAT32"):
            with open(IMAGE_PATHS[2], 'rb') as img_stream:
                fatfs = fat_32.FAT32(img_stream)
                result = fatfs.get_free_cluster()
                self.assertEqual(result, 13)

    def test_follow_cluster(self):
        with self.subTest(i="FAT12"):
            with open(IMAGE_PATHS[0], 'rb') as img_stream:
                fatfs = fat_12.FAT12(img_stream)
                result = fatfs.follow_cluster(4)
                self.assertEqual(result, [4, 5, 6, 7])
                with self.assertRaises(Exception):
                    result = fatfs.follow_cluster(50)
        with self.subTest(i="FAT16"):
            with open(IMAGE_PATHS[1], 'rb') as img_stream:
                fatfs = fat_16.FAT16(img_stream)
                result = fatfs.follow_cluster(4)
                self.assertEqual(result, [4, 5, 6, 7])
                with self.assertRaises(Exception):
                    result = fatfs.follow_cluster(50)
        with self.subTest(i="FAT32"):
            with open(IMAGE_PATHS[2], 'rb') as img_stream:
                fatfs = fat_32.FAT32(img_stream)
                result = fatfs.follow_cluster(4)
                self.assertEqual(result, [4, 5])
                with self.assertRaises(Exception):
                    result = fatfs.follow_cluster(50)

    def test_cluster_to_stream(self):
        with self.subTest(i="FAT12"):
            with open(IMAGE_PATHS[0], 'rb') as img_stream:
                fatfs = fat_12.FAT12(img_stream)
                with io.BytesIO() as mem:
                    # here we take the last cluster of 'long_file.txt'
                    # as it contains chars and empty space
                    fatfs.cluster_to_stream(7, mem)
                    mem.seek(0)
                    result = mem.read()
                    expected = b'1'*1856 + b'\n' + b'\x00'*190 + b'\x00'
                    self.assertEqual(result, expected)
        with self.subTest(i="FAT16"):
            with open(IMAGE_PATHS[1], 'rb') as img_stream:
                fatfs = fat_16.FAT16(img_stream)
                with io.BytesIO() as mem:
                    # here we take the last cluster of 'long_file.txt'
                    # as it contains chars and empty space
                    fatfs.cluster_to_stream(7, mem)
                    mem.seek(0)
                    result = mem.read()
                    expected = b'1'*1856 + b'\n' + b'\x00'*190 + b'\x00'
                    self.assertEqual(result, expected)
        with self.subTest(i="FAT32"):
            with open(IMAGE_PATHS[2], 'rb') as img_stream:
                fatfs = fat_32.FAT32(img_stream)
                result = fatfs.get_free_cluster()
                with io.BytesIO() as mem:
                    # here we take the last cluster of 'long_file.txt'
                    # as it contains chars and empty space
                    fatfs.cluster_to_stream(5, mem)
                    mem.seek(0)
                    result = mem.read()
                    expected = b'1'*3904 + b'\n' + b'\x00'*191
                    self.assertEqual(result, expected)

    def test_get_root_dir_entries(self):
        expected_entries = ['another',
                            'areallylongfilenamethatiwanttoreadcorrectly.txt',
                            'long_file.txt',
                            'no_free_slack.txt',
                            'onedirectory',
                            'testfile.txt',
                           ]
        with self.subTest(i="FAT12"):
            with open(IMAGE_PATHS[0], 'rb') as img_stream:
                fatfs = fat_12.FAT12(img_stream)
                counter = 0
                for _, lfn in fatfs.get_root_dir_entries():
                    if lfn != "":
                        self.assertEqual(lfn, expected_entries[counter])
                        counter += 1
        with self.subTest(i="FAT16"):
            with open(IMAGE_PATHS[1], 'rb') as img_stream:
                fatfs = fat_16.FAT16(img_stream)
                counter = 0
                for _, lfn in fatfs.get_root_dir_entries():
                    if lfn != "":
                        self.assertEqual(lfn, expected_entries[counter])
                        counter += 1
        with self.subTest(i="FAT32"):
            with open(IMAGE_PATHS[2], 'rb') as img_stream:
                fatfs = fat_32.FAT32(img_stream)
                counter = 0
                for _, lfn in fatfs.get_root_dir_entries():
                    if lfn != "":
                        self.assertEqual(lfn, expected_entries[counter])
                        counter += 1

    def test_write_fat_entry_fat12(self):
        with open(IMAGE_PATHS[0], 'rb+') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            # store current value to restore old state after test
            actual_value = fatfs.get_cluster_value(4)
            value_above = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(5)
            expected = 19
            # Test writing even cluster number
            fatfs.write_fat_entry(4, expected)
            result = fatfs.get_cluster_value(4)
            self.assertEqual(result, expected)
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(3)
            value_below_now = fatfs.get_cluster_value(5)
            self.assertEqual(value_above_now, value_above)
            self.assertEqual(value_below_now, value_below)
            # restore old status. hopfully this works
            fatfs.write_fat_entry(4, actual_value)
            # Test writing odd cluster number
            value_above = fatfs.get_cluster_value(2)
            value_below = fatfs.get_cluster_value(4)
            fatfs.write_fat_entry(3, expected)
            result = fatfs.get_cluster_value(3)
            self.assertEqual(result, expected)
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(2)
            value_below_now = fatfs.get_cluster_value(4)
            self.assertEqual(value_above_now, value_above)
            self.assertEqual(value_below_now, value_below)
            # restore old status. hopfully this works
            fatfs.write_fat_entry(3, actual_value)
            with self.assertRaises(AttributeError):
                fatfs.write_fat_entry(-1, 15)
            with self.assertRaises(AttributeError):
                fatfs.write_fat_entry(fatfs.entries_per_fat, 15)
            with self.assertRaises(AssertionError):
                fatfs.write_fat_entry(2, 0)
            with self.assertRaises(AssertionError):
                fatfs.write_fat_entry(2, 4087)

    def test_write_fat_entry_fat16(self):
        with open(IMAGE_PATHS[1], 'rb+') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            actual_value = fatfs.get_cluster_value(4)
            value_above = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(5)
            expected = 19
            fatfs.write_fat_entry(4, expected)
            result = fatfs.get_cluster_value(4)
            self.assertEqual(result, expected)
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(3)
            value_below_now = fatfs.get_cluster_value(5)
            self.assertEqual(value_above_now, value_above)
            self.assertEqual(value_below_now, value_below)
            fatfs.write_fat_entry(4, actual_value)
            with self.assertRaises(AttributeError):
                fatfs.write_fat_entry(-1, 15)
            with self.assertRaises(AttributeError):
                fatfs.write_fat_entry(fatfs.entries_per_fat, 15)
            with self.assertRaises(AssertionError):
                fatfs.write_fat_entry(2, 0)
            with self.assertRaises(AssertionError):
                fatfs.write_fat_entry(2, 0xfff7)

    def test_write_fat_entry_fat32(self):
        with open(IMAGE_PATHS[2], 'rb+') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            actual_value = fatfs.get_cluster_value(4)
            value_above = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(5)
            expected = 19
            fatfs.write_fat_entry(4, expected)
            result = fatfs.get_cluster_value(4)
            self.assertEqual(result, expected)
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(3)
            value_below_now = fatfs.get_cluster_value(5)
            self.assertEqual(value_above_now, value_above)
            self.assertEqual(value_below_now, value_below)
            fatfs.write_fat_entry(4, actual_value)
            with self.assertRaises(AttributeError):
                fatfs.write_fat_entry(-1, 15)
            with self.assertRaises(AttributeError):
                fatfs.write_fat_entry(fatfs.entries_per_fat, 15)
            with self.assertRaises(AssertionError):
                fatfs.write_fat_entry(2, 0)
            with self.assertRaises(AssertionError):
                fatfs.write_fat_entry(2, 0xffffff7)

    def test_find_file(self):
        for img_path in IMAGE_PATHS:
            with open(img_path, 'rb') as img_stream:
                # create FAT object
                fatfs = create_fat(img_stream)
                result = fatfs.find_file("long_file.txt")
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
                # Test finding a non existing file
                with self.assertRaises(Exception):
                    fatfs.find_file("i-dont-exist")

    def test_write_free_cluster(self):
        """
        test if writing free cluster count into FAT32 FS INFO sector works
        correctly
        """
        img_path = IMAGE_PATHS[2]
        with open(img_path, 'rb+') as img_stream:
            # create FAT32 object
            fatfs = create_fat(img_stream)
            orig_free_clusters = fatfs.pre.free_data_cluster_count
            # write new free cluster count
            new_value = 1337
            fatfs.write_free_clusters(new_value)
            # test if new free cluster count was wriiten to disk
            img_stream.seek(0)
            fatfs2 = create_fat(img_stream)
            self.assertEqual(fatfs2.pre.free_data_cluster_count, new_value)
            # test if new free cluster count was correctly reread
            self.assertEqual(fatfs.pre.free_data_cluster_count, new_value)
            # restore old free cluster count
            fatfs.write_free_clusters(orig_free_clusters)

    def test_write_last_allocated(self):
        """
        test if writing last_allocated_cluster into FAT32 FS INFO sector works
        correctly
        """
        img_path = IMAGE_PATHS[2]
        with open(img_path, 'rb+') as img_stream:
            # create FAT32 object
            fatfs = create_fat(img_stream)
            orig_alloc_cluster = fatfs.pre.last_allocated_data_cluster
            # write new last_allocated_cluster
            new_value = 1337
            fatfs.write_last_allocated(new_value)
            # test if new last_allocated_cluster value was wriiten to disk
            img_stream.seek(0)
            fatfs2 = create_fat(img_stream)
            self.assertEqual(fatfs2.pre.last_allocated_data_cluster, new_value)
            # test if new last_allocated_cluster value was correctly reread
            self.assertEqual(fatfs.pre.last_allocated_data_cluster, new_value)
            # restore old last_allocated_cluster count
            fatfs.write_last_allocated(orig_alloc_cluster)


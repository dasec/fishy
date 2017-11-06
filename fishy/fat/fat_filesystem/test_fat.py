from . import fat
from . import fat_detector
import os
import io
import shutil
import subprocess
import tempfile
import unittest


this_dir = os.path.dirname(os.path.abspath(__file__))
utilsdir = os.path.join(this_dir, os.pardir, os.pardir, os.pardir, 'utils')
imagedir = tempfile.mkdtemp()


image_paths = [
                os.path.join(imagedir, 'testfs-fat12.dd'),
                os.path.join(imagedir, 'testfs-fat16.dd'),
                os.path.join(imagedir, 'testfs-fat32.dd'),
              ]

def setUpModule():
    # create test filesystems
    cmd = os.path.join(utilsdir, "create_testfs.sh") + " " + utilsdir \
          + " " + imagedir + " " + "fat" + " true"
    subprocess.call(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, shell=True)

def tearDownModule():
    # remove created filesystem images
    shutil.rmtree(imagedir)

class TestFatDetector(unittest.TestCase):

    def test_get_filesystem(self):
        with open(image_paths[0], 'rb') as f:
            result = fat_detector.get_filesystem_type(f)
            self.assertEqual(result, 'FAT12')
        with open(image_paths[1], 'rb') as f:
            result = fat_detector.get_filesystem_type(f)
            self.assertEqual(result, 'FAT16')
        with open(image_paths[2], 'rb') as f:
            result = fat_detector.get_filesystem_type(f)
            self.assertEqual(result, 'FAT32')

    def test_is_fat(self):
        with open(image_paths[0], 'rb') as f:
            result = fat_detector.is_fat(f)
            self.assertEqual(result, True)
        with open(image_paths[1], 'rb') as f:
            result = fat_detector.is_fat(f)
            self.assertEqual(result, True)
        with open(image_paths[2], 'rb') as f:
            result = fat_detector.is_fat(f)
            self.assertEqual(result, True)

class TestFatImplementation(unittest.TestCase):

    def test_parse_predata_region(self):
        with self.subTest(i="FAT12"):
            with open(image_paths[0], 'rb') as f:
                fs = fat.FAT12(f)
                self.assertEqual(fs.pre.sector_size, 512)
                self.assertEqual(fs.pre.sectors_per_cluster, 4)
                self.assertEqual(fs.pre.reserved_sector_count, 1)
                self.assertEqual(fs.pre.fat_count, 2)
                self.assertEqual(fs.pre.rootdir_entry_count, 512)
                self.assertEqual(fs.pre.sectors_per_fat, 2)
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb') as f:
                fs = fat.FAT16(f)
                self.assertEqual(fs.pre.sector_size, 512)
                self.assertEqual(fs.pre.sectors_per_cluster, 4)
                self.assertEqual(fs.pre.reserved_sector_count, 4)
                self.assertEqual(fs.pre.fat_count, 2)
                self.assertEqual(fs.pre.rootdir_entry_count, 512)
                self.assertEqual(fs.pre.sectors_per_fat, 52)
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb') as f:
                fs = fat.FAT32(f)
                self.assertEqual(fs.pre.sector_size, 512)
                self.assertEqual(fs.pre.sectors_per_cluster, 8)
                self.assertEqual(fs.pre.reserved_sector_count, 32)
                self.assertEqual(fs.pre.fat_count, 2)
                self.assertEqual(fs.pre.sectors_per_fat, 544)
                self.assertEqual(fs.pre.free_data_cluster_count, 68599)
                self.assertEqual(fs.pre.last_allocated_data_cluster, 12)
                self.assertEqual(fs.pre.flags.active_fat, 0)
                self.assertEqual(fs.pre.flags.mirrored, False)
                self.assertEqual(fs.pre.fsinfo_sector, 1)
                self.assertEqual(fs.pre.bootsector_copy_sector, 6)

    def test_get_cluster_value(self):
        with self.subTest(i="FAT12"):
            with open(image_paths[0], 'rb') as f:
                fs = fat.FAT12(f)
                self.assertEqual(fs._get_cluster_value(0), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(1), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(2), 'free_cluster')
                self.assertEqual(fs._get_cluster_value(3), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(4), 5)
                self.assertEqual(fs._get_cluster_value(5), 6)
                self.assertEqual(fs._get_cluster_value(6), 7)
                self.assertEqual(fs._get_cluster_value(7), 'last_cluster')
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb') as f:
                fs = fat.FAT16(f)
                self.assertEqual(fs._get_cluster_value(0), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(1), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(2), 'free_cluster')
                self.assertEqual(fs._get_cluster_value(3), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(4), 5)
                self.assertEqual(fs._get_cluster_value(5), 6)
                self.assertEqual(fs._get_cluster_value(6), 7)
                self.assertEqual(fs._get_cluster_value(7), 'last_cluster')
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb') as f:
                fs = fat.FAT32(f)
                self.assertEqual(fs._get_cluster_value(0), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(1), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(2), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(3), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(4), 5)
                self.assertEqual(fs._get_cluster_value(5), 'last_cluster')
                self.assertEqual(fs._get_cluster_value(6), 7)
                self.assertEqual(fs._get_cluster_value(7), 'last_cluster')

    def test_get_free_cluster(self):
        with self.subTest(i="FAT12"):
            with open(image_paths[0], 'rb') as f:
                fs = fat.FAT12(f)
                result = fs.get_free_cluster()
                self.assertEqual(result, 17)
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb') as f:
                fs = fat.FAT16(f)
                result = fs.get_free_cluster()
                self.assertEqual(result, 17)
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb') as f:
                fs = fat.FAT32(f)
                result = fs.get_free_cluster()
                self.assertEqual(result, 13)

    def test_follow_cluster(self):
        with self.subTest(i="FAT12"):
            with open(image_paths[0], 'rb') as f:
                fs = fat.FAT12(f)
                result = fs.follow_cluster(4)
                self.assertEqual(result, [4, 5, 6, 7])
                with self.assertRaises(Exception):
                    result = fs.follow_cluster(50)
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb') as f:
                fs = fat.FAT16(f)
                result = fs.follow_cluster(4)
                self.assertEqual(result, [4, 5, 6, 7])
                with self.assertRaises(Exception):
                    result = fs.follow_cluster(50)
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb') as f:
                fs = fat.FAT32(f)
                result = fs.follow_cluster(4)
                self.assertEqual(result, [4, 5])
                with self.assertRaises(Exception):
                    result = fs.follow_cluster(50)

    def test_cluster_to_stream(self):
        with self.subTest(i="FAT12"):
            with open(image_paths[0], 'rb') as f:
                fs = fat.FAT12(f)
                with io.BytesIO() as mem:
                    # here we take the last cluster of 'long_file.txt'
                    # as it contains chars and empty space
                    fs.cluster_to_stream(7, mem)
                    mem.seek(0)
                    result = mem.read()
                    expected = b'1'*1856 + b'\n' + b'\x00'*190 + b'\x00'
                    self.assertEqual(result, expected)
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb') as f:
                fs = fat.FAT16(f)
                with io.BytesIO() as mem:
                    # here we take the last cluster of 'long_file.txt'
                    # as it contains chars and empty space
                    fs.cluster_to_stream(7, mem)
                    mem.seek(0)
                    result = mem.read()
                    expected = b'1'*1856 + b'\n' + b'\x00'*190 + b'\x00'
                    self.assertEqual(result, expected)
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb') as f:
                fs = fat.FAT32(f)
                result = fs.get_free_cluster()
                with io.BytesIO() as mem:
                    # here we take the last cluster of 'long_file.txt'
                    # as it contains chars and empty space
                    fs.cluster_to_stream(5, mem)
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
            with open(image_paths[0], 'rb') as f:
                fs = fat.FAT12(f)
                counter = 0
                for e, lfn in fs.get_root_dir_entries():
                    if lfn != "":
                        self.assertEqual(lfn, expected_entries[counter])
                        counter += 1
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb') as f:
                fs = fat.FAT16(f)
                counter = 0
                for e, lfn in fs.get_root_dir_entries():
                    if lfn != "":
                        self.assertEqual(lfn, expected_entries[counter])
                        counter += 1
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb') as f:
                fs = fat.FAT16(f)
                counter = 0
                for e, lfn in fs.get_root_dir_entries():
                    if lfn != "":
                        self.assertEqual(lfn, expected_entries[counter])
                        counter += 1

    def test_write_fat_entry(self):
        with self.subTest(i="FAT12"):
            with open(image_paths[0], 'rb+') as f:
                fs = fat.FAT12(f)
                actual_value = fs._get_cluster_value(4)
                expected = 19
                fs.write_fat_entry(4, expected)
                result = fs._get_cluster_value(4)
                self.assertEqual(result, expected)
                fs.write_fat_entry(4,actual_value)
                with self.assertRaises(AttributeError):
                    fs.write_fat_entry(-1, 15)
                with self.assertRaises(AttributeError):
                    fs.write_fat_entry(fs.entries_per_fat, 15)
                with self.assertRaises(AssertionError):
                    fs.write_fat_entry(2, 0)
                with self.assertRaises(AssertionError):
                    fs.write_fat_entry(2, 4087)
        with self.subTest(i="FAT16"):
            with open(image_paths[1], 'rb+') as f:
                fs = fat.FAT16(f)
                actual_value = fs._get_cluster_value(4)
                expected = 19
                fs.write_fat_entry(4, expected)
                result = fs._get_cluster_value(4)
                self.assertEqual(result, expected)
                fs.write_fat_entry(4,actual_value)
                with self.assertRaises(AttributeError):
                    fs.write_fat_entry(-1, 15)
                with self.assertRaises(AttributeError):
                    fs.write_fat_entry(fs.entries_per_fat, 15)
                with self.assertRaises(AssertionError):
                    fs.write_fat_entry(2, 0)
                with self.assertRaises(AssertionError):
                    fs.write_fat_entry(2, 0xfff7)
        with self.subTest(i="FAT32"):
            with open(image_paths[2], 'rb+') as f:
                fs = fat.FAT32(f)
                actual_value = fs._get_cluster_value(4)
                expected = 19
                fs.write_fat_entry(4, expected)
                result = fs._get_cluster_value(4)
                self.assertEqual(result, expected)
                fs.write_fat_entry(4,actual_value)
                with self.assertRaises(AttributeError):
                    fs.write_fat_entry(-1, 15)
                with self.assertRaises(AttributeError):
                    fs.write_fat_entry(fs.entries_per_fat, 15)
                with self.assertRaises(AssertionError):
                    fs.write_fat_entry(2, 0)
                with self.assertRaises(AssertionError):
                    fs.write_fat_entry(2, 0xffffff7)

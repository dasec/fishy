from .filesystem_detector import get_filesystem_type, UnsupportedFilesystemError
import os
import shutil
import subprocess
import tempfile
import unittest


this_dir = os.path.dirname(os.path.abspath(__file__))
utilsdir = os.path.join(this_dir, os.pardir, 'utils')
imagedir = tempfile.mkdtemp()


class TestFileSystemDetector(unittest.TestCase):

    fat_image_paths = [
                    os.path.join(imagedir, 'testfs-fat12.dd'),
                    os.path.join(imagedir, 'testfs-fat16.dd'),
                    os.path.join(imagedir, 'testfs-fat32.dd'),
                      ]
    ntfs_image_paths = [
                        os.path.join(imagedir, 'testfs-ntfs.dd'),
                       ]
    ext4_image_paths = [
                        os.path.join(imagedir, 'testfs-ext4.dd'),
                       ]

    @classmethod
    def setUpClass(cls):
        # regenerate test filesystems
        cmd = os.path.join(utilsdir, "create_testfs.sh") + " " + utilsdir \
              + " " + imagedir + " " + "all" + " true"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)

    @classmethod
    def tearDownClass(cls):
        # remove created filesystem images
        shutil.rmtree(imagedir)

    def test_fat_images(self):
        for img in TestFileSystemDetector.fat_image_paths:
            with self.subTest(i=img):
                with open(img, 'rb') as fs_stream:
                    result = get_filesystem_type(fs_stream)
                    self.assertEqual(result, 'FAT')

    def test_ntfs_images(self):
        for img in TestFileSystemDetector.ntfs_image_paths:
            with self.subTest(i=img):
                with open(img, 'rb') as fs_stream:
                    result = get_filesystem_type(fs_stream)
                    self.assertEqual(result, 'NTFS')

    def test_ext4_images(self):
        for img in TestFileSystemDetector.ext4_image_paths:
            with self.subTest(i=img):
                with open(img, 'rb') as fs_stream:
                    with self.assertRaises(UnsupportedFilesystemError):
                        get_filesystem_type(fs_stream)

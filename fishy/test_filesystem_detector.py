# pylint: disable=missing-docstring
import os
import shutil
import subprocess
import tempfile
import unittest
from .filesystem_detector import get_filesystem_type, UnsupportedFilesystemError


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UTILSDIR = os.path.join(THIS_DIR, os.pardir, 'utils')
IMAGEDIR = tempfile.mkdtemp()


class TestFileSystemDetector(unittest.TestCase):

    fat_image_paths = [
        os.path.join(IMAGEDIR, 'testfs-fat12-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat16-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat32-stable1.dd'),
        ]
    ntfs_image_paths = [
        os.path.join(IMAGEDIR, 'testfs-ntfs-stable1.dd'),
        ]
    ext4_image_paths = [
        os.path.join(IMAGEDIR, 'testfs-ext4-stable1.dd'),
        ]

    @classmethod
    def setUpClass(cls):
        # regenerate test filesystems
        cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
              + " -d " + IMAGEDIR + " -t " + "all" + " -u -s '-stable1'"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        # stderr=subprocess.PIPE,
                        shell=True)

    @classmethod
    def tearDownClass(cls):
        # remove created filesystem images
        shutil.rmtree(IMAGEDIR)

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

"""
this file contains test fixtures which can be used by unittests
"""
import os
import tempfile
import subprocess
import shutil
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UTILSDIR = os.path.join(THIS_DIR, os.pardir, 'utils')



@pytest.fixture(scope="module")
def testfs_fat_stable1():
    """
    creates FAT filesystem test images
    :return: list of strings, containing paths to fat test images
    """
    image_dir = tempfile.mkdtemp()

    image_paths = [
        os.path.join(image_dir, 'testfs-fat12-stable1.dd'),
        os.path.join(image_dir, 'testfs-fat16-stable1.dd'),
        os.path.join(image_dir, 'testfs-fat32-stable1.dd'),
        ]

    # create test filesystems
    cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
          + " -d " + image_dir + " -t " + "fat" + " -u -s '-stable1'"
    subprocess.call(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

    yield image_paths

    # remove created filesystem images
    shutil.rmtree(image_dir)

@pytest.fixture(scope="module")
def testfs_ntfs_stable1():
    """
    creates NFTS filesystem test images
    :return: list of strings, containing paths to ntfs test images
    """
    image_dir = tempfile.mkdtemp()

    image_paths = [
        os.path.join(image_dir, 'testfs-ntfs-stable1.dd'),
        ]

    # create test filesystems
    cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
          + " -d " + image_dir + " -t " + "ntfs" + " -u -s '-stable1'"
    subprocess.call(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

    yield image_paths

    # remove created filesystem images
    shutil.rmtree(image_dir)

@pytest.fixture(scope="module")
def testfs_ntfs_stable2():
    """
    creates NFTS filesystem test images
    :return: list of strings, containing paths to ntfs test images
    """
    image_dir = tempfile.mkdtemp()

    image_paths = [
        os.path.join(image_dir, 'testfs-ntfs-stable2.dd'),
        ]

    # create test filesystems
    cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
          + " -d " + image_dir + " -t " + "ntfs" + " -u -s '-stable2'"
    subprocess.call(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

    yield image_paths

    # remove created filesystem images
    shutil.rmtree(image_dir)

@pytest.fixture(scope="module")
def testfs_ext4_stable1():
    """
    creates ext4 filesystem test images
    :return: list of strings, containing paths to fat test images
    """
    image_dir = tempfile.mkdtemp()

    image_paths = [
        os.path.join(image_dir, 'testfs-ext4-stable1.dd'),
        ]

    # create test filesystems
    cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
          + " -d " + image_dir + " -t " + "ext4" + " -u -s '-stable1'"
    subprocess.call(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

    yield image_paths

    # remove created filesystem images
    shutil.rmtree(image_dir)

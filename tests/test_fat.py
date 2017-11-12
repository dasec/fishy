# pylint: disable=missing-docstring
"""
This file contains tests for all three different fat implementations under
fishy.fat.filesystem.fat_*
"""
import io
import pytest
from fishy.fat.fat_filesystem.fat_wrapper import create_fat
from fishy.fat.fat_filesystem import fat_12
from fishy.fat.fat_filesystem import fat_16
from fishy.fat.fat_filesystem import fat_32


class TestPreDataRegion(object):
    def test_parse_predata_fat12(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            assert fatfs.pre.sector_size == 512
            assert fatfs.pre.sectors_per_cluster == 4
            assert fatfs.pre.reserved_sector_count == 1
            assert fatfs.pre.fat_count == 2
            assert fatfs.pre.rootdir_entry_count == 512
            assert fatfs.pre.sectors_per_fat == 2

    def test_parse_predata_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            assert fatfs.pre.sector_size == 512
            assert fatfs.pre.sectors_per_cluster == 4
            assert fatfs.pre.reserved_sector_count == 4
            assert fatfs.pre.fat_count == 2
            assert fatfs.pre.rootdir_entry_count == 512
            assert fatfs.pre.sectors_per_fat == 52

    def test_parse_predata_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            assert fatfs.pre.sector_size == 512
            assert fatfs.pre.sectors_per_cluster == 8
            assert fatfs.pre.reserved_sector_count == 32
            assert fatfs.pre.fat_count == 2
            assert fatfs.pre.sectors_per_fat == 544
            assert fatfs.pre.free_data_cluster_count == 68599
            assert fatfs.pre.last_allocated_data_cluster == 12
            assert fatfs.pre.flags.active_fat == 0
            assert not fatfs.pre.flags.mirrored
            assert fatfs.pre.fsinfo_sector == 1
            assert fatfs.pre.bootsector_copy_sector == 6

class TestGetClusterValue(object):
    def test_get_cluster_value_fat12(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            assert fatfs.get_cluster_value(0) == 'last_cluster'
            assert fatfs.get_cluster_value(1) == 'last_cluster'
            assert fatfs.get_cluster_value(2) == 'free_cluster'
            assert fatfs.get_cluster_value(3) == 'last_cluster'
            assert fatfs.get_cluster_value(4) == 5
            assert fatfs.get_cluster_value(5) == 6
            assert fatfs.get_cluster_value(6) == 7
            assert fatfs.get_cluster_value(7) == 'last_cluster'

    def test_get_cluster_value_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            assert fatfs.get_cluster_value(0) == 'last_cluster'
            assert fatfs.get_cluster_value(1) == 'last_cluster'
            assert fatfs.get_cluster_value(2) == 'free_cluster'
            assert fatfs.get_cluster_value(3) == 'last_cluster'
            assert fatfs.get_cluster_value(4) == 5
            assert fatfs.get_cluster_value(5) == 6
            assert fatfs.get_cluster_value(6) == 7
            assert fatfs.get_cluster_value(7) == 'last_cluster'

    def test_get_cluster_value_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            assert fatfs.get_cluster_value(0) == 'last_cluster'
            assert fatfs.get_cluster_value(1) == 'last_cluster'
            assert fatfs.get_cluster_value(2) == 'last_cluster'
            assert fatfs.get_cluster_value(3) == 'last_cluster'
            assert fatfs.get_cluster_value(4) == 5
            assert fatfs.get_cluster_value(5) == 'last_cluster'
            assert fatfs.get_cluster_value(6) == 7
            assert fatfs.get_cluster_value(7) == 'last_cluster'

class TestGetFreeCluster(object):
    def test_get_free_cluster_fat12(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            result = fatfs.get_free_cluster()
            assert result == 17

    def test_get_free_cluster_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            result = fatfs.get_free_cluster()
            assert result == 17

    def test_get_free_cluster_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            result = fatfs.get_free_cluster()
            assert result == 13

class TestFollowCluster(object):
    def test_follow_cluster_fat12(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            result = fatfs.follow_cluster(4)
            assert result == [4, 5, 6, 7]
            with pytest.raises(Exception):
                result = fatfs.follow_cluster(50)

    def test_follow_cluster_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            result = fatfs.follow_cluster(4)
            assert result == [4, 5, 6, 7]
            with pytest.raises(Exception):
                result = fatfs.follow_cluster(50)

    def test_follow_cluster_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            result = fatfs.follow_cluster(4)
            assert result == [4, 5]
            with pytest.raises(Exception):
                result = fatfs.follow_cluster(50)

class TestClusterToStream(object):
    def test_cluster_to_stream_fat12(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            with io.BytesIO() as mem:
                # here we take the last cluster of 'long_file.txt'
                # as it contains chars and empty space
                fatfs.cluster_to_stream(7, mem)
                mem.seek(0)
                result = mem.read()
                expected = b'1'*1856 + b'\n' + b'\x00'*190 + b'\x00'
                assert result == expected

    def test_cluster_to_stream_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            with io.BytesIO() as mem:
                # here we take the last cluster of 'long_file.txt'
                # as it contains chars and empty space
                fatfs.cluster_to_stream(7, mem)
                mem.seek(0)
                result = mem.read()
                expected = b'1'*1856 + b'\n' + b'\x00'*190 + b'\x00'
                assert result == expected

    def test_cluster_to_stream_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            result = fatfs.get_free_cluster()
            with io.BytesIO() as mem:
                # here we take the last cluster of 'long_file.txt'
                # as it contains chars and empty space
                fatfs.cluster_to_stream(5, mem)
                mem.seek(0)
                result = mem.read()
                expected = b'1'*3904 + b'\n' + b'\x00'*191
                assert result == expected


class TestGetRootDirEntries(object):
    expected_entries = ['another',
                        'areallylongfilenamethatiwanttoreadcorrectly.txt',
                        'long_file.txt',
                        'no_free_slack.txt',
                        'onedirectory',
                        'testfile.txt',
                        ]

    def test_get_root_dir_entries_fat12(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            counter = 0
            for _, lfn in fatfs.get_root_dir_entries():
                if lfn != "":
                    assert lfn == self.expected_entries[counter]
                    counter += 1

    def test_get_root_dir_entries_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            counter = 0
            for _, lfn in fatfs.get_root_dir_entries():
                if lfn != "":
                    assert lfn == self.expected_entries[counter]
                    counter += 1

    def test_get_root_dir_entries_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            counter = 0
            for _, lfn in fatfs.get_root_dir_entries():
                if lfn != "":
                    assert lfn == self.expected_entries[counter]
                    counter += 1


class TestWriteFatEntry_FAT12(object):
    def test_write_fat_entry_fat12_even(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb+') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            # store current value to restore old state after test
            actual_value = fatfs.get_cluster_value(4)
            value_above = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(5)
            expected = 19
            # Test writing even cluster number
            fatfs.write_fat_entry(4, expected)
            result = fatfs.get_cluster_value(4)
            assert result == expected
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(3)
            value_below_now = fatfs.get_cluster_value(5)
            assert value_above_now == value_above
            assert value_below_now == value_below
            # restore old status. hopfully this works
            fatfs.write_fat_entry(4, actual_value)

    def test_write_fat_entry_fat12_off(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb+') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            # Test writing odd cluster number
            value_above = fatfs.get_cluster_value(2)
            actual_value = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(4)
            expected = 19
            fatfs.write_fat_entry(3, expected)
            result = fatfs.get_cluster_value(3)
            assert result == expected
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(2)
            value_below_now = fatfs.get_cluster_value(4)
            assert value_above_now == value_above
            assert value_below_now == value_below
            # restore old status. hopfully this works
            fatfs.write_fat_entry(3, actual_value)

    def test_write_exceptions(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[0], 'rb+') as img_stream:
            fatfs = fat_12.FAT12(img_stream)
            with pytest.raises(AttributeError):
                fatfs.write_fat_entry(-1, 15)
            with pytest.raises(AttributeError):
                fatfs.write_fat_entry(fatfs.entries_per_fat, 15)
            with pytest.raises(AssertionError):
                fatfs.write_fat_entry(2, 0)
            with pytest.raises(AssertionError):
                fatfs.write_fat_entry(2, 4087)


class TestWriteFatEntry_FAT16(object):
    def test_write_fat_entry_fat16(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb+') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            actual_value = fatfs.get_cluster_value(4)
            value_above = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(5)
            expected = 19
            fatfs.write_fat_entry(4, expected)
            result = fatfs.get_cluster_value(4)
            assert result == expected
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(3)
            value_below_now = fatfs.get_cluster_value(5)
            assert value_above_now == value_above
            assert value_below_now == value_below
            fatfs.write_fat_entry(4, actual_value)

    def test_write_exceptions(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[1], 'rb+') as img_stream:
            fatfs = fat_16.FAT16(img_stream)
            with pytest.raises(AttributeError):
                fatfs.write_fat_entry(-1, 15)
            with pytest.raises(AttributeError):
                fatfs.write_fat_entry(fatfs.entries_per_fat, 15)
            with pytest.raises(AssertionError):
                fatfs.write_fat_entry(2, 0)
            with pytest.raises(AssertionError):
                fatfs.write_fat_entry(2, 0xfff7)

class TestWriteFatEntry_FAT32(object):
    def test_write_fat_entry_fat32(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb+') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            actual_value = fatfs.get_cluster_value(4)
            value_above = fatfs.get_cluster_value(3)
            value_below = fatfs.get_cluster_value(5)
            expected = 19
            fatfs.write_fat_entry(4, expected)
            result = fatfs.get_cluster_value(4)
            assert result == expected
            # Test that we didn't damage cluster enties beside our own
            value_above_now = fatfs.get_cluster_value(3)
            value_below_now = fatfs.get_cluster_value(5)
            assert value_above_now == value_above
            assert value_below_now == value_below
            fatfs.write_fat_entry(4, actual_value)

    def test_write_exceptions(self, testfs_fat_stable1):
        with open(testfs_fat_stable1[2], 'rb+') as img_stream:
            fatfs = fat_32.FAT32(img_stream)
            with pytest.raises(AttributeError):
                fatfs.write_fat_entry(-1, 15)
            with pytest.raises(AttributeError):
                fatfs.write_fat_entry(fatfs.entries_per_fat, 15)
            with pytest.raises(AssertionError):
                fatfs.write_fat_entry(2, 0)
            with pytest.raises(AssertionError):
                fatfs.write_fat_entry(2, 0xffffff7)

class TestFindFile(object):
    def test_find_file(self, testfs_fat_stable1):
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb') as img_stream:
                # create FAT object
                fatfs = create_fat(img_stream)
                result = fatfs.find_file("long_file.txt")
                # check for file attibutes
                assert result.name == b'LONG_F~1'
                assert result.extension == b'TXT'
                assert not result.attributes.unused
                assert not result.attributes.device
                assert result.attributes.archive
                assert not result.attributes.subDirectory
                assert not result.attributes.volumeLabel
                assert not result.attributes.system
                assert not result.attributes.hidden
                assert not result.attributes.readonly
                assert result.fileSize == 8001

    def test_find_non_existing(self, testfs_fat_stable1):
        # Test finding a non existing file
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb') as img_stream:
                # create FAT object
                fatfs = create_fat(img_stream)
                with pytest.raises(Exception):
                    fatfs.find_file("i-dont-exist")

class TestWriteFreeCluster(object):
    def test_write_free_cluster(self, testfs_fat_stable1):
        """
        test if writing free cluster count into FAT32 FS INFO sector works
        correctly
        """
        img_path = testfs_fat_stable1[2]
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
            assert fatfs2.pre.free_data_cluster_count == new_value
            # test if new free cluster count was correctly reread
            assert fatfs.pre.free_data_cluster_count == new_value
            # restore old free cluster count
            fatfs.write_free_clusters(orig_free_clusters)

    def test_write_last_allocated(self, testfs_fat_stable1):
        """
        test if writing last_allocated_cluster into FAT32 FS INFO sector works
        correctly
        """
        img_path = testfs_fat_stable1[2]
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
            assert fatfs2.pre.last_allocated_data_cluster == new_value
            # test if new last_allocated_cluster value was correctly reread
            assert fatfs.pre.last_allocated_data_cluster == new_value
            # restore old last_allocated_cluster count
            fatfs.write_last_allocated(orig_alloc_cluster)

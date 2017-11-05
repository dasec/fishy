#!/bin/bash

# This script creates test images with FAT12,
# FAT16 and FAT32 filesystems and copies a test
# filestructure into them
#
# Requires: 
# * a directory called 'mount-fs' to mount the created filesystem
# * a directory called 'fs-files' including the filestructure
#   that will be copied into the created filesystem images
#
# Usage:
# ./create_testfs.sh [WORKINGDIR] [DESTDIR] [FSTYPE]
# [WORKINGDIR] - Directory where 'mount-fs' and 'fs-files' directories are
#                located. Defaults to current directory
# [DESTDIR]    - Directory where images will be stored. Defaults to
#                [WORKINGDIR].
# [FSTYPE]     - For which filesystem type the images will be created.
#                Valid options: fat, ntfs, ext4. Defaults to fat+ntfs
#                if this option is used, only one type can be chosen.

workingdir="$1"
fsdest="$2"
fstype="$3"
filestructure="fs-files"

if [ "$workingdir" == "" ]; then
	workingdir="$(pwd)"
fi

if [ ! $fsdest == "" ]; then
	if [ ! -d "$fsdest" ]; then
		echo "destination directory '$fsdest' is missing"
		exit 1
	fi
else
	fsdest="$workingdir"
fi


filestructure="$workingdir/$filestructure"

# check if required directories exist
if [ ! -d "$filestructure" ]; then
	echo "directory '$filestructure' is missing"
	exit 1
fi
if [ ! -d "$workingdir/mount-fs" ]; then
	echo "directory 'mount-fs' is missing"
	exit 1
fi

function copy_files {
	# this function copies the content of $filestructure
	# into a given filesystem image
	# usage copy_files [FILESYSTEM_IMAGE]
	sudo mount "$1" "$workingdir"/mount-fs
	sudo cp -r "$filestructure"/* "$workingdir"/mount-fs
	sudo umount "$workingdir"/mount-fs
}

function create_fat {
	# Create a 1MB FAT12 image
	dd if=/dev/zero of="$fsdest/testfs-fat12.dd" bs=512 count=2000
	mkfs.vfat -F 12 "$fsdest/testfs-fat12.dd"
	copy_files "$fsdest/testfs-fat12.dd"

	# Create a 26MB FAT16 image
	dd if=/dev/zero of="$fsdest/testfs-fat16.dd" bs=512 count=50000
	mkfs.vfat -F 16 "$fsdest/testfs-fat16.dd"
	copy_files "$fsdest/testfs-fat16.dd"

	# Create a 282MB FAT32 image
	dd if=/dev/zero of="$fsdest/testfs-fat32.dd" bs=512 count=550000
	mkfs.vfat -F 32 "$fsdest/testfs-fat32.dd"
	copy_files "$fsdest/testfs-fat32.dd"
}

function create_ntfs {
	# Create a 10MB NTFS image
	dd if=/dev/zero of="$fsdest/testfs-ntfs.dd" bs=512 count=20000
	mkfs.ntfs -F "$fsdest/testfs-ntfs.dd"
	copy_files "$fsdest/testfs-ntfs.dd"
}

function create_ext4 {
	# Create a 10MB NTFS image
	dd if=/dev/zero of="$fsdest/testfs-ext4.dd" bs=512 count=20000
	mkfs.ext4 "$fsdest/testfs-ext4.dd"
	copy_files "$fsdest/testfs-ext4.dd"
}


if [ "$fstype" == 'fat' ]; then
	create_fat
elif [ "$fstype" == 'ntfs' ]; then
	create_ntfs
elif [ "$fstype" == 'ext4' ]; then
	create_ext4
elif [ "$fstype" == 'all' ]; then
	create_fat
	create_ntfs
	create_ext4
elif [ "$fstype" == '' ]; then
	create_fat
	create_ntfs
else
	echo "unknown filesystem type: '$fstype'"
	exit 1
fi

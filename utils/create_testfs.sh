#!/bin/bash

# This script creates test images with FAT12,
# FAT16 and FAT32 filesystems and copies a test
# filestructure into them
#
# Requires: 
# * a directory called 'mount-fs' to mount the created filesystem
# * a directory called 'fs-files' including the filestructure
#   that will be copied into the created filesystem images

workingdir="$1"
useramdisk="$2"
filestructure="fs-files"

if [ "$workingdir" == "" ]; then
	workingdir="$(pwd)"
fi

if [ ! $useramdisk == "" ]; then
	if [ ! -d "$workingdir/ramdisk" ]; then
		echo "directory '$workingdir/ramdisk' is missing"
		exit 1
	fi
	fsdest="$workingdir/ramdisk"
	# only mount new tmpfs, if it is not already mounted
	if !  df | grep "$fsdest" > /dev/null; then
		echo mounting ramdisk...
		sudo mount -t tmpfs -o size=3g tmpfs "$workingdir/ramdisk"
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

# Create a 10MB NTFS image
dd if=/dev/zero of="$fsdest/testfs-ntfs.dd" bs=512 count=20000
mkfs.ntfs -F "$fsdest/testfs-ntfs.dd"
copy_files "$fsdest/testfs-ntfs.dd"

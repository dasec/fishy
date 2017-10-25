#!/bin/bash

# This script creates test images with FAT12,
# FAT16 and FAT32 filesystems and copies a test
# filestructure into them
#
# Requires: 
# * a directory called 'mount-fs' to mount the created filesystem
# * a directory called 'fs-files' including the filestructure
#   that will be copied into the created filesystem images

filestructure="fs-files"

# check if required directories exist
if [ ! -d "$filestructure" ]; then
	echo "directory '$filestructure' is missing"
	exit 1
fi
if [ ! -d "mount-fs" ]; then
	echo "directory 'mount-fs' is missing"
	exit 1
fi

function copy_files {
	# this function copies the content of $filestructure
	# into a given filesystem image
	# usage copy_files [FILESYSTEM_IMAGE]
	sudo mount "$1" mount-fs
	sudo cp -r "$filestructure"/* mount-fs
	sudo umount mount-fs
}

# Create a 1MB FAT12 image
dd if=/dev/zero of=testfs-fat12.dd bs=512 count=2000
mkfs.vfat testfs-fat12.dd
copy_files testfs-fat12.dd

# Create a 512MB FAT16 image
dd if=/dev/zero of=testfs-fat16.dd bs=512 count=1000000
mkfs.vfat testfs-fat16.dd
copy_files testfs-fat16.dd

# Create a 2GB FAT32 image
dd if=/dev/zero of=testfs-fat32.dd bs=512 count=4000500
mkfs.vfat testfs-fat32.dd
copy_files testfs-fat16.dd

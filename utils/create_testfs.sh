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
# Usage: ./create_testfs.sh [-uh] [-w WORKINGDIR] [-d DEST] [-t FSTYPE]
#   -w WORKINGDIR          Directory where 'mount-fs' and 
#                          'fs-files' directories are located.
#                          Defaults to current directory
#   -d DEST                Directory where images will be stored.
#                          Defaults to [WORKINGDIR].
#   -t FSTYPE              For which filesystem type the images
#                          will be created. Valid options: fat,
#                          ntfs, ext4, all. Defaults to fat+ntfs
#   -u                     try to source .create_testfs.conf
#
# if a .create_mount exists in the directory the script is located, this file
# will be sourced. Thus it is possible to provide a path where prepared disk
# images can be copied from.
#
# To copy testfs images from an existing location instead of creating them,
# create a file called `.create_testfs.conf` in the directory of this script.
# there place the following line:
# copyfrom="/path/from/where/to/copy/the/testfs_images"

# workingdir="$1"
# fsdest="$2"
# fstype="$3"
# useconf="$4"
filestructure="fs-files"


# help usage information
function print_help {
	echo "Usage: $0 [-uh] [-w WORKINGDIR] [-d DEST] [-t FSTYPE]"
	echo "  -w WORKINGDIR          Directory where 'mount-fs' and "
	echo "                         'fs-files' directories are located."
	echo "                         Defaults to current directory"
	echo "  -d DEST                Directory where images will be stored."
	echo "                         Defaults to [WORKINGDIR]."
	echo "  -t FSTYPE              For which filesystem type the images"
	echo "                         will be created. Valid options: fat,"
	echo "                         ntfs, ext4, all. Defaults to fat+ntfs"
	echo "  -u                     try to source .create_testfs.conf"
}


# parse command line options
workingdir=  fsdest=  fstype=  useconf=  

while getopts w:d:t:uh opt; do
  case $opt in
  h)
      print_help
      exit 0
      ;;
  w)
      workingdir=$OPTARG
      ;;
  d)
      fsdest=$OPTARG
      ;;
  t)
      fstype=$OPTARG
      ;;
  u)
      useconf=1
      ;;
  esac
done

shift $((OPTIND - 1))


# Source configuration
copyfrom=""
if [ -f "$(dirname ${BASH_SOURCE})"/.create_testfs.conf ] && [ ! "$useconf" == "" ]; then
	source "$(dirname ${BASH_SOURCE})"/.create_testfs.conf
fi

# If working dir was not specified, use current directory
if [ "$workingdir" == "" ]; then
	workingdir="$(pwd)"
fi

# if DEST was given, test if it exists, otherwise default to $workingdir
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
	if [ ! "$copyfrom" == "" ]; then
		cp "$copyfrom/testfs-fat12.dd" "$fsdest"
		cp "$copyfrom/testfs-fat16.dd" "$fsdest"
		cp "$copyfrom/testfs-fat32.dd" "$fsdest"
	else
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
	fi
}

function create_ntfs {
	if [ ! "$copyfrom" == "" ]; then
		cp "$copyfrom/testfs-ntfs.dd" "$fsdest"
	else
		# Create a 10MB NTFS image
		dd if=/dev/zero of="$fsdest/testfs-ntfs.dd" bs=512 count=20000
		mkfs.ntfs -F "$fsdest/testfs-ntfs.dd"
		copy_files "$fsdest/testfs-ntfs.dd"
	fi
}

function create_ext4 {
	if [ ! "$copyfrom" == "" ]; then
		cp "$copyfrom/testfs-ext4.dd" "$fsdest"
	else
		# Create a 10MB NTFS image
		dd if=/dev/zero of="$fsdest/testfs-ext4.dd" bs=512 count=20000
		mkfs.ext4 "$fsdest/testfs-ext4.dd"
		copy_files "$fsdest/testfs-ext4.dd"
	fi
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

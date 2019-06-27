"""
Implementation of fishy's command line interface.
"""
import sys
import traceback
import argparse
import logging
import getpass
import typing as typ
from fishy.wrapper.bad_cluster import BadClusterWrapper
from fishy.wrapper.cluster_allocation import ClusterAllocation
from fishy.fat.fat_filesystem.fat_wrapper import create_fat
from fishy.fat.fat_filesystem.fattools import FATtools
from fishy.wrapper.file_slack import FileSlack
from fishy.metadata import Metadata
from fishy.wrapper.mft_slack import MftSlack
from fishy.wrapper.osd2 import OSD2
from fishy.wrapper.obso_faddr import FADDR
from fishy.wrapper.reserved_gdt_blocks import ReservedGDTBlocks
from fishy.wrapper.superblock_slack import SuperblockSlack
from fishy.wrapper.inode_padding import inodePadding
from fishy.wrapper.write_gen import write_gen
from fishy.wrapper.timestamp_hiding import timestampHiding
from fishy.wrapper.xfield_padding import xfieldPadding


LOGGER = logging.getLogger("cli")


def do_metadata(args: argparse.Namespace) -> None:
    """
    handles metadata subcommand execution
    :param args: argparse.Namespace
    """
    if args.password is False:
        meta = Metadata()
    else:
        print("Please enter password: ")
        pw = getpass.getpass()
        meta = Metadata(password=pw)
    meta.read(args.metadata)
    meta.info()


def do_fattools(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles fattools subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    fattool = FATtools(create_fat(device))
    if args.fat:
        fattool.list_fat()
    elif args.info:
        fattool.list_info()
    elif args.list is not None:
        fattool.list_directory(args.list)


def do_fileslack(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    hanles fileslack subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.info:
        slacker = FileSlack(device, Metadata(), args.dev)
        slacker.info(args.destination)
    if args.write:
        if args.password is False:
            slacker = FileSlack(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            slacker = FileSlack(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into fileslack
            slacker.write(sys.stdin.buffer, args.destination)
        else:
            # write from files into fileslack
            with open(args.file, 'rb') as fstream:
                slacker.write(fstream, args.destination, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            slacker.metadata.write(metadata_out)
    elif args.read:
        # read file slack of a single hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data in fileslack into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.read_into_file(args.outfile)
    elif args.clear:
        # clear fileslack
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.clear()


def do_mftslack(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    hanles mftslack subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.info:
        slacker = MftSlack(device, Metadata(), args.dev)
        slacker.info(args.offset, args.limit)
    if args.write:
        if args.password is False:
            slacker = MftSlack(device, Metadata(), args.dev, args.domirr)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            slacker = MftSlack(device, Metadata(password=pw), args.dev, args.domirr)
        if not args.file:
            # write from stdin into mftslack
            slacker.write(sys.stdin.buffer, offset=args.offset)
        else:
            # write from files into mftslack
            with open(args.file, 'rb') as fstream:
                slacker.write(fstream, args.file, args.offset)
        with open(args.metadata, 'wb+') as metadata_out:
            slacker.metadata.write(metadata_out)
    elif args.read:
        # read file slack of a single hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slacker = MftSlack(device, meta, args.dev)
            slacker.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data in fileslack into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slacker = MftSlack(device, meta, args.dev)
            slacker.read_into_file(args.outfile)
    elif args.clear:
        # clear fileslack
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slacker = MftSlack(device, meta, args.dev)
            slacker.clear()


def do_addcluster(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    hanles addcluster subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        if args.password is False:
            allocator = ClusterAllocation(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            allocator = ClusterAllocation(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into additional clusters
            allocator.write(sys.stdin.buffer, args.destination)
        else:
            # write from files into additional clusters
            with open(args.file, 'rb') as fstream:
                allocator.write(fstream, args.destination, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            allocator.metadata.write(metadata_out)
    elif args.read:
        # read file slack of a single hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            allocator = ClusterAllocation(device, meta, args.dev)
            allocator.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data from additional clusters into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            allocator = ClusterAllocation(device, meta, args.dev)
            allocator.read_into_file(args.outfile)
    elif args.clear:
        # clear additional clusters
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            allocator = ClusterAllocation(device, meta, args.dev)
            allocator.clear()

def do_badcluster(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    hanles badcluster subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        if args.password is False:
            allocator = BadClusterWrapper(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            allocator = BadClusterWrapper(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into bad clusters
            allocator.write(sys.stdin.buffer)
        else:
            # write from file into bad cluster
            with open(args.file, 'rb') as fstream:
                allocator.write(fstream,  args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            allocator.metadata.write(metadata_out)
    elif args.read:
        # read bad cluster to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            allocator = BadClusterWrapper(device, meta, args.dev)
            allocator.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data from bad cluster into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            allocator = BadClusterWrapper(device, meta, args.dev)
            allocator.read_into_file(args.outfile)
    elif args.clear:
        # clear bad cluster
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            allocator = BadClusterWrapper(device, meta, args.dev)
            allocator.clear()


def do_reserved_gdt_blocks(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles reserved_gdt_blocks subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        if args.password is False:
            reserve = ReservedGDTBlocks(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            reserve = ReservedGDTBlocks(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into reserved GDT blocks
            reserve.write(sys.stdin.buffer)
        else:
            # write from files into reserved GDT blocks
            with open(args.file, 'rb') as fstream:
                reserve.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            reserve.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.read_into_file(args.outfile)
    elif args.clear:
        # clear reserved GDT blocks
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.clear()
    elif args.info:
        # show info
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.info()


def do_superblock_slack(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles superblock_slack subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        if args.password is False:
            slack = SuperblockSlack(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            slack = SuperblockSlack(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into superblock slack
            slack.write(sys.stdin.buffer)
        else:
            # write from files into superblock slack
            with open(args.file, 'rb') as fstream:
                slack.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            slack.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.read_into_file(args.outfile)
    elif args.clear:
        # clear superblock slack
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.clear()
    elif args.info:
        # show info
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.info()


def do_osd2(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles osd2 subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        if args.password is False:
            osd2 = OSD2(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            osd2 = OSD2(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into osd2 fields
            osd2.write(sys.stdin.buffer)
        else:
            # write from files into osd2 fields
            with open(args.file, 'rb') as fstream:
                osd2.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            osd2.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.read_into_file(args.outfile)
    elif args.clear:
        # clear osd2 fields
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.clear()
    elif args.info:
        # show info
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.info()

def do_obso_faddr(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles obso_faddr subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        if args.password is False:
            faddr = FADDR(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            faddr = FADDR(device, Metadata(password=pw), args.dev)
        if not args.file:
            # write from stdin into faddr fields
            faddr.write(sys.stdin.buffer)
        else:
            # write from files into faddr fields
            with open(args.file, 'rb') as fstream:
                faddr.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            faddr.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            faddr = FADDR(device, meta, args.dev)
            faddr.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            faddr = FADDR(device, meta, args.dev)
            faddr.read_into_file(args.outfile)
    elif args.clear:
        # clear faddr fields
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            faddr = FADDR(device, meta, args.dev)
            faddr.clear()
    elif args.info:
        # show info
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            faddr = FADDR(device, meta, args.dev)
            faddr.info()
			
def do_inode_padding(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    
    if args.write:
        if args.password is False:
            ipad = inodePadding(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            ipad = inodePadding(device, Metadata(password=pw), args.dev)
        if not args.file:
            ipad.write(sys.stdin.buffer)
        else:
            with open(args.file, 'rb') as fstream:
                ipad.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            ipad.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            ipad = inodePadding(device, meta, args.dev)
            ipad.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            ipad = inodePadding(device, meta, args.dev)
            ipad.read_into_file(args.outfile)
    elif args.clear:
        # clear faddr fields
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            ipad = inodePadding(device, meta, args.dev)
            ipad.clear()

def do_write_gen(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    
    if args.write:
        if args.password is False:
            wgen = write_gen(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            wgen = write_gen(device, Metadata(password=pw), args.dev)
        if not args.file:
            wgen.write(sys.stdin.buffer)
        else:
            with open(args.file, 'rb') as fstream:
                wgen.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            wgen.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            wgen = write_gen(device, meta, args.dev)
            wgen.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password = pw)
            meta.read(metadata_file)
            wgen = write_gen(device, meta, args.dev)
            wgen.read_into_file(args.outfile)
    elif args.clear:
        # clear faddr fields
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            wgen = write_gen(device, meta, args.dev)
            wgen.clear()

def do_timestamp_hiding(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    
    if args.write:
        if args.password is False:
            timestamp = timestampHiding(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            timestamp = timestampHiding(device, Metadata(password=pw), args.dev)
        if not args.file:
            timestamp.write(sys.stdin.buffer)
        else:
            with open(args.file, 'rb') as fstream:
                timestamp.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            timestamp.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            timestamp = timestampHiding(device, meta, args.dev)
            timestamp.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            timestamp = timestampHiding(device, meta, args.dev)
            timestamp.read_into_file(args.outfile)
    elif args.clear:
        # clear faddr fields
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            timestamp = timestampHiding(device, meta, args.dev)
            timestamp.clear()

def do_xfield_padding(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    
    if args.write:
        if args.password is False:
            xfield = xfieldPadding(device, Metadata(), args.dev)
        else:
            print("Please enter password: ")
            pw = getpass.getpass()
            xfield = xfieldPadding(device, Metadata(password=pw), args.dev)
        if not args.file:
            xfield.write(sys.stdin.buffer)
        else:
            with open(args.file, 'rb') as fstream:
                xfield.write(fstream, args.file)
        with open(args.metadata, 'wb+') as metadata_out:
            xfield.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            xfield = xfieldPadding(device, meta, args.dev)
            xfield.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            xfield = xfieldPadding(device, meta, args.dev)
            xfield.read_into_file(args.outfile)
    elif args.clear:
        # clear faddr fields
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is False:
                meta = Metadata()
            else:
                print("Please enter password: ")
                pw = getpass.getpass()
                meta = Metadata(password=pw)
            meta.read(metadata_file)
            xfield = xfieldPadding(device, meta, args.dev)
            xfield.clear()

			
			
			
def build_parser() -> argparse.ArgumentParser:
    """
    Get the cli parser

    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description='Toolkit for filesystem based data hiding techniques.')
    # TODO: Maybe this option should be required for hiding technique
    #       subcommand but not for metadata.... needs more thoughs than I
    #       currently have
    parser.set_defaults(which='no_arguments')
    parser.add_argument('-d', '--device', dest='dev', required=False, help='Path to filesystem')
    parser.add_argument('-p', '--password', dest='password', action='store_true', required=False, help='Password for encryption of metadata')
    # TODO Maybe we should provide a more fine grained option to choose between different log levels
    parser.add_argument('--verbose', '-v', action='count', help="Increase verbosity. Use it multiple times to increase verbosity further.")
    subparsers = parser.add_subparsers(help='Hiding techniques sub-commands')

    # FAT Tools
    fatt = subparsers.add_parser('fattools', help='List statistics about FAT filesystem')
    fatt.set_defaults(which='fattools')
    fatt.add_argument('-l', '--ls', dest='list', type=int, metavar='CLUSTER_ID', help='List files under cluster id. Use 0 for root directory')
    fatt.add_argument('-f', '--fat', dest='fat', action='store_true', help='List content of FAT')
    fatt.add_argument('-i', '--info', dest='info', action='store_true', help='Show some information about the filesystem')

    # Metadata info
    metadata = subparsers.add_parser('metadata', help='list information about a metadata file')
    metadata.set_defaults(which='metadata')
    metadata.add_argument('-m', '--metadata', dest='metadata', type=argparse.FileType('rb'), help="filepath to metadata file")

    # FileSlack
    fileslack = subparsers.add_parser('fileslack', help='Operate on file slack')
    fileslack.set_defaults(which='fileslack')
    fileslack.add_argument('-t', '--target', dest='destination', action='append', required=False, help='absolute path to file or directory on filesystem, directories will be parsed recursively')
    fileslack.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    fileslack.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from slackspace to stdout')
    fileslack.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from slackspace to OUTFILE')
    fileslack.add_argument('-w', '--write', dest='write', action='store_true', help='write to slackspace')
    fileslack.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear slackspace')
    fileslack.add_argument('-i', '--info', dest='info', action='store_true', help='print file slack information of given files')
    fileslack.add_argument('file', metavar='FILE', nargs='?', help="File to write into slack space, if nothing provided, use stdin")

    # MftSlack
    mftslack = subparsers.add_parser('mftslack', help='Operate on mft slack')
    mftslack.set_defaults(which='mftslack')
    mftslack.add_argument('-s', '--seek', dest='offset', default=0, type=int, required=False, help='sector offset to the start of the first mft entry to be used when hiding data. To avoid overwriting data use the "Next position" provided by the last execution of this module.')
    mftslack.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    mftslack.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from slackspace to stdout')
    mftslack.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from slackspace to OUTFILE')
    mftslack.add_argument('-w', '--write', dest='write', action='store_true', help='write to slackspace')
    mftslack.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear slackspace')
    mftslack.add_argument('-d', '--domirr', dest='domirr', action='store_true', help='write copy of data to $MFTMirr. Avoids detection with chkdsk')
    mftslack.add_argument('-i', '--info', dest='info', action='store_true', help='print mft slack information of entries in limit')
    mftslack.add_argument('-l', '--limit', dest='limit', default=-1, type=int, required=False, help='limit the amount of mft entries to print information for when using the "--info" switch')
    mftslack.add_argument('file', metavar='FILE', nargs='?', help="File to write into slack space, if nothing provided, use stdin")

    # Additional Cluster Allocation
    addcluster = subparsers.add_parser('addcluster', help='Allocate more clusters for a file')
    addcluster.set_defaults(which='addcluster')
    addcluster.add_argument('-t', '--target', dest='destination', required=False, help='absolute path to file or directory on filesystem')
    addcluster.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    addcluster.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from allocated clusters to stdout')
    addcluster.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from allocated clusters to OUTFILE')
    addcluster.add_argument('-w', '--write', dest='write', action='store_true', help='write to additional allocated clusters')
    addcluster.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear allocated clusters')
    addcluster.add_argument('file', metavar='FILE', nargs='?', help="File to write into additionally allocated clusters, if nothing provided, use stdin")

    # Additional Cluster Allocation
    badcluster = subparsers.add_parser('badcluster', help='Allocate more clusters for a file')
    badcluster.set_defaults(which='badcluster')
    badcluster.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    badcluster.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from allocated clusters to stdout')
    badcluster.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from allocated clusters to OUTFILE')
    badcluster.add_argument('-w', '--write', dest='write', action='store_true', help='write to additional allocated clusters')
    badcluster.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear allocated clusters')
    badcluster.add_argument('file', metavar='FILE', nargs='?', help="File to write into additionally allocated clusters, if nothing provided, use stdin")

    # Reserved GDT blocks
    reserved_gdt_blocks = subparsers.add_parser('reserved_gdt_blocks', help='hide data in reserved GDT blocks')
    reserved_gdt_blocks.set_defaults(which='reserved_gdt_blocks')
    reserved_gdt_blocks.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    reserved_gdt_blocks.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from reserved GDT blocks to stdout')
    reserved_gdt_blocks.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from reserved GDT blocks to OUTFILE')
    reserved_gdt_blocks.add_argument('-w', '--write', dest='write', action='store_true', help='write to reserved GDT blocks')
    reserved_gdt_blocks.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear reserved GDT blocks')
    reserved_gdt_blocks.add_argument('-i', '--info', dest='info', action='store_true', help='show infor1mation about reserved gdt')
    reserved_gdt_blocks.add_argument('file', metavar='FILE', nargs='?', help="File to write into reserved GDT blocks, if nothing provided, use stdin")

    # Superblock slack
    superblock_slack = subparsers.add_parser('superblock_slack', help='hide data in superblock slack')
    superblock_slack.set_defaults(which='superblock_slack')
    superblock_slack.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    superblock_slack.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from superblock slack to stdout')
    superblock_slack.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from superblock slack to OUTFILE')
    superblock_slack.add_argument('-w', '--write', dest='write', action='store_true', help='write to superblock slack')
    superblock_slack.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear superblock slack')
    superblock_slack.add_argument('-i', '--info', dest='info', action='store_true', help='show information about superblock')
    superblock_slack.add_argument('file', metavar='FILE', nargs='?', help="File to write into superblock slack, if nothing provided, use stdin")

    # OSD2
    osd2 = subparsers.add_parser('osd2', help='hide data in osd2 fields of inodes')
    osd2.set_defaults(which='osd2')
    osd2.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    osd2.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from osd2 fields to stdout')
    osd2.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from osd2 fields to OUTFILE')
    osd2.add_argument('-w', '--write', dest='write', action='store_true', help='write to osd2 fields')
    osd2.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear osd2 fields')
    osd2.add_argument('-i', '--info', dest='info', action='store_true', help='show information about osd2')
    osd2.add_argument('file', metavar='FILE', nargs='?', help="File to write into osd2 fields, if nothing provided, use stdin")

    # obso_faddr
    obso_faddr = subparsers.add_parser('obso_faddr', help='hide data in obso_faddr fields of inodes')
    obso_faddr.set_defaults(which='obso_faddr')
    obso_faddr.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    obso_faddr.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from obso_faddr fields to stdout')
    obso_faddr.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from obso_faddr fields to OUTFILE')
    obso_faddr.add_argument('-w', '--write', dest='write', action='store_true', help='write to obso_faddr fields')
    obso_faddr.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear obso_faddr fields')
    obso_faddr.add_argument('-i', '--info', dest='info', action='store_true', help='show information about obso_faddr')
    obso_faddr.add_argument('file', metavar='FILE', nargs='?', help="File to write into obso_faddr fields, if nothing provided, use stdin")
	
	# inode Padding
    inode_padding = subparsers.add_parser('inode_padding', help='hide data in padding fields of inodes')
    inode_padding.set_defaults(which='inode_padding')
    inode_padding.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    inode_padding.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from padding fields to stdout')
    inode_padding.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from padding fields to OUTFILE')
    inode_padding.add_argument('-w', '--write', dest='write', action='store_true', help='write to padding fields')
    inode_padding.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear padding fields')
    inode_padding.add_argument('file', metavar='FILE', nargs='?', help="File to write into padding fields, if nothing provided, use stdin")

	# write gen
    write_gen = subparsers.add_parser('write_gen', help='hide data in write_gen fields of inodes')
    write_gen.set_defaults(which='write_gen')
    write_gen.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    write_gen.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from write_gen fields to stdout')
    write_gen.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from write_gen fields to OUTFILE')
    write_gen.add_argument('-w', '--write', dest='write', action='store_true', help='write to write_gen fields')
    write_gen.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear write_gen fields')
    write_gen.add_argument('file', metavar='FILE', nargs='?', help="File to write into write_gen fields, if nothing provided, use stdin")

	
	# timestamp hiding
    timestamp = subparsers.add_parser('timestamp_hiding', help='hide data in inode timestamps')
    timestamp.set_defaults(which='timestamp_hiding')
    timestamp.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    timestamp.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from timestamps to stdout')
    timestamp.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from timestamps to OUTFILE')
    timestamp.add_argument('-w', '--write', dest='write', action='store_true', help='write to timestamps')
    timestamp.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear timestamps')
    timestamp.add_argument('file', metavar='FILE', nargs='?', help="File to write into timestamps, if nothing provided, use stdin")


	# xfield padding
    xfield = subparsers.add_parser('xfield_padding', help='hide data in inode extended fields')
    xfield.set_defaults(which='xfield_padding')
    xfield.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    xfield.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from extended fields to stdout')
    xfield.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from extended fields to OUTFILE')
    xfield.add_argument('-w', '--write', dest='write', action='store_true', help='write to extended fields')
    xfield.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear extended fields')
    xfield.add_argument('file', metavar='FILE', nargs='?', help="File to write into extended fields, if nothing provided, use stdin")
	
	

    return parser


def main():
    # set exception handler
    sys.excepthook = general_excepthook
    # Parse cli arguments
    parser = build_parser()
    args = parser.parse_args()

    # Set logging level (verbosity)
    if args.verbose is None: args.verbose = 0
    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    if args.verbose > 2:
        fish = """
                   .|_-
             ___.-´  /_.
        .--´`    `´`-,/     .
       ..--.-´-.      ´-.  /|
      (o( o( o )         ./.
      `       ´             -
   (               `.       /
    -....--   .\    \--..-  \\
        `--´    -.-´      \.-
                           \|
        """
        LOGGER.debug(fish)
        LOGGER.debug("Thank you for debugging so hard! We know it is "
                     "a mess. So, here is a friend, who will support you :)")


    # if 'metadata' was chosen
    if args.which == 'no_arguments':
        parser.print_help()
    elif args.which == 'metadata':
        do_metadata(args)
    else:
        with open(args.dev, 'rb+') as device:
            # if 'fattools' was chosen
            if args.which == "fattools":
                do_fattools(args, device)

            # if 'fileslack' was chosen
            if args.which == 'fileslack':
                do_fileslack(args, device)

            # if 'mftslack' was chosen
            if args.which == 'mftslack':
                do_mftslack(args, device)

            # if 'addcluster' was chosen
            if args.which == 'addcluster':
                do_addcluster(args, device)

            # if 'badcluster' was chosen
            if args.which == 'badcluster':
                do_badcluster(args, device)

            # if 'reserved_gdt_blocks' was chosen
            if args.which == 'reserved_gdt_blocks':
                do_reserved_gdt_blocks(args, device)

            # if 'osd2' was chosen
            if args.which == "osd2":
                do_osd2(args, device)

            # if 'obso_faddr' was chosen
            if args.which == "obso_faddr":
                do_obso_faddr(args, device)
				
			# if 'inode_padding' was chosen
            if args.which == "inode_padding":
                do_inode_padding(args, device)

			# if 'timestamp_hiding' was chosen
            if args.which == "timestamp_hiding":
                do_timestamp_hiding(args, device)
				
			# if 'xfield_padding' was chosen
            if args.which == "xfield_padding":
                do_xfield_padding(args, device)

			# if 'write_gen' was chosen
            if args.which == "write_gen":
                do_write_gen(args, device)

            # if 'superblock_slack' was chosen
            if args.which == 'superblock_slack':
                do_superblock_slack(args,device)


def general_excepthook(errtype, value, tb):
    """
    This function serves as a general exception handler, who catches all
    exceptions, that were not handled at a higher lever
    """
    LOGGER.critical("Error: %s: %s.", errtype, value)
    LOGGER.info("".join(traceback.format_exception(type, value, tb)))
    sys.exit(1)

if __name__ == "__main__":
    main()

"""
Implementation of fishy's command line interface.
"""
import sys
import traceback
import argparse
import logging
import typing as typ
from fishy.cluster_allocation import ClusterAllocation
from fishy.fat.fat_filesystem.fat_wrapper import create_fat
from fishy.fat.fat_filesystem.fattools import FATtools
from fishy.file_slack import FileSlack
from fishy.metadata import Metadata
from fishy.mft_slack import MftSlack
from fishy.osd2 import OSD2
from fishy.reserved_gdt_blocks import ReservedGDTBlocks
from fishy.superblock_slack import SuperblockSlack


LOGGER = logging.getLogger("cli")


def do_metadata(args: argparse.Namespace) -> None:
    """
    handles metadata subcommand execution
    :param args: argparse.Namespace
    """
    if args.password is None:
        meta = Metadata()
    else:
        meta = Metadata(password=args.password)
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
        if args.password is None:
            slacker = FileSlack(device, Metadata(), args.dev)
        else:
            slacker = FileSlack(device, Metadata(password=args.password), args.dev)
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
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data in fileslack into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.read_into_file(args.outfile)
    elif args.clear:
        # clear fileslack
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
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
        if args.password is None:
            slacker = MftSlack(device, Metadata(), args.dev)
        else:
            slacker = MftSlack(device, Metadata(password=args.password), args.dev)
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
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            slacker = MftSlack(device, meta, args.dev)
            slacker.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data in fileslack into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            slacker = MftSlack(device, meta, args.dev)
            slacker.read_into_file(args.outfile)
    elif args.clear:
        # clear fileslack
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
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
        if args.password is None:
            allocator = ClusterAllocation(device, Metadata(), args.dev)
        else:
            allocator = ClusterAllocation(device, Metadata(password=args.password), args.dev)
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
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            allocator = ClusterAllocation(device, meta, args.dev)
            allocator.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden data from additional clusters into outfile
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            allocator = ClusterAllocation(device, meta, args.dev)
            allocator.read_into_file(args.outfile)
    elif args.clear:
        # clear additional clusters
        with open(args.metadata, 'rb') as metadata_file:
            if args.password is None:
                meta = Metadata()
            else:
                meta = Metadata(password=args.password)
            meta.read(metadata_file)
            allocator = ClusterAllocation(device, meta, args.dev)
            allocator.clear()

def do_reserved_gdt_blocks(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles reserved_gdt_blocks subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        reserve = ReservedGDTBlocks(device, Metadata(), args.dev)
        if not args.file:
            # write from stdin into reserved GDT blocks
            reserve.write(sys.stdin.buffer)
        else:
            # write from files into reserved GDT blocks
            with open(args.file, 'rb') as fstream:
                reserve.write(fstream, args.file)
        with open(args.metadata, 'w+') as metadata_out:
            reserve.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.read_into_file(args.outfile)
    elif args.clear:
        # clear reserved GDT blocks
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            reserve = ReservedGDTBlocks(device, meta, args.dev)
            reserve.clear()

def do_superblock_slack(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles superblock_slack subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        slack = SuperblockSlack(device, Metadata(), args.dev)
        if not args.file:
            # write from stdin into superblock slack
            slack.write(sys.stdin.buffer)
        else:
            # write from files into superblock slack
            with open(args.file, 'rb') as fstream:
                slack.write(fstream, args.file)
        with open(args.metadata, 'w+') as metadata_out:
            slack.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.read_into_file(args.outfile)
    elif args.clear:
        # clear superblock slack
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            slack = SuperblockSlack(device, meta, args.dev)
            slack.clear()


def do_osd2(args: argparse.Namespace, device: typ.BinaryIO) -> None:
    """
    handles osd2 subcommand execution
    :param args: argparse.Namespace
    :param device: stream of the filesystem
    """
    if args.write:
        osd2 = OSD2(device, Metadata(), args.dev)
        if not args.file:
            # write from stdin into osd2 fields
            osd2.write(sys.stdin.buffer)
        else:
            # write from files into osd2 fields
            with open(args.file, 'rb') as fstream:
                osd2.write(fstream, args.file)
        with open(args.metadata, 'w+') as metadata_out:
            osd2.metadata.write(metadata_out)
    elif args.read:
        # read hidden file to stdout
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.read(sys.stdout.buffer)
    elif args.outfile:
        # read hidden file into outfile
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.read_into_file(args.outfile)
    elif args.clear:
        # clear osd2 fields
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            osd2 = OSD2(device, meta, args.dev)
            osd2.clear()


def build_parser() -> argparse.ArgumentParser:
    """
    Get the cli parser

    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description='Toolkit for filesystem based data hiding techniques.')
    # TODO: Maybe this option should be required for hiding technique
    #       subcommand but not for metadata.... needs more thoughs than I
    #       currently have
    parser.add_argument('-d', '--device', dest='dev', required=False, help='Path to filesystem')
    parser.add_argument('-p', '--password', dest='password', required=False, help='Password for encryption of metadata')
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
    fileslack.add_argument('-d', '--dest', dest='destination', action='append', required=False, help='absolute path to file or directory on filesystem, directories will be parsed recursively')
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
    mftslack.add_argument('-i', '--info', dest='info', action='store_true', help='print mft slack information of entries in limit')
    mftslack.add_argument('-l', '--limit', dest='limit', default=-1, type=int, required=False, help='limit the amount of mft entries to print information for when using the "--info" switch')
    mftslack.add_argument('file', metavar='FILE', nargs='?', help="File to write into slack space, if nothing provided, use stdin")

    # Additional Cluster Allocation
    addcluster = subparsers.add_parser('addcluster', help='Allocate more clusters for a file')
    addcluster.set_defaults(which='addcluster')
    addcluster.add_argument('-d', '--dest', dest='destination', required=False, help='absolute path to file or directory on filesystem, directories will be parsed recursively')
    addcluster.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    addcluster.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from allocated clusters to stdout')
    addcluster.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from allocated clusters to OUTFILE')
    addcluster.add_argument('-w', '--write', dest='write', action='store_true', help='write to additional allocated clusters')
    addcluster.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear allocated clusters')
    addcluster.add_argument('file', metavar='FILE', nargs='?', help="File to write into additionally allocated clusters, if nothing provided, use stdin")

    # Reserved GDT blocks
    reserved_gdt_blocks = subparsers.add_parser('reserved_gdt_blocks', help='hide data in reserved GDT blocks')
    reserved_gdt_blocks.set_defaults(which='reserved_gdt_blocks')
    reserved_gdt_blocks.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    reserved_gdt_blocks.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from reserved GDT blocks to stdout')
    reserved_gdt_blocks.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from reserved GDT blocks to OUTFILE')
    reserved_gdt_blocks.add_argument('-w', '--write', dest='write', action='store_true', help='write to reserved GDT blocks')
    reserved_gdt_blocks.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear reserved GDT blocks')
    reserved_gdt_blocks.add_argument('file', metavar='FILE', nargs='?', help="File to write into reserved GDT blocks, if nothing provided, use stdin")

    # Superblock slack
    superblock_slack = subparsers.add_parser('superblock_slack', help='hide data in superblock slack')
    superblock_slack.set_defaults(which='superblock_slack')
    superblock_slack.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    superblock_slack.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from superblock slack to stdout')
    superblock_slack.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from superblock slack to OUTFILE')
    superblock_slack.add_argument('-w', '--write', dest='write', action='store_true', help='write to superblock slack')
    superblock_slack.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear superblock slack')
    superblock_slack.add_argument('file', metavar='FILE', nargs='?', help="File to write into superblock slack, if nothing provided, use stdin")

    # OSD2
    osd2 = subparsers.add_parser('osd2', help='hide data in osd2 fields of inodes')
    osd2.set_defaults(which='osd2')
    osd2.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    osd2.add_argument('-r', '--read', dest='read', action='store_true', help='read hidden data from osd2 fields to stdout')
    osd2.add_argument('-o', '--outfile', dest='outfile', metavar='OUTFILE', help='read hidden data from osd2 fields to OUTFILE')
    osd2.add_argument('-w', '--write', dest='write', action='store_true', help='write to osd2 fields')
    osd2.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear osd2 fields')
    osd2.add_argument('file', metavar='FILE', nargs='?', help="File to write into osd2 fields, if nothing provided, use stdin")

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
    if args.which == 'metadata':
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

            # if 'reserved_gdt_blocks' was chosen
            if args.which == 'reserved_gdt_blocks':
                do_reserved_gdt_blocks(args, device)

            # if 'osd2' was chosen
            if args.which == "osd2":
                do_osd2(args, device)

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

import sys
import argparse
import logging
import typing as typ
from .fat.fat_filesystem.fattools import FATtools
from .fat.fat_filesystem.fat_wrapper import create_fat
from .file_slack import FileSlack
from .metadata import Metadata


def do_metadata(args: argparse.Namespace) -> None:
    """
    handles metadata subcommand execution
    :param args: argparse.Namespace
    """
    meta = Metadata()
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
    if args.write:
        slacker = FileSlack(device, Metadata(), args.dev)
        if len(args.files) == 0:
            # write from stdin into fileslack
            slacker.write(sys.stdin.buffer, args.destination)
        else:
            # write from files into fileslack
            for filename in args.files:
                with open(filename, 'rb') as fstream:
                    slacker.write(fstream, args.destination, filename)
        with open(args.metadata, 'w+') as metadata_out:
            slacker.metadata.write(metadata_out)
    elif args.read:
        # read file slack of a single hidden file to stdout
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.read(sys.stdout.buffer, args.read)
    elif args.outdir:
        # read fileslack of all hidden files into files
        # under a given directory
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.read_into_files(args.outdir)
    elif args.clear:
        # clear fileslack
        with open(args.metadata, 'r') as metadata_file:
            meta = Metadata()
            meta.read(metadata_file)
            slacker = FileSlack(device, meta, args.dev)
            slacker.clear()


def main():
    parser = argparse.ArgumentParser(description='Toolkit for filesystem based data hiding techniques.')
    # TODO: Maybe this option should be required for hiding technique
    #       subcommand but not for metadata.... needs more thoughs than I
    #       currently have
    parser.add_argument('-d', '--device', dest='dev', required=False, help='Path to filesystem')
    # TODO Maybe we should provide a more fine grained option to choose between different log levels
    parser.add_argument('--debug', dest='debug', action='store_true', help="turn debug output on")
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
    metadata.add_argument('-m', '--metadata', dest='metadata', type=argparse.FileType('r'), help="filepath to metadata file")

    # FileSlack
    fileslack = subparsers.add_parser('fileslack', help='Operate on file slack')
    fileslack.set_defaults(which='fileslack')
    fileslack.add_argument('-d', '--dest', dest='destination', action='append', required=False, help='absolute path to file or directory on filesystem, directories will be parsed recursively')
    fileslack.add_argument('-m', '--metadata', dest='metadata', required=True, help='Metadata file to use')
    fileslack.add_argument('-r', '--read', dest='read', metavar='FILE_ID', help='read file with FILE_ID from slackspace to stdout')
    fileslack.add_argument('-o', '--outdir', dest='outdir', metavar='OUTDIR', help='read files from slackspace to OUTDIR')
    fileslack.add_argument('-w', '--write', dest='write', action='store_true', help='write to slackspace')
    fileslack.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear slackspace')
    fileslack.add_argument('files', metavar='FILE', nargs='*', help="Files to write into slack space, if nothing provided, use stdin")

    # Parse cli arguments
    args = parser.parse_args()

    if args.debug:
        # Turn debug output on
        logging.basicConfig(level=logging.DEBUG)

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


if __name__ == "__main__":
    main()

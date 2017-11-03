import sys
import argparse
import logging
from .fat.fat_filesystem.fattools import FATtools
from .fat.fat_filesystem.fat_wrapper import FAT
from .fat.simple_file_slack import SimpleFileSlack as FATSimpleFileSlack
from .fileSlack import FileSlack
from .metadata import Metadata


def main():
    parser = argparse.ArgumentParser(description='Toolkit for filesystem based data hiding techniques.')
    # TODO: Maybe this option should be required for hiding technique options
    #       but not for metadata.... needs more thoughs than I currently have
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
    metadata = subparsers.add_parser('fileslack', help='list information about a metadata file')
    metadata.set_defaults(which='metadata')
    metadata.add_argument('-m', '--metadata', dest='metadata', type=argparse.FileType('r'), help="filepath to metadata file")
    metadata.add_argument('-i', '--info', dest='info', action='store_true', help='Show information about the metadata file')

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

    # FAT Simple File Slack
    # Deprecated, will move into general FileSlack module
    # Currently still here for historical reasons
    fatsds = subparsers.add_parser('fatsimplefileslack', help='Operate on slack space of a single file')
    fatsds.set_defaults(which='fatsimplefileslack')
    fatsds.add_argument('-f', '--file', dest='file', required=True, help='absolute path to file on filesystem')
    fatsds.add_argument('-r', '--read', dest='read', action='store_true', help='read from slackspace')
    fatsds.add_argument('-w', '--write', dest='write', action='store_true', help='write to slackspace')
    fatsds.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear slackspace')

    # Parse cli arguments
    args = parser.parse_args()

    if args.debug:
        # Turn debug output on
        logging.basicConfig(level=logging.DEBUG)

    with open(args.dev, 'rb+') as device:
        # if 'fattools' was chosen
        if args.which == "fattools":
            ft = FATtools(FAT(device))
            if args.fat:
                ft.list_fat()
            elif args.info:
                ft.list_info()
            elif args.list is not None:
                ft.list_directory(args.list)

        # if 'metadata' was chosen
        if args.which == 'metadata':
            raise NotImplementedError()
            # m = Metadata(args.metadata)
            # m.print()

        # if 'fileslack' was chosen
        if args.which == 'fileslack':
            if args.write:
                fs = FileSlack(device, Metadata(), args.dev)
                if len(args.files) == 0:
                    # write from stdin into fileslack
                    fs.write(sys.stdin.buffer, args.destination)
                else:
                    # write from files  into fileslack
                    for f in args.files:
                        with open(f, 'rb') as fstream:
                            fs.write(fstream, args.destination, f)
                with open(args.metadata, 'w+') as metadata_out:
                    fs.metadata.write(metadata_out)
            elif args.read:
                # read file slack of a single hidden file to stdout
                with open(args.metadata, 'r') as metadata_file:
                    m = Metadata()
                    m.read(metadata_file)
                    fs = FileSlack(device, m)
                    fs.read(sys.stdout.buffer, args.read)
            elif args.outdir:
                # read fileslack of all hidden files into files
                # under a given directory
                with open(args.metadata, 'r') as metadata_file:
                    m = Metadata()
                    m.read(metadata_file)
                    fs = FileSlack(device, m)
                    fs.read_into_files(args.outdir)
            elif args.clear:
                # clear fileslack
                with open(args.metadata, 'r') as metadata_file:
                    m = Metadata()
                    m.read(metadata_file)
                    fs = FileSlack(device, m)
                    fs.clear()

        # if 'fatsimplefileslack' was chosen
        if args.which == "fatsimplefileslack":
            filename = args.file
            fs = FATSimpleFileSlack(device)
            if args.write:
                fs.write(sys.stdin.buffer, filename)
            if args.read:
                fs.read(sys.stdout.buffer, filename)
            if args.clear:
                fs.clear(filename)


if __name__ == "__main__":
    main()

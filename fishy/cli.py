import sys
import argparse
from .fat.simple_disk_slack import SimpleDiskSlack as FATSimpleDiskSlack

def main():
    parser = argparse.ArgumentParser(description='Toolkit for filesystem based data hiding techniques.')
    parser.add_argument('-d', '--device', dest='dev', required=True, help='Path to filesystem')
    subparsers = parser.add_subparsers(help='Hiding techniques sub-commands')

    # FAT Simple Disk Slack
    fatsds = subparsers.add_parser('fatsimplediskslack', help='Operate on slack space of a single file')
    fatsds.set_defaults(which='fatsimplediskslack')
    fatsds.add_argument('-f', '--file', dest='file', required=True, help='absolute path to file on filesystem')
    fatsds.add_argument('-r', '--read', dest='read', action='store_true', help='read from slackspace')
    fatsds.add_argument('-w', '--write', dest='write', action='store_true', help='write to slackspace')
    fatsds.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear slackspace')
    args = parser.parse_args()

    f = open(args.dev, 'rb+')

    # if 'fatsimplediskslack' was chosen
    if args.which == "fatsimplediskslack":
        filename = args.file
        fs = FATSimpleDiskSlack(f)
        if args.write:
            fs.write(sys.stdin.buffer, filename)
        if args.read:
            fs.read(sys.stdout.buffer, filename)
        if args.clear:
            fs.clear(filename)

if __name__ == "__main__":
    main()

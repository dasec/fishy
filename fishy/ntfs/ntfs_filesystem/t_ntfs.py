"""
Manual testing script for NTFS class
"""

from .ntfs import NTFS
from .record_header import RECORD_HEADER
from .attribute_header import ATTRIBUTE_HEADER

with open('ntfs_filesystem/testfs-ntfs.dd', 'rb') as fs:
    n = NTFS(fs)
    print("Record Size: ", n.record_size)
    print("Start Offset: ", n.start_offset)
    print("MFT Offset: ", n.mft_offset)
    print("MFT Runs: ", n.mft_runs)
    record = n.get_record(0)
    header = RECORD_HEADER.parse(record)
    print("Record Header Signature: ", header.signature)
    offset = header.first_attribute_offset
    header = ATTRIBUTE_HEADER.parse(record[offset:])
    print("Attribute type: ", header.type)
    offset = offset + header.total_length
    header = ATTRIBUTE_HEADER.parse(record[offset:])
    print("Attribute type: ", header.type)

    #Print the filenames of the first mft records
    for x in range(0, 75):
        name: str = n.get_filename_from_record(x)
        print("Name of record ", x, ": ", name)

    record_number = n.get_record_of_file("another")
    print("Record number of file \"another\": ", record_number)
    print("Data of file \"another\": ", n.get_data(record_number))
    print("Dataruns of file \"long_file.txt\": ", n.get_data_runs(n.get_record(66)))
    print("Record number of file \"onedirectory/nested_directory/royce.txt\": ", n.get_record_of_file('onedirectory/nested_directory/royce.txt'))
    print(n.get_data_runs(n.get_record(6)))

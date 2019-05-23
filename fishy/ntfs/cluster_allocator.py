"""
Implementation for allocation of additional
data runs for a file to hide data in
"""

import typing
from math import ceil
from .ntfs_filesystem.ntfs import NTFS
from .ntfs_filesystem.attributes import DATA_ID
from .ntfs_filesystem.attribute_header import ATTRIBUTE_HEADER


class AllocatorMetadata:
    """
    This class contains the metadata needed by the
    ClusterAllocator for allocating additional clusters
    to a file in ntfs
    """

    def __init__(self, d: typing.Dict = None):
        """
        Declaration of the needed attributes
        """
        if d is None:
            self.file = None
            self.size = 0
            self.new_runs = []
        else:
            self.file = d['file']
            self.size = d['size']
            self.new_runs = d['new_runs']


class ClusterAllocator:
    """
    This class can allocate additional clusters
    to a file and write data into those clusters.
    It can also read from clusters earlier allocated by it
    and clear clusters allocated by it.
    """

    def __init__(self, stream: typing.BinaryIO):
        """
        Parse the stream as ntfs
        """
        self.stream = stream
        self.ntfs = NTFS(stream)


    def write(self, instream: typing.BinaryIO, path: str) -> AllocatorMetadata:
        """
        Writes the data from instream the newly allocated clusters for the file at path
        :param instream: The stream constaining the data to write
        :param path: The path to the file to append to
        :return: The created AllocatorMetadata
        """
        metadata = AllocatorMetadata()
        size = len(instream.peek())
        #size = instream.seek(0, 2)
        runs = self.allocate_clusters(path, ceil(size/self.ntfs.cluster_size))
        #instream.seek(0)
        written = 0
        for run in runs:
            self.ntfs.stream.seek(self.ntfs.start_offset + \
                    self.ntfs.cluster_size * run['offset'])
            length = run['length'] * self.ntfs.cluster_size
            if written + length >= size:
                length = size - written

            written += self.ntfs.stream.write(instream.read(length))

        metadata.file = path
        metadata.size = size
        metadata.new_runs = runs
        return metadata


    def read(self, outstream: typing.BinaryIO, metadata: AllocatorMetadata) -> None:
        """
        Reads the hidden data specified by metadata and writes them to outstream
        :param outstream: The stream to write the data to
        :param metadata: The metadata describing the hidden data
        """
        cluster_size = self.ntfs.cluster_size
        size = metadata.size
        runs = metadata.new_runs

        written = 0
        for run in runs:
            self.ntfs.stream.seek(self.ntfs.start_offset + \
                    self.ntfs.cluster_size * run['offset'])
            length = run['length'] * self.ntfs.cluster_size
            if written + length >= size:
                length = size - written

            written += outstream.write(self.ntfs.stream.read(length))


    def clear(self, metadata: AllocatorMetadata) -> None:
        """
        Clears the hidden data. Removes the runs from the file and deallocates the clusters.
        :param metadata: The metadata for the hidden data
        """
        #Remove runs from file
        #TODO Pay attention to attributes following the data attribute and record size

        #Get record number of file
        file_record_n = self.ntfs.get_record_of_file(metadata.file)
        #File doesn't exist anymore -> Nothing to clear
        #TODO Maybe need to deallocate additional clusters? Look into behavior on deletion of file
        if file_record_n is None:
            return

        #Get record of file
        file_record = self.ntfs.get_record(file_record_n)
        #Get offset to data attribute
        offset = self.ntfs.find_attribute(file_record, DATA_ID)
        attribute_header = ATTRIBUTE_HEADER.parse(file_record[offset:])

        #Overwrite hidden data
        for run in metadata.new_runs:
            self.ntfs.stream.seek(self.ntfs.start_offset + \
                    self.ntfs.cluster_size * run['offset'])
            length = run['length'] * self.ntfs.cluster_size

            self.ntfs.stream.write(b'0'*length)

        #Iterate through runs and remove ones that were added
        offset += attribute_header.datarun_offset
        run_offset = 0
        byte = file_record[offset]
        while byte != 0:
            run_offset_len = byte >> 4
            run_length_len = byte & 0x0F

            offset += 1 + run_length_len
            run_length = int.from_bytes(file_record[offset-run_length_len:offset], 'little')
            offset += run_offset_len
            run_offset += int.from_bytes(file_record[offset-run_offset_len:offset], 'little')
            if {'length':run_length, 'offset':run_offset} in metadata.new_runs:
                file_record[offset-run_offset_len-run_length_len-1:offset] = b'0'
            byte = file_record[offset]

        #Deallocate clusters in $Bitmap file
        #TODO
        bitmap_run = self.ntfs.get_data_runs(self.ntfs.get_record(6))[0]
        self.ntfs.stream.seek(self.ntfs.start_offset + bitmap_run['offset'])
        for data_run in metadata.new_runs:
            self.ntfs.stream.seek(int(data_run['offset']/8), 1)
            byte = int.from_bytes(self.ntfs.stream.read(1), 'little')
            byte = byte & ( 0xFF ^ (1 << (7 - data_run['offset']%8)))
            byte = bytes([byte])    #TODO check if works properly
            self.ntfs.stream.seek(-1, 1)
            self.ntfs.stream.write(byte)
            self.ntfs.stream.seek(-1, 1)

        # self.ntfs.stream.seek(self.ntfs.start_offset + self.ntfs.mft_offset + \
                # self.ntfs.record_size * 6)

    def allocate_clusters(self, path: str,  n: int) -> [{'length', 'offset'}]:
        """
        Find n unallocated clusters and allocate them to the given file
        :param path: The path to the file to allocate the clusters to
        :param n: The number of clusters to allocate
        :return: The newly allocated runs of the file
        """

        #Get the allocation bitmap from the $Bitmap file
        bitmap = self.ntfs.get_data(6)
        file_record_n = self.ntfs.get_record_of_file(path)
        #The file doesn't exist
        assert not file_record_n is None, "Specified file not found"

        file_record = self.ntfs.get_record(file_record_n)
        offset = self.ntfs.find_attribute(file_record, DATA_ID)
        assert not offset is None, "Specified file has no data attribute"
        attribute_header = ATTRIBUTE_HEADER.parse(file_record[offset:])
        assert attribute_header.nonresident, \
                "Allocating clusters to resident data not supported yet"

        #Search for the requested amount of unallocated clusters
        new_runs = []
        clusters_found = []
        cluster_pos = 50

        #TODO Ignore the first few clusters
        #Go through every bit of the bitmap
        for byte in bitmap:
            for position in range(8):
                bit = (byte >> 7-position) & 1
                #Cluster is unallocated
                if bit == 0:
                    clusters_found.append(cluster_pos+position)
                    #The desired number of unallocated clusters was found
                    if len(clusters_found) == n:
                        break

            #Also exit outer loop when desired number found
            if len(clusters_found) == n:
                break

            cluster_pos += 8

        assert len(clusters_found) == n,\
         "Not enough free clusters found (" + str(len(clusters_found)) + " out of " + str(n) + ")"
        self._write_cluster_allocation(clusters_found)

        #Add the runs to the file
        #TODO Pay attention to attributes following the data attribute and record size
        offset += attribute_header.datarun_offset
        run_offset = 0
        byte = file_record[offset]
        while byte != 0:
            run_offset_len = byte >> 4
            offset += 1 + (byte & 0x0F) + run_offset_len
            run_offset += int.from_bytes(file_record[offset-run_offset_len:offset], 'little')
            byte = file_record[offset]

        #TODO Multiple clusters to one run when possible
        new_run_data = bytearray()
        for cluster in clusters_found:
            relative_run_offset = cluster - run_offset
            run_offset += relative_run_offset
            new_runs.append({'length': 1, 'offset': run_offset})
            relative_run_offset = relative_run_offset.to_bytes(\
                    (relative_run_offset.bit_length()+7) // 8, byteorder='little', signed=True)
            run_len = (1).to_bytes(1, 'little')
            byte = bytes([(len(relative_run_offset) << 4) & 1])
            new_run_data.extend(byte)
            new_run_data.extend(run_len)
            new_run_data.extend(relative_run_offset)

        new_run_data.extend(b'0')
        self.ntfs.stream.seek(self.ntfs.start_offset + self.ntfs.mft_offset + \
                self.ntfs.record_size * file_record_n + offset)
        self.ntfs.stream.write(new_run_data)
        return new_runs


    def _write_cluster_allocation(self, clusters: []):

        offset = self.ntfs.start_offset
        bitmap_record = self.ntfs.get_record(6)
        offset += self.ntfs.get_data_runs(bitmap_record)[0]['offset']

        for cluster in clusters:
            position = int(cluster/8)

            self.stream.seek(offset + position)
            old_value = int.from_bytes(self.stream.read(1), byteorder='big')
            new_value = old_value | (1 << (cluster % 8))
            self.stream.seek(-1, 1)
            self.stream.write(bytes([new_value]))


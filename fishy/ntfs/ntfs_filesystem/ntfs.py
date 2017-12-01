"""
Contains a class for NTFS operations
"""

import typing
from .bootsector import NTFS_BOOTSECTOR
from .attribute_header import ATTRIBUTE_HEADER
from .record_header import RECORD_HEADER
from .attributes import FILE_NAME_ID, DATA_ID, INDEX_ROOT_ID, INDEX_ALLOCATION_ID,\
FILE_NAME_ATTRIBUTE, INDEX_ROOT, INDEX_HEADER, INDEX_RECORD_HEADER, INDEX_RECORD_ENTRY

ROOT_DIR_RECORD = 5
BITMAP_RECORD  = 6

#TODO Implement reading data from records with attribute list
class NTFS:
    """
    Class for NTFS operations
    """

    def __init__(self, stream: typing.BinaryIO):
        """
        :param stream: binary stream of the NTFS data
        """
        self.stream = stream
        self.start_offset = stream.tell()
        bootsector = self.get_bootsector()
        self.sector_size = bootsector.sector_size
        self.cluster_size = bootsector.cluster_size*self.sector_size
        self.mft_offset = bootsector.mft_cluster*self.cluster_size
        self.record_size = self._calculate_record_size(bootsector)

        stream.seek(self.start_offset + self.mft_offset)
        self.mft_record = stream.read(self.record_size)

        self.mft_runs = self.get_data_runs(self.mft_record)


    def _calculate_record_size(self, bootsector) -> int:
        """
        Calculates the size of a MFT record
        using the cluster_size field of the bootsector
        :param bootsector: The ntfs bootsector
        """

        size = bootsector.clusters_per_file_record

        #If the size is positive it is in clusters
        if size > 0:
            size = size*self.cluster_size

        #If the size is negative that means a size of 2^|size| bytes
        elif size < 0:
            size = 2**(-1*size)

        return size


    def get_bootsector(self) -> NTFS_BOOTSECTOR:
        """
        Returns a NTFS_BOOTSECTOR struct of the bootsector
        """
        self.stream.seek(self.start_offset)
        return NTFS_BOOTSECTOR.parse_stream(self.stream)


    def get_bootsector_copy(self) -> NTFS_BOOTSECTOR:
        """
        Returns a NTFS_BOOTSECTOR struct of the bootsector copy
        """
        #Get the main bootsector to look for disk size
        bootsector = self.get_bootsector()
        #Calculate the offset to the bootsector copy (last sector)
        offset = self.start_offset + bootsector.total_sectors*bootsector.sector_size
        #Parse and return the bootsector copy
        self.stream.seek(offset)
        return NTFS_BOOTSECTOR.parse_stream(self.stream)


    def get_record(self, n: int) -> bytes:
        """
        Returns the nth record of the mft
        :param n: The number of the mft entry
        """

        #Check which mft run the record is in
        offset = 0
        records = 0
        for run in self.mft_runs:
            records += int(run['length']/self.record_size)
            offset += run['offset']
            #Requested record is in current run
            if records >= n:
                #Calculate the offset in the correct run
                record_diff = records - int(run['length']/self.record_size) + (n)
                #Calculate the total offset in the filesystem
                offset += record_diff * self.record_size
                break

        #Seek to the absolute offset on the disk
        self.stream.seek(self.start_offset + offset)
        return self.stream.read(self.record_size)


    def get_record_of_file(self, name: str, record_n: int = None) -> int:
        """
        Returns the record number of the file with the given name
        :param name: The name of the file to search
        :param record_n: The record number of the directory to look in
        """

        #print(name)
        #End of recursion
        if name == '':
            return record_n

        #Split the given string into path components
        path = name.split('/')

        #Start of recursion: Search the root directory
        if record_n is None:
            record_n = ROOT_DIR_RECORD

        #Get the INDEX_ROOT attribute of the directory
        record = self.get_record(record_n)
        offset = self.find_attribute(record, INDEX_ROOT_ID)
        attribute_header = ATTRIBUTE_HEADER.parse(record[offset:])
        offset += attribute_header.offset

        #Get the header of the index entries
        offset += INDEX_ROOT.sizeof()
        index_header = INDEX_HEADER.parse(record[offset:])

        #The indices are not stored inside the mft record
        if index_header.flags == 1:
            #Get the INDEX_ALLOCATION attribute
            offset = self.find_attribute(record, INDEX_ALLOCATION_ID)
            attribute_header = ATTRIBUTE_HEADER.parse(record[offset:])

            #Get the runs of the index records
            runs = self.get_data_runs(record, offset)

            #Search through all runs
            run_offset = self.start_offset
            for run in runs:
                #Read the clusters of the run from the image
                run_offset += run['offset']
                self.stream.seek(run_offset)
                index_record = self.stream.read(run['length'])
                index_record_header = INDEX_RECORD_HEADER.parse(index_record)

                #The index_entry_offset field is relative to 0x18
                offset = index_record_header.index_entry_offset + 0x18

                #Search through all index entries in the record
                flags = 0
                while offset < index_record_header.size_of_entries and flags != 2:
                    index_record_entry = INDEX_RECORD_ENTRY.parse(index_record[offset:])
                    #print(index_record_entry)

                    #The first path component is found
                    #index_record_entry.file_name seems to be corrupted rather often,
                    #so the name is looked up in the mft record
                    if self.get_filename_from_record(\
                            index_record_entry.record_reference.segment_number_low_part\
                            ) == path[0]:

                        #Remove the first path component
                        path.remove(path[0])
                        #And recursively call with the rest of the path
                        name = "/".join(path)
                        return self.get_record_of_file(name,\
                                index_record_entry.record_reference.segment_number_low_part)

                    #Read the flags and update the offset
                    flags = index_record_entry.flags
                    offset += index_record_entry.size_of_index_entry

        #The indices are stored inside the mft record
        else:
            #Remember the offset of the INDEX_HEADER
            start_offset = offset

            #Get the offset to the first entry
            offset += index_header.first_entry_offset
            index_record_entry = INDEX_RECORD_ENTRY.parse(record[offset:])

            #Search through all index entries in the record
            flags = 0
            while offset < start_offset + index_header.total_size and flags != 2:
                index_record_entry = INDEX_RECORD_ENTRY.parse(record[offset:])
                #print(index_record_entry)
                #print(index_record_entry.file_name.decode('utf-16'))

                #The first path component is found
                #index_record_entry.file_name seems to be corrupted rather often,
                #so the name is looked up in the mft record
                if self.get_filename_from_record(\
                        index_record_entry.record_reference.segment_number_low_part\
                        ) == path[0]:

                    #Remove the first path component
                    path.remove(path[0])
                    #And recursively call with the rest of the path
                    name = "/".join(path)
                    return self.get_record_of_file(name,\
                            index_record_entry.record_reference.segment_number_low_part)

                #Read the flags and update the offset
                flags = index_record_entry.flags
                offset += index_record_entry.size_of_index_entry


    def get_filename_from_record(self, n: int) -> str:
        """
        Extracts the filename from the FILE_NAME_ATTRIBUTE if the record n
        """
        record = self.get_record(n)
        offset = self.find_attribute(record, FILE_NAME_ID)
        if offset != None:
            #Calculate offset to actual attribute data
            header = ATTRIBUTE_HEADER.parse(record[offset:])
            offset = offset + header.offset

            #Extract name from FILE_NAME_ATTRIBUTE
            filename_attribute = FILE_NAME_ATTRIBUTE.parse(record[offset:])
            name = filename_attribute.file_name
            return name.decode("utf-16")


    def get_attribute_header_offset(self, record: bytes) -> int:
        """
        Return offset to first attribute header of MFT Record
        :param record: The MFT Record
        """
        record_header = RECORD_HEADER.parse(record)
        return record_header.first_attribute_offset


    def find_attribute(self, record: bytes, attr_id: int, include_header: bool = True) -> int:
        """
        Returns the offset of the first attribute with the specified id from the mft record
        :param record: The mft record
        :param attr_id: The id of the attribute to find
        :param include_header: Whether the offset should include the header
        :return: The offset to the attribute
        """
        offset = self.get_attribute_header_offset(record)
        while offset < self.record_size:
            attribute_header = ATTRIBUTE_HEADER.parse(record[offset:])

            #Attribute found
            if attribute_header.type == attr_id:
                #Header should not be included in offset
                #TODO Definitely create tests for that
                if not include_header:
                    #Add offset to actual attribute
                    if attribute_header.nonresident:
                        offset += attribute_header.datarun_offset
                    else:
                        offset += attribute_header.offset

                return offset

            #There is a next attribute
            #elif attribute_header.total_length != ATTRIBUTE_HEADER.sizeof(attribute_header):
            elif attribute_header.nonresident or attribute_header.offset != 0:
                offset = offset + attribute_header.total_length

            #There is no next attribute
            else:
                return None

        #Why not?
        return None


    def get_data(self, n: int) -> bytes:
        """
        Extracts the data from a MFT Record
        :param n: the number of the MFT Record
        """
        record = self.get_record(n)
        offset = self.find_attribute(record, DATA_ID)

        if offset != None:
            return self.__extract_from_data_attribute(record, offset)


    def __extract_from_data_attribute(self, record: bytes, offset: int) -> bytes:
        """
        Extracts the data from a data attribute
        :param record: The record containing the data attribute
        :param offset: The offset to the data attribute header
        """

        header = ATTRIBUTE_HEADER.parse(record[offset:])

        #Nonresident attribute
        if header.nonresident:
            runs = self.get_data_runs(record, offset)
            data = bytearray()
            offset = 0
            for run in runs:
                offset += run['offset']
                self.stream.seek(self.start_offset + offset)
                data.extend(self.stream.read(run['length']))

            return data

        #Resident attribute
        else:
            offset = offset + header.offset
            length = header.length
            return record[offset:offset+length]


    def get_data_runs(self, record: bytes, offset: int = None):
        """
        Extracts data runs of a data attribute from a record
        :param record: The record to extract from
        :param offset: The offset to the data attribute
        """

        #Try to find offset of data attribute if none is given
        if offset is None:
            offset = self.find_attribute(record, DATA_ID)
            if offset is None:
                return None

        header = ATTRIBUTE_HEADER.parse(record[offset:])

        #Only nonresident data has runs
        if header.nonresident:
            runs = []
            offset = offset + header.datarun_offset
            #The first byte contains the size of the run length and offset field
            byte = record[offset]
            #Stop if there is an entry for a run with length=offset=0
            while byte != 0:
                offset = offset + 1

                #The last four bits are the size of the length field
                length = (byte & 0x0F)
                #The first four bits are the size of the offset field
                run_offset = byte >> 4
                #Read the run length in clusters
                offset += length
                length = record[offset-length:offset]
                #Read the run offset in clusters
                offset += run_offset
                run_offset = record[offset-run_offset:offset]

                #Convert the values from clusters to bytes
                length = int.from_bytes(length, "little")*self.cluster_size
                run_offset = int.from_bytes(run_offset, "little")*self.cluster_size
                runs.append({'length': length, 'offset': run_offset})
                byte = record[offset]

            return runs
        else:
            return []

    def get_attribute_size(self, record: bytes, attr_id: int) -> int:
        """
        Returns the size of the given attribute in the given record
        :param record: The record of the attribute
        :param attr_id: The id of the attribute to look for
        """
        #Get the header of the requested attribute
        offset = self.find_attribute(record, attr_id)
        #There is no attribute of the requested type
        if offset is None:
            return 0

        #Parse the attribute header
        attribute_header = ATTRIBUTE_HEADER.parse(record[offset:])
        #Distinguish between nonresident and resident attributes
        if attribute_header.nonresident:
            return attribute_header.alloc_size
        else:
            return attribute_header.size


    #TODO Allocate more space if needed and consider the real size field in the record header
    def set_data_size(self, record_n: int, size: int) -> bool:
        """
        :param record_n: The record number of the data attribute
        :param size: The size to set
        :return: Whether setting the size was successful
        """
        #Get the desired record
        record = self.get_record(record_n)
        offset = self.find_attribute(record, DATA_ID)

        #No data attribute in the record
        if offset is None:
            return False

        #Get attribute header
        attribute_header = ATTRIBUTE_HEADER.parse(record[offset:])
        #Distinguish between resident and nonresident attribute
        if attribute_header.nonresident:
            #Don't allow for setting a size bigger than the allocated disk space
            if size > attribute_header.alloc_size:
                return False
            #Set the size
            attribute_header.real_size = size
            #Set the stream size to the next cluster boundary
            attribute_header.stream_size = size + (self.cluster_size - size % self.cluster_size)

        else:
            #Check if new size fits into record
            if size > (self.record_size - (8+offset)):
                return False
            #Set the size
            attribute_header.length = size

        #Write the changes
        offset = self.mft_offset + record_n*self.record_size + offset
        self.stream.seek(self.start_offset + offset)
        self.stream.write(attribute_header.build())

        return True


    #TODO Test test test and test
    def write_data(self, record_n: int, data: bytes) -> bool:
        """
        Writes data into an existing data attribute of a mft record without changing its size
        :param record_n: The the number of the record to write into
        :param data: The data to write
        :return: Whether the write was successful
        """
        #Get the desired record
        record = self.get_record(record_n)
        #Check if the data attribute is big enough for the data to write
        data_size = len(data)

        #Size of the data attribute couldn't be set to size of data to write
        if not self.set_data_size(record_n, data_size):
            return False

        #Get the runs of the data attribute
        runs = self.get_data_runs(record)
        #There is no data attribute
        if runs is None:
            return False
        #The data attribute is resident
        elif runs == []:
            #Treat the resident data like a data run
            length = self.get_attribute_size(record, DATA_ID)
            offset = self.mft_offset + self.record_size*record_n + \
                    self.find_attribute(record, DATA_ID, False)
            runs.append({'length': length, 'offset': offset})
        #The data attribute is nonresident
        else:
            #Append RAM Slack to data
            if data_size % self.sector_size != 0:
                data.append(b'\0' * (self.sector_size - data_size % self.sector_size))
                data_size += self.sector_size - data_size % self.sector_size

        #Write the data to the data runs
        written = 0
        offset = self.start_offset
        for run in runs:
            offset += run['offset']
            length = run['length']
            #For the last run
            if written+length > data_size:
                length = data_size - written

            #Write the data to the run
            self.stream.seek(offset)
            written_to_run = self.stream.write(data[offset:offset+length])

            #Something went wrong
            if written_to_run != length:
                return False

            written += written_to_run

            #All data written
            if written == data_size:
                return True


    #TODO Implement
    def allocate_clusters(self, clusters: []) -> bool:
        """
        Sets the given clusters as allocated in the $Bitmap file
        :param clusters: The clusters to allocate
        """
        pass

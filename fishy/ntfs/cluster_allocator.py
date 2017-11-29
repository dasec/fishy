"""
Implementation for allocation of additional
data runs for a file to hide data in
"""

import typing
from .ntfs_filesystem.ntfs import NTFS


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
            self.original_runs = []
            self.new_runs = []
        else:
            self.file = d['file']
            self.original_runs = d['original_runs']
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


    def allocate_clusters(self, n: int) -> [{'lenght', 'offset'}] -> AllocatorMetadata:
        """
        Find n unallocated clusters and add them to the data runs of the $Bitmap file
        """

        #Get the allocation bitmap from the $Bitmap file
        bitmap_record = self.ntfs.get_record(6)
        bitmap = self.ntfs.get_data(6)

        #Get the runs already allocated
        runs = self.ntfs.get_data_runs(bitmap_record)
        #Shorten the bitmap to only the actual bitmap
        #TODO Only read the first run in the frist place
        bitmap = bitmap[:runs[0]['length']]

        #Search for the requested amount of unallocated clusters
        new_runs = []
        clusters_found = []
        cluster_pos = 0

        #Go through every bit of the bitmap
        for byte in bitmap:
            for position in range(8):
                bit = (byte >> position) & 1
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

        assert len(clusters_found) == n, "Not enough free clusters found"
        self.write_cluster_allocation(clusters_found)
        #TODO Return the new runs


    def write_cluster_allocation(self, clusters: []):

        offset = self.ntfs.start_offset
        bitmap_record = self.ntfs.get_record(6)
        offset += self.ntfs.get_data_runs(bitmap_record)[0]['offset']

        for cluster in clusters:
            position = int(cluster/8)

            self.stream.seek(offset + position)
            old_value = self.stream.read(1)
            new_value = old_value | (1 << (cluster % 8))
            self.stream.seek(-1, 1)
            self.stream.write(new_value)


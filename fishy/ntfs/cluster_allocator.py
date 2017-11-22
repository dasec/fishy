"""
Implementation for allocation of additional
data runs for a file to hide data in
"""

import typing
from .ntfs_filesystem.ntfs import NTFS


class AllocatorMetadata:

    def __init__(self):
        self.file = None
        self.original_runs = []
        self.new_runs = []


class ClusterAllocator:

    def __init__(self, stream: typing.BinaryIO):
        self.stream = stream
        self.ntfs = NTFS(stream)


    def allocate_clusters(self, n: int) -> [{'lenght', 'offset'}]:

        bitmap_record = self.ntfs.get_record(6)
        bitmap = self.ntfs.get_data(6)

        runs = self.ntfs.get_data_runs(bitmap_record)
        new_runs = []
        clusters_found = []
        cluster_pos = 0

        for byte in bitmap:
            for position in range(8):
                bit = (byte >> position) & 1
                if bit == 0:
                    clusters_found.append(cluster_pos+position)
                    if len(clusters_found) == n:
                        break

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


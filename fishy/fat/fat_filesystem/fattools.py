"""
FATtools implements some common operations on
FAT filesystems.
"""


class FATtools:
    """
    FATtools implements some common inspection operations on
    FAT filesystems.
    """
    def __init__(self, fat):
        """
        :param fat: FAT filesystem object
        """
        self.fat = fat

    def list_directory(self, cluster_id=0):
        """
        list directory entries
        :param cluster_id: id of cluster that contains the
                           directory. If cluster_id == 0
                           then the root directory is listed
        """
        if cluster_id == 0:
            dir_iterator = self.fat.get_root_dir_entries()
        else:
            dir_iterator = self.fat.get_dir_entries(cluster_id)
        for entry in dir_iterator:
            # get correct filetype
            if entry.is_dir():
                filetype = 'd'
            else:
                filetype = 'f'
            # check if file is marked as deleted
            if entry.is_deleted():
                deleted = 'd'
            else:
                deleted = ' '
            # check if it is a dot entry
            if entry.is_dot_entry():
                dot = '.'
            else:
                dot = ' '
            print(filetype, deleted, dot,
                    str(entry.get_start_cluster()).ljust(8),
                    str(entry.get_filesize()).ljust(8),
                    entry.get_name()
                 )

    def list_fat(self):
        """
        list all fat entries
        """
        for i in range(self.fat.entries_per_fat):
            print(i, self.fat.get_cluster_value(i))

    def list_info(self):
        """
        shows some info about the FAT filesystem
        """
        # get FAT Type:
        fat_type = self.fat.pre.fs_type.decode('ascii').strip()
        print('FAT Type:'.ljust(42),
              fat_type)
        # Sector Size
        print('Sector Size:'.ljust(42),
              self.fat.pre.sector_size)
        # secors per cluster
        print('Sectors per Cluster:'.ljust(42),
              self.fat.pre.sectors_per_cluster)
        # sectors per fat
        print('Sectors per FAT:'.ljust(42),
              self.fat.pre.sectors_per_fat)
        # fat count
        print('FAT Count:'.ljust(42),
              self.fat.pre.fat_count)
        # Start of dataregion
        print('Dataregion Start Byte:'.ljust(42),
              self.fat.start_dataregion)
        # FAT32 specific
        if fat_type == 'FAT32':
            print("Free Data Clusters (FS Info):".ljust(42),
                  self.fat.pre.free_data_cluster_count)
            print("Recently Allocated Data Cluster (FS Info):".ljust(42),
                  self.fat.pre.last_allocated_data_cluster)
            print("Root Directory Cluster:".ljust(42),
                  self.fat.pre.rootdir_cluster)
            print("FAT Mirrored:".ljust(42),
                  self.fat.pre.flags.mirrored)
            print("Active FAT:".ljust(42),
                  self.fat.pre.flags.active_fat)
            print("Sector of Bootsector Copy:".ljust(42),
                  self.fat.pre.bootsector_copy_sector)

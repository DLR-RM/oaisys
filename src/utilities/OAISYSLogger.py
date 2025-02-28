import csv
import os
import pathlib


class OAISYSLogger:
    """docstring for OAISYSLogger"""

    def __init__(self, output_path=None):
        self.logger = None
        self.logging_handles = {}
        self.log_dir_created = False
        if output_path is not None:
            self.output_path = output_path

    def reset(self):
        self.logger = None
        self.logging_handles = {}
        self.log_dir_created = False
        self.output_path = None

    def set_output_path(self, output_path):
        self.output_path = output_path

    def create_log_dir(self, path):
        """ create log folder
        Args:
            path:                   path to log folder [str]
        Returns:
            None
        """
        self.log_dir_created = True
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    def log_pose(self, identifier, value, file_name=None):
        """ log pose to csv
        Args:
            identifier:             identifier on which data has to be logged [dict]
            value:                  value, which has to be logged (x, y, z, qw, qx, qy, qz) [array]
            file_name:              name of file, where data is stored. By default, this parameter will be equal as the
                                    identifier [str]
        Returns:
            None
        """
        # check if log folder exist
        if self.log_dir_created is False:
            self.create_log_dir(path=self.output_path)

        # set file_name if not done yet
        if file_name is None:
            file_name = identifier

        # store identifier information and set write mode
        if identifier not in self.logging_handles:
            self.logging_handles[identifier] = os.path.join(self.output_path, file_name + ".csv")
            writer_mode = 'w'
        else:
            writer_mode = 'a'

        # create(w)/open(a) csv file and store pose data
        with open(self.logging_handles[identifier], mode=writer_mode, newline='') as file:
            for v in value:
                file.write(str(v) + ', ')
            file.write('\n')

    def log_scalar(self, identifier, value, file_name=None):
        """ log scalar value to file
        Args:
            identifier:             identifier on which data has to be logged [dict]
            value:                  value, which has to be logged [?]
            file_name:              name of file, where data is stored. By default, this parameter will be equal as the
                                    identifier [str]
        Returns:
            None
        """
        # check if log folder exist
        if self.log_dir_created is False:
            self.create_log_dir(path=self.output_path)

        # set file_name if not done yet
        if file_name is None:
            file_name = identifier

        # store identifier information and set write mode
        if identifier not in self.logging_handles:
            self.logging_handles[identifier] = os.path.join(self.output_path, file_name + ".csv")
            writer_mode = 'w'
        else:
            writer_mode = 'a'

        # create(w)/open(a) csv file and store scalar
        with open(self.logging_handles[identifier], mode=writer_mode, newline='') as file:
            file.write(str(value) + ', ')
            file.write('\n')

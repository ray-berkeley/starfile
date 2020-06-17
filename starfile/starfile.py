from pathlib import Path
from linecache import getline
from typing import Tuple, List

import pandas as pd


class StarFile:
    def __init__(self, filename: str, data: dict = None):
        self.filename = Path(filename)
        self.dataframes = []

        # if self.filename.exists():
        #     self._read_file()
        #
        # if data is not None:
        #     df = pd.DataFrame(data)
        #     self.dataframes.append()

    @property
    def dataframes(self):
        return self._dataframes

    @dataframes.setter
    def dataframes(self, dataframes: List[pd.DataFrame]):
        self._dataframes = dataframes

    @property
    def n_lines(self):
        if self.filename.exists():

            with open(self.filename, 'r') as f:
                n = sum(1 for line in f)
            return n

        else:
            return None

    @property
    def data_block_starts(self):
        """
        Return a list of indices in which line.strip() == 'data_'
        :return:
        """
        data_block_starts = []
        with open(self.filename) as file:
            for idx, line in enumerate(file, 1):
                if line.strip().startswith('data_'):
                    data_block_starts.append(idx)

        if len(data_block_starts) == 0:
            raise ValueError(f"File with name '{self.filename}' has no valid STAR data blocks")
        return data_block_starts

    @property
    def n_data_blocks(self):
        """
        Count the number of data blocks in the file
        :return:
        """
        n_data_blocks = len(self.data_block_starts)
        return n_data_blocks

    def _read_file(self):
        n_lines = self.n_lines
        data_block_starts = self.data_block_starts
        starts_ends = self._starts_ends(data_block_starts, n_lines)
        dataframes = []

        for data_block_start, data_block_end in starts_ends:
            df = self._read_data_block(data_block_start, data_block_end)
            dataframes.append(df)

        self.dataframes = dataframes

    def _read_data_block(self, data_block_start: int, data_block_end: int):
        line_number = data_block_start
        current_line = self._get_line(line_number)

        if not current_line.startswith('data_'):
            raise ValueError(f'Cannot start reading loop from line which does not indicate start of data block')

        data_block_name = current_line[5:]

        data_block = []
        line_number += 1

        for line_number in range(line_number, data_block_end):
            current_line = self._get_line(line_number)

            if current_line.startswith('loop_'):
                data_block = self._read_loop_block(line_number, data_block_end)
                return data_block
            else:
                data_block.append(current_line)

        data_block = self._data_block_clean(data_block, data_block_name)
        return data_block

    def _read_loop_block(self, start_line_number: int, end_line_number: int):
        header, data_block_start = self._read_loop_header(start_line_number)
        df = self._read_loop_data(data_block_start, end_line_number)
        df.columns = header
        return df

    def _read_loop_data(self, start_line_number: int, end_line_number: int = None) -> pd.DataFrame:
        header_length = start_line_number - 1
        if end_line_number is None:
            df = pd.read_csv(self.filename, skiprows=header_length, delim_whitespace=True, header=None)
        else:
            footer_length = self.n_lines - end_line_number
            df = pd.read_csv(self.filename, skiprows=header_length, skipfooter=footer_length, delim_whitespace=True,
                             header=None, engine='python')
        return df

    def _read_loop_header(self, start_line_number: int) -> Tuple[list, int]:
        """

        :param start_line_number: line number (1-indexed) with loop_ entry
        :return:
        """
        loop_header = []
        line_number = start_line_number

        # Check that loop header starts with loop
        line = getline(str(self.filename), line_number).strip()
        if not line.startswith('loop_'):
            raise ValueError(f'Cannot start reading loop from line which does not indicate start of loop block')

        # Advance then iterate over lines while in loop header
        line_number +=1
        line = self._get_line(line_number)

        while line.startswith('_'):
            if line.startswith('_'):
                line = line.split()[0][1:]  # Removes leading '_' and numbers in loopheader if present
                loop_header.append(line)
                line_number += 1
            line = self._get_line(line_number)

        data_block_start = line_number
        return loop_header, data_block_start

    def _get_line(self, line_number: int):
        return getline(str(self.filename), line_number).strip()

    def _starts_ends(self, data_block_starts, n_lines):
        """
        tuple of start and end line numbers
        :return:
        """
        starts_ends = [(start, end - 1) for start, end in zip(data_block_starts, data_block_starts[1:])]
        starts_ends.append((data_block_starts[-1], n_lines))
        return starts_ends

    def _data_block_clean(self, data_block, data_block_name):
        """
        Make a pandas dataframe from the names and info in a data block from a star file in a list of lists
        :param data_block:
        :return:
        """
        data_clean = {}
        for line in data_block:

            if line == '':
                continue

            name_and_data = line.split()
            key = name_and_data[0][1:]
            value = name_and_data[1]

            data_clean[key] = value

        df = pd.DataFrame(data_clean, index=['value'])
        df.name = data_block_name
        return df




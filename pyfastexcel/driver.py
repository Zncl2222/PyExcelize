from __future__ import annotations

import base64
import ctypes
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import msgspec
from openpyxl import load_workbook
from openpyxl_style_writer import CustomStyle

from .style import StyleManager
from .worksheet import WorkSheet

BASE_DIR = Path(__file__).resolve().parent


class ExcelDriver:
    """
    A driver class to write data to Excel files using custom styles.

    ### Attributes:
        _FILE_PROPS (dict[str, str]): Default file properties for the Excel
        file.
        _PROTECT_ALGORITHM (tuple[str]): Algorithm for the workbook protection

    ### Methods:
        __init__(): Initializes the ExcelDriver.
        _read_lib(lib_path: str): Reads a library for Excel manipulation.
        read_lib_and_create_excel(lib_path: str = None): Reads the library and
                creates the Excel file.
    """

    _FILE_PROPS = {
        'Category': '',
        'ContentStatus': '',
        'Created': '',
        'Creator': 'pyfastexcel',
        'Description': '',
        'Identifier': 'xlsx',
        'Keywords': 'spreadsheet',
        'LastModifiedBy': 'pyfastexcel',
        'Modified': '',
        'Revision': '0',
        'Subject': '',
        'Title': '',
        'Language': 'en-Us',
        'Version': '',
    }
    _PROTECT_ALGORITHM = (
        'XOR',
        'MD4',
        'MD5',
        'SHA-1',
        'SHA-256',
        'SHA-384',
        'SHA-512',
    )

    def __init__(self, pre_allocate: dict[str, int] = None, plain_data: list[list[str]] = None):
        """
        Initializes the Workbook with default settings and initializes Sheet1.

        It initializes the workbook structure with Sheet1 as the default sheet,
        sets default file properties, initializes current sheet and sheet list,
        and initializes dictionaries for workbook and protection settings.

        Args:
            pre_allocate (dict[str, int], optional): A dictionary containing 'n_rows' and 'n_cols'
                keys specifying the dimensions for pre-allocating data in Sheet1.
            plain_data (list[list[str]], optional): A 2D list of strings representing initial data
                to populate Sheet1.
        """
        self.workbook = {
            'Sheet1': WorkSheet(pre_allocate=pre_allocate, plain_data=plain_data),
        }
        self.file_props = self._get_default_file_props()
        self.sheet = 'Sheet1'
        self._sheet_list = tuple(['Sheet1'])
        self._dict_wb = {}
        self.protection = {}
        self.style = StyleManager()

    @property
    def sheet_list(self):
        return self._sheet_list

    def save(self, path: str = './pyfastexcel.xlsx') -> None:
        if not hasattr(self, 'decoded_bytes'):
            self.read_lib_and_create_excel()

        with open(path, 'wb') as file:
            file.write(self.decoded_bytes)

    def __getitem__(self, key: str) -> WorkSheet:
        return self.workbook[key]

    def _check_if_sheet_exists(self, sheet_name: str) -> None:
        if sheet_name not in self.sheet_list:
            raise KeyError(f'{sheet_name} Sheet Does Not Exist.')

    def read_lib_and_create_excel(self, lib_path: str = None) -> bytes:
        """
        Reads the library and creates the Excel file.

        Args:
            lib_path (str, optional): The path to the library. Defaults to None.

        Returns:
            bytes: The byte data of the created Excel file.
        """
        pyfastexcel = self._read_lib(lib_path)
        self._create_style()

        # Transfer all WorkSheet Object to the sheet dictionary in the workbook.
        set_group_columns = False
        set_row_columns = False
        use_openpyxl = False
        for sheet in self._sheet_list:
            self._dict_wb[sheet] = self.workbook[sheet]._transfer_to_dict()
            if self.workbook[sheet].engine == 'openpyxl':
                use_openpyxl = True
            if len(self.workbook[sheet].grouped_columns) != 0:
                set_group_columns = True
            if len(self.workbook[sheet].grouped_rows) != 0:
                set_row_columns = True

        # Set writer (if some of the function that excelize StremWriter is not support, and
        # system will use normal writer to write the excel)
        if (set_group_columns or set_row_columns) and use_openpyxl is False:
            engine = 'normalWriter'
        else:
            engine = 'streamWriter'

        results = {
            'content': self._dict_wb,
            'file_props': self.file_props,
            'style': self.style._style_map,
            'protection': self.protection,
            'engine': engine,
        }
        json_data = msgspec.json.encode(results)
        create_excel = pyfastexcel.Export
        free_pointer = pyfastexcel.FreeCPointer
        free_pointer.argtypes = [ctypes.c_void_p]
        create_excel.argtypes = [ctypes.c_char_p]
        create_excel.restype = ctypes.c_void_p
        byte_data = create_excel(json_data)
        self.decoded_bytes = base64.b64decode(ctypes.cast(byte_data, ctypes.c_char_p).value)
        free_pointer(byte_data)
        StyleManager.reset_style_configs()

        # Due to Streaming API of Excelize can't group column currently
        # So implement this function by openpyxl
        if (set_group_columns or set_row_columns) and use_openpyxl is True:
            self.decoded_bytes = self._set_group_columns_and_group_rows()

        return self.decoded_bytes

    def _set_group_columns_and_group_rows(self):
        wb = load_workbook(BytesIO(self.decoded_bytes))
        for sheet in self._sheet_list:
            grouped_columns = self.workbook[sheet].grouped_columns
            ws = wb[sheet]
            for col in grouped_columns:
                ws.column_dimensions.group(
                    col['start_col'],
                    col['end_col'],
                    outline_level=col['outline_level'],
                    hidden=col['hidden'],
                )
            grouped_rows = self.workbook[sheet].grouped_rows
            for row in grouped_rows:
                ws.row_dimensions.group(
                    row['start_row'],
                    row['end_row'],
                    outline_level=row['outline_level'],
                    hidden=row['hidden'],
                )

        # Save the workbook to a BytesIO stream
        excel_stream = BytesIO()
        wb.save(excel_stream)
        decoded_bytes = excel_stream.getvalue()
        excel_stream.close()
        return decoded_bytes

    def _read_lib(self, lib_path: str) -> ctypes.CDLL:
        """
        Reads a shared-library for writing Excel.

        Args:
            lib_path (str): The path to the library.

        Returns:
            ctypes.CDLL: The library object.
        """
        if lib_path is None:
            if sys.platform.startswith('linux'):
                lib_path = str(list(BASE_DIR.glob('**/*.so'))[0])
            elif sys.platform.startswith('win32'):
                lib_path = str(list(BASE_DIR.glob('**/*.dll'))[0])
        lib = ctypes.CDLL(lib_path, winmode=0)
        return lib

    def _get_default_file_props(self) -> dict[str, str]:
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        file_props = self._FILE_PROPS.copy()
        file_props['Created'] = now
        file_props['Modified'] = now
        return file_props

    def _get_style_collections(self) -> dict[str, CustomStyle]:
        """
        Gets collections of custom styles.

        Returns:
            dict[str, CustomStyle]: A dictionary containing custom style
                collections.
        """
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not callable(getattr(self, attr)) and isinstance(getattr(self, attr), CustomStyle)
        }

    def _create_style(self) -> None:
        """
        Creates custom styles for the Excel file.

        This method initializes custom styles for the Excel file based on
        predefined attributes.
        """
        style_collections = self._get_style_collections()
        self.style._STYLE_NAME_MAP.update({val: key for key, val in style_collections.items()})

        # Set the CustomStyle from the pre-defined class attributes.
        for key, val in style_collections.items():
            self.style._update_style_map(key, val)

        # Set the CustomStyle from the REGISTERED method.
        for key, val in self.style.REGISTERED_STYLES.items():
            self.style._update_style_map(key, val)

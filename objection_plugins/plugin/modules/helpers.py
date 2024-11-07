from objection.state.connection import state_connection
from objection.commands import filemanager
from dataclasses import dataclass
from frida.core import RPCException
from .mydatabases import Row
import sqlite3
import shutil
import ntpath
import os
import contextlib
import sys
import io


MAX_VALUE_LENGTH = 16


@dataclass
class AppData:
    api: state_connection.api
    application_db_path: str = ""
    application_root_path: str = ""


@dataclass
class Helpers:
    app_data: AppData

    def get_file_name(self, path: str) -> str:
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    @contextlib.contextmanager
    def nostdout(self):
        save_stdout = sys.stdout
        sys.stdout = io.BytesIO()
        yield
        sys.stdout = save_stdout

    def download_database_file(self, src: str, dst: str) -> None:
        with self.nostdout():
            filemanager.download([src, dst])
        # filemanager.download([src, dst])

    def copy_database(self, file_path: str) -> str:
        temp_path = os.path.join(
            "copied_databases", self.get_file_name(file_path) + ".copy")

        shutil.copy2(file_path, temp_path)
        return temp_path

    def copy_updated_database(self, file_path: str) -> None:
        temp_path = os.path.join(
            "copied_databases", self.get_file_name(file_path) + ".copy")

        if os.path.isfile(file_path + "-wal_tmp"):
            shutil.copy2(file_path + "-wal_tmp", file_path + "-wal")
            os.remove(file_path + "-wal_tmp")
            shutil.copy2(file_path + "-wal", temp_path + "-wal")
        else:
            shutil.copy2(file_path, temp_path)

        sql_conn = sqlite3.connect(temp_path)
        sql_conn.close()

    def get_value_return_str(
        self,
        active_db_tables: list,
        copied_db_tables: list,
        table: str,
        row: int,
        column: str,
    ) -> str:
        path = os.path.join("blob_data", f"{table}_{row}_{column}")
        result = f" BLOB value: '{os.path.join('.', path, 'original.bin')}' -> '{os.path.join('.', path, 'active.bin')}'"

        active_table = next(
            (t for t in active_db_tables if t.table_name == table), None
        )
        copied_table = next(
            (t for t in copied_db_tables if t.table_name == table), None
        )

        if not active_table or not copied_table:
            return result

        active_row = next(
            (r for r in active_table.rows if r.row_value == str(row)), None
        )
        copied_row = next(
            (r for r in copied_table.rows if r.row_value == str(row)), None
        )

        if not active_row or not copied_row:
            return result

        active_column = next(
            (c for c in active_row.columns if c.column_name == column), None
        )
        copied_column = next(
            (c for c in copied_row.columns if c.column_name == column), None
        )

        if not active_column or not copied_column:
            return result

        active_value = active_column.value
        copied_value = copied_column.value

        if (isinstance(active_value, (str, int)) or active_value is None) and (
            isinstance(copied_value, (str, int)) or copied_value is None
        ):
            result = f": '{self.get_value(copied_value)}' -> '{self.get_value(active_value)}'"
        else:
            os.makedirs(path, exist_ok=True)
            if copied_value is None:
                copied_value = b"NULL"
            if active_value is None:
                active_value = b"NULL"
            with open(os.path.join(path, "original.bin"), "wb") as fp:
                fp.write(copied_value)
            with open(os.path.join(path, "active.bin"), "wb") as fp:
                fp.write(active_value)

        return result

    def get_value(self, value):
        value_str = str(value)
        if len(value_str) > MAX_VALUE_LENGTH:
            return f"{value_str[:MAX_VALUE_LENGTH]}..."
        else:
            return value_str

    def get_value_in_row(self, value_row: Row) -> dict:
        value_dict = {}
        for column in value_row.columns:
            value_dict[column.column_name] = self.get_value(column.value)

        return value_dict

    def get_databases(self) -> list:
        database_name_list = []
        ls_data = self.get_ls_data(self.app_data.application_db_path)[0]
        for file_name in ls_data["files"].keys():
            if file_name.endswith(".db"):
                database_name_list.append(file_name)
        return database_name_list

    def get_ls_data(self, path: str) -> tuple[dict, str]:
        try:
            ls_data = self.app_data.api.android_file_ls(path)
            dir_name = "isDirectory"
        except RPCException:
            ls_data = self.app_data.api.ios_file_ls(path)
            dir_name = "NSFileType"

        return ls_data, dir_name

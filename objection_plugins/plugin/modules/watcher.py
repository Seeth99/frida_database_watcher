from dataclasses import dataclass
from .helpers import Helpers, AppData, RPCException
from .mydatabases import Database
import time
import shutil
import os


@dataclass
class MyWatcher:
    dbs_tables_dict: dict
    app_data: AppData

    # @contextlib.contextmanager
    # def nostdout(self):
    #     save_stdout = sys.stdout
    #     sys.stdout = io.BytesIO()
    #     yield
    #     sys.stdout = save_stdout

    # def download_database_file(self, src: str, dst: str) -> None:
    #     with self.nostdout():
    #         filemanager.download([src, dst])
    #     # filemanager.download([src, dst])

    def get_timestamp(self, database_name: str) -> str:
        ls_data = Helpers(self.app_data).get_ls_data(
            self.app_data.application_db_path)[0]
        try:
            try:
                return ls_data["files"][f"{database_name}-wal"]["attributes"]["lastModified"]
            except KeyError:
                return ls_data["files"][f"{database_name}-wal"]["attributes"]["NSFileModificationDate"]
        except KeyError:
            try:
                return ls_data["files"][f"{database_name}"]["attributes"]["lastModified"]
            except KeyError:
                return ls_data["files"][f"{database_name}"]["attributes"]["NSFileModificationDate"]

    def generate_dicts(self, database_name_list: list, copy: bool) -> dict:
        database_dict: dict = {}
        for database_name in database_name_list:
            active_db_path = os.path.join("active_databases", database_name)
            database_dict[database_name] = {"active_db_path": active_db_path}

            # Helpers(self.app_data).download_database_file(
            #     os.path.join(
            #         self.app_data.application_db_path, database_name
            #     ).replace("\\", "/"),
            #     active_db_path,
            # )

            if copy:
                database_dict[database_name]["copied_db_path"] = Helpers(
                    self.app_data
                ).copy_database(active_db_path)
            else:
                database_dict[database_name][
                    "copied_db_path"
                ] = os.path.join("copied_databases", f"{database_name}.copy")

            # Get the last modified timestamp
            database_dict[database_name]["timestamp"] = self.get_timestamp(
                database_name)

            # # Get blacklisted tables
            # database_dict[database_name]["black_tables"] = self.dbs_tables_dict[database_name]

        return database_dict

    def run_watcher(self, database_name_list: list, database_dict: dict) -> None:
        # TODO Fix this Ghetto watchdog
        print(f"\nStarted monitoring {database_name_list}\n")
        while True:
            for database_name in database_name_list:
                updated_timestamp = self.get_timestamp(database_name)
                if database_dict[database_name]["timestamp"] == updated_timestamp:
                    continue

                # If the timestamp was updated
                self.timestamp_was_updated(database_name, database_dict)

                # Update timestamp variable
                database_dict[database_name]["timestamp"] = updated_timestamp
            time.sleep(1)

    def run_startup(self) -> None:
        database_name_list = list(self.dbs_tables_dict.keys())
        database_dict = self.generate_dicts(database_name_list, True)

        if not database_dict:
            return

        print(f"\nChanges made to {database_name_list} since last session\n")
        for database_name in database_name_list:
            self.timestamp_was_updated(database_name, database_dict)

            # Update timestamp variable
            database_dict[database_name]["timestamp"] = self.get_timestamp(
                database_name)

        # Start watcher for live updates
        self.run_watcher(database_name_list, database_dict)

    def timestamp_was_updated(self, database_name: str, database_dict: dict):
        src_path = os.path.join(
            self.app_data.application_db_path, database_name).replace("\\", "/")
        dst_path = os.path.join(f"active_databases", database_name)

        Helpers(self.app_data).download_database_file(
            src_path+"-wal", dst_path+"-wal")

        if os.path.isfile(dst_path+"-wal"):
            tmp_path = os.path.join(
                f"active_databases", f"{database_name}-wal_tmp")
            shutil.copy2(dst_path+"-wal", tmp_path)
        else:
            Helpers(self.app_data).download_database_file(src_path, dst_path)

        self.compare_databases(
            Database(
                database_dict[database_name]["active_db_path"],
                database_name,
                self.dbs_tables_dict[database_name],
            ),
            Database(
                database_dict[database_name]["copied_db_path"],
                database_name,
                self.dbs_tables_dict[database_name],
            ),
        )

        # Update the copied database
        Helpers(self.app_data).copy_updated_database(
            database_dict[database_name]["active_db_path"]
        )

    def compare_databases(self, active_db: Database, copied_db: Database) -> None:
        active_db.fill_database_data()
        copied_db.fill_database_data()

        for copied_table in copied_db.tables:
            active_table = next(
                (
                    t
                    for t in active_db.tables
                    if t.table_name == copied_table.table_name
                ),
                None,
            )

            # Find deleted tables
            # TODO Needed?
            if not active_table:
                print(
                    f"\033[91m[-] Database: {copied_db.database_name}, Table: {copied_table.table_name}, Table deleted.\n\033[0m"
                )
                continue

            # Find deleted rows
            for copied_row in copied_table.rows:
                active_row = next(
                    (
                        r
                        for r in active_table.rows
                        if r.row_value == copied_row.row_value
                    ),
                    None,
                )
                if not active_row:
                    result = Helpers(
                        self.app_data).get_value_in_row(copied_row)
                    print(
                        f"\033[91m[-] Database: {copied_db.database_name}, Table: {copied_table.table_name}, Row: {copied_row.row_value} deleted: {result}\n\033[0m"
                    )
                    continue
                # Compare column values within the row
                for copied_column in copied_row.columns:
                    active_column = next(
                        (
                            c
                            for c in active_row.columns
                            if c.column_name == copied_column.column_name
                        ),
                        None,
                    )
                    # Find deleted column
                    # TODO Needed?
                    if not active_column:
                        print(
                            f"\033[91m[-] Database: {copied_db.database_name}, Table: {copied_table.table_name}, Row: {copied_row.row_value}, Column: {copied_column.column_name} deleted.\n\033[0m"
                        )
                    elif copied_column.value != active_column.value:
                        result = Helpers(self.app_data).get_value_return_str(
                            active_db.tables,
                            copied_db.tables,
                            active_table.table_name,
                            active_row.row_value,
                            active_column.column_name,
                        )
                        print(
                            f"\033[93m[^] Database: {copied_db.database_name}, Table: {copied_table.table_name}, Row: {copied_row.row_value}, Column: {copied_column.column_name} changed{result}\n\033[0m"
                        )  # : '{copied_column.value}' -> '{active_column.value}'

            # Find added rows
            # TODO Added tables and columns???
            for active_row in active_table.rows:
                copied_row = next(
                    (
                        r
                        for r in copied_table.rows
                        if r.row_value == active_row.row_value
                    ),
                    None,
                )
                if not copied_row:
                    result = Helpers(
                        self.app_data).get_value_in_row(active_row)
                    print(
                        f"\033[92m[+] Database: {active_db.database_name}, Table: {active_table.table_name}, Row: {active_row.row_value} added: {result}\n\033[0m"
                    )

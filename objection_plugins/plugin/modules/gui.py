from dataclasses import dataclass, field
from .watcher import MyWatcher
from .helpers import Helpers, AppData
from .scan_db import ScanDB
from .mydatabases import Database
import PySimpleGUI as sg
import shutil
import os
import time


@dataclass
class Gui:
    app_data: AppData
    db_list: list = field(default_factory=list)
    dir_list: list = field(default_factory=list)
    selected_db_dict: dict = field(default_factory=dict[str, list])

    def __post_init__(self):
        self.dir_list = ScanDB(self.app_data).scan()

    def start_gui(self) -> list:
        window = sg.Window("Database Auto", self.directory_layout())

        while True:
            event, values = window.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                window.close()
                return

            elif event == "dir_next":
                self.remove_old_files()
                if not self.app_data.application_db_path:
                    self.app_data.application_db_path = self.get_selected_dir(
                        values)

                if self.app_data.application_db_path:
                    window.close()
                    window = sg.Window(
                        "Database Auto", self.databases_layout())

            elif event == "db_next":
                for db_name in self.db_list:
                    if values[db_name]:
                        self.selected_db_dict.update({db_name: []})

                window.close()
                window = sg.Window(
                    "Database Auto", self.tables_layout())

            elif event == "BackToDir":
                self.app_data.application_db_path = None
                self.db_list.clear()
                window.close()
                window = sg.Window("Database Auto", self.directory_layout())

            elif event == "BackToDb":
                self.selected_db_dict.clear()
                window.close()
                window = sg.Window("Database Auto", self.databases_layout())

            elif event == "Start":
                self.get_selected_dbs_and_tables(values)
                window.close()
                break

        # Start watcher
        print(self.selected_db_dict)
        if self.selected_db_dict:
            MyWatcher(self.selected_db_dict,
                      self.app_data).run_startup()

    def directory_layout(self) -> list:
        # TODO Change to checkboxes
        # Create a list of radio buttons for directories.
        directory_radio_buttons = [
            [
                sg.Radio(directory, "directory_radio",
                         key=directory, default=False)
            ]
            for directory in self.dir_list
        ]

        # Layout for the initial directory selection.
        initial_layout = [
            [sg.Text("Select a database directory:")],
            *directory_radio_buttons,
            [
                # sg.Button("Exit", size=(10, 0)),
                sg.Push(),
                sg.Button("Next", size=(10, 0), key="dir_next"),
            ],
        ]
        return initial_layout

    def databases_layout(self) -> list:
        # Get the files with .db extension
        if not self.db_list:
            self.db_list = Helpers(self.app_data).get_databases()

        checkboxes = [
            [
                [
                    sg.Checkbox(text=db_name, default=False,
                                key=db_name, size=(30, 0)),
                ]
                for db_name in self.db_list
            ],
        ]

        layout = [
            [checkboxes],
            [
                # sg.Button("Exit", size=(10, 0)),
                sg.Push(),
                sg.Button("Back", size=(10, 0), key="BackToDir"),
                sg.Button("Next", size=(10, 0), key="db_next"),
            ],
        ]
        return layout

    def tables_layout(self) -> list:
        # TODO If already set
        table_dict = self.get_tables()

        # Create a list to hold the layout for each column
        columns = []
        for db_name in table_dict:
            column_data = [
                [sg.Text(db_name + ":", font=("Arial", 12, "bold"))]
            ]
            for table_name in table_dict[db_name]:
                column_data.append(
                    [sg.Checkbox(text=table_name, default=False, key=db_name + "-" + table_name, size=(30, 0))])

            columns.append(column_data)

        # Combine the columns into a single layout using sg.Column elements
        layout = [
            [
                sg.Column(columns[i], scrollable=True,
                          vertical_scroll_only=True, justification="left", size=(None, 400))
                for i in range(len(columns))
            ],
            [
                # sg.Button("Exit", size=(10, 0)),
                sg.Push(),
                sg.Button("Back", size=(10, 0), key="BackToDb"),
                sg.Button("Start", size=(10, 0), key="Start"),
            ],
        ]
        return layout

    def get_selected_dir(self, values: dict) -> str:
        # Get the selected directory from radio buttons.
        for directory in values:
            if values[directory]:
                return directory

    def remove_old_files(self) -> None:
        shutil.rmtree("active_databases", ignore_errors=True)
        shutil.rmtree("copied_databases", ignore_errors=True)
        shutil.rmtree("blob_data", ignore_errors=True)

    def get_tables(self) -> dict:
        # Directories for storing the .db files
        os.makedirs("active_databases", exist_ok=True)
        os.makedirs("copied_databases", exist_ok=True)

        table_dict = {}
        for db_name in self.selected_db_dict.keys():
            src_path = os.path.join(self.app_data.application_db_path,
                                    db_name).replace("\\", "/")
            dst_path = os.path.join("active_databases", db_name)
            Helpers(self.app_data).download_database_file(src_path, dst_path)
            time.sleep(1)  # BUG Dies here on ios
            Helpers(self.app_data).download_database_file(
                src_path+"-wal", dst_path+"-wal")

            table_dict[db_name] = Database(dst_path, db_name).get_tables()

        return table_dict

    def get_selected_dbs_and_tables(self, values: dict) -> None:
        # TODO merge into one for-loop
        for value in values:
            if values[value]:
                splitted_value = value.split("-", 1)
                db_name = splitted_value[0]
                table_name = splitted_value[1]
                self.selected_db_dict[db_name].append(table_name)

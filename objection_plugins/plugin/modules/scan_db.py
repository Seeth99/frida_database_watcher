from dataclasses import dataclass, field
from objection.state.connection import state_connection
from .helpers import Helpers, AppData, RPCException


@dataclass
class ScanDB:
    app_data: AppData
    dir_list: list = field(default_factory=list)

    def contains_database(self, path: str) -> bool:
        ls_data, dir_name = Helpers(self.app_data).get_ls_data(path)

        for content in ls_data["files"]:
            is_directory = ls_data["files"][content]["attributes"][dir_name]
            if is_directory == True or is_directory == "NSFileTypeDirectory":
                continue

            file_name = ls_data["files"][content]["fileName"]
            if file_name.endswith(".db"):
                return True

        return False

    def find_directories(self, path: str) -> None:
        ls_data, dir_name = Helpers(self.app_data).get_ls_data(path)

        if self.contains_database(path):
            self.dir_list.append(path)

        for content in ls_data["files"]:
            is_directory = ls_data["files"][content]["attributes"][dir_name]
            if is_directory == False or is_directory == "NSFileTypeRegular":
                continue

            subdir_name = ls_data["files"][content]["fileName"]
            self.find_directories(path + "/" + subdir_name)

    def scan(self) -> list:
        self.find_directories(self.app_data.application_root_path)
        return self.dir_list

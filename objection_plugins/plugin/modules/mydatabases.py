from dataclasses import dataclass, field
import sqlite3


@dataclass
class Column:
    column_name: str
    value: str | int | bytes


@dataclass
class Row:
    row_value: str
    columns: list[Column]


@dataclass
class Table:
    table_name: str
    rows: list[Row]


@dataclass
class Database:
    db_path: str
    database_name: str
    whitelisted_tables: list = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    def __post_init__(self):
        self.sql_conn = sqlite3.connect(self.db_path)
        self.cursor = self.sql_conn.cursor()  # cursor: sqlite3.Cursor

    def get_tables(self) -> list:
        try:
            found_tables = self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
            table_list = []
            for table in found_tables:
                table_list.append(table[0])
            return table_list

        except sqlite3.Error as error:
            print("Failed to fetch database tables", error)
            exit()

    def fill_database_data(self) -> None:
        try:
            for table_name in self.get_tables():
                if table_name not in self.whitelisted_tables:
                    continue
                table_data = self.cursor.execute(
                    f"SELECT * FROM {table_name};")
                columns = [
                    Column(column[0], None) for column in table_data.description
                ]

                rows = self.cursor.execute(
                    f"SELECT ROWID,* FROM {table_name};"
                ).fetchall()
                table_rows = []
                for row in rows:
                    primary_key = row[0]
                    row_values = row[1:]
                    row_columns = [
                        Column(column.column_name, value)
                        for column, value in zip(columns, row_values)
                    ]
                    table_rows.append(Row(str(primary_key), row_columns))

                self.tables.append(Table(table_name, table_rows))
            self.sql_conn.close()

        except sqlite3.Error as error:
            print("Failed to fetch database data", error)
            exit()

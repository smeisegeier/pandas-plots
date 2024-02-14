from typing import Literal

from sqlalchemy import create_engine, text
from sqlalchemy_utils import create_database, database_exists


def connect_sql(
    db: str,
    host: str = '',
    user: str = '',
    pw: str = '',
    dbms: Literal['mssql', 'sqlite','postgres'] = 'mssql',
    ensure_db_exists: bool = False,
    ) -> object:
    """
    Connects to any SQL database based on the given parameters.

    Args:
        db (str): The name of the database / sqlite-file.
        host (str, optional): The host name or IP address of the database server. Defaults to an empty string.
        user (str, optional): The username for authentication. Defaults to an empty string.
        pw (str, optional): The password for authentication. Defaults to an empty string.
        dbms (Literal['mssql', 'sqlite','postgres'], optional): The type of database management system. Defaults to 'mssql'.
        ensure_db_exists (bool, optional): Specifies whether to create the database if it does not exist. Defaults to False.

    Returns:
        Connection: The connection object for the established database connection.
    
    Remarks:
        - postgres
            - psycopg2-binary must be installed
            - example:
                con = my_connect_to_any_sql(
                    host='<instance>.postgres.database.azure.com',
                    db='eteste',
                    user='<user>n@<instance>',
                    pw='<password>',
                    dbms='postgres',
                    ensure_db_exists=False
                )
        - mssql
            - sqlalchemy nust be <v2 to write -> sql
    
    """

    if dbms == 'mssql':
        url = f'mssql://{user}:{pw}@{host}/{db}?driver=ODBC Driver 17 for SQL Server'
    elif dbms == 'sqlite':
        url = f'sqlite:///{db}'
    elif dbms == 'postgres':
        url = f'postgresql+psycopg2://{user}:{pw}@{host}/{db}'
    else:
        print("dbms not supported")
        return None

    engine = create_engine(
        url,    # * leave positional argument unnamed, since it was relabeled between versions..
        connect_args={'connect_timeout': 10},
        )

    # * ensure db exists
    if ensure_db_exists:
        if not database_exists(engine.url):
            create_database(engine.url)
            print(f'db {db} created')
        else:
            print(f'db {db} exists')

    # * now connect
    try:
        con=engine.connect()
    except Exception as e:
        print(e)

    return con
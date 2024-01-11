import psycopg2.pool as pg_pool
import time


class PGConnectionPool:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, db_user=None, db_pass=None, db_host=None, db_name=None, db_port=None
    ):
        if not hasattr(self, "db_host"):
            if not db_user or not db_pass or not db_host or not db_name or not db_port:
                raise Exception(
                    """db_user, db_pass, db_host, db_name, db_port are required to create a connection pool.
                    If you're seeing this unexpectedly, be sure to initialize the connection pool before using it."""
                )
            self.db_user = db_user
            self.db_pass = db_pass
            self.db_host = db_host
            self.db_name = db_name
            self.db_port = db_port
            self._connections = None
            self._instance = None
            pass

    @property
    def connection_pool(self):
        if self._connections:
            return self._connections
        else:
            self._connections = pg_pool.ThreadedConnectionPool(
                1,
                20,
                user=self.db_user,
                password=self.db_pass,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
            )
            return self._connections

    def get_connection(self):
        connection = None
        attempts = 0
        while connection == None and attempts < 20:
            try:
                connection = self.connection_pool.getconn()
            except:
                attempts += 1
                time.sleep(0.25)
        return connection

    def return_connection(self, conn):
        self.connection_pool.putconn(conn)

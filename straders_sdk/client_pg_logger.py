import psycopg2.pool as pg_pool
import time
import logging


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
            self.logger = logging.getLogger("PGConnectionPool")
            pass

    @property
    def connection_pool(self):
        if self._connections:
            return self._connections
        else:
            self._connections = pg_pool.ThreadedConnectionPool(
                1,
                100,
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
        while connection == None and attempts < 60:
            try:
                # self.logger.debug("Attempting to get a connection from the pool")
                connection = self.connection_pool.getconn()
                self.logger.debug(
                    f"Got a connection from the pool after {attempts} attempts - {len(self.connection_pool._used)} / {self.connection_pool.maxconn}used"
                )
            except:
                attempts += 1
                time.sleep(1)
        return connection

    def return_connection(self, conn):
        if not conn:
            self.logger("Tried to rturn something that's not a connection? what? why?")
            return
        closed = conn.closed > 0
        # self.logger.debug("about to rturn a connection to the pool")
        self.connection_pool.putconn(conn, close=closed)
        # self.logger.debug(
        #    f"Returned a connection to the pool - {len(self.connection_pool._used)} / {self.connection_pool.maxconn} used"
        # )

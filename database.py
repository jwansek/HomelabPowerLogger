from dataclasses import dataclass
import pymysql
import os

@dataclass
class PowerDatabase:
    host: str = "db"
    user: str = "root"
    passwd: str = None
    db: str = "power"
    port: int = 3306

    def __enter__(self):
        if self.passwd is None:
            self.passwd = os.environ["MYSQL_ROOT_PASSWORD"]
            
        try:
            self.__connection = self.__get_connection()
        except Exception as e:
            print(e)
            if e.args[0] == 1049:
                self.__connection = self.__build_db()
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.commit()
        self.__connection.close()

    def __get_connection(self):
        return pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd,
            charset = "utf8mb4",
            database = self.db
        )

    def __build_db(self):
        print("Building database...")
        self.__connection = pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd,
            charset = "utf8mb4",
        )
        with self.__connection.cursor() as cursor:
            # unsafe:
            cursor.execute("CREATE DATABASE %s" % self.db)
            cursor.execute("USE %s" % self.db)

            cursor.execute("""
            CREATE TABLE tasmota_devices (
                host VARCHAR(25) NOT NULL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                password VARCHAR(50) NOT NULL
            );
            """)

            if "TASMOTA_DEVICES" in os.environ.keys():
                devices = os.environ["TASMOTA_DEVICES"].split(",")
                for device in devices:
                    host, username, password = device.split(":")
                    cursor.execute("INSERT INTO tasmota_devices VALUES (%s, %s, %s);", (host, username, password))

            cursor.execute("""
            CREATE TABLE watt_readings (
                host VARCHAR(25) NOT NULL,
                `datetime` DATETIME DEFAULT NOW(),
                reading FLOAT(24) NOT NULL,
                FOREIGN KEY (host) REFERENCES tasmota_devices (host),
                PRIMARY KEY (host, `datetime`)
            );
            """)

            cursor.execute("""
            CREATE TABLE kwh_readings (
                host VARCHAR(25) NOT NULL,
                `datetime` DATETIME DEFAULT NOW(),
                reading FLOAT(24) NOT NULL,
                FOREIGN KEY (host) REFERENCES tasmota_devices (host),
                PRIMARY KEY (host, `datetime`)
            );
            """)

            self.__connection.commit()
            return self.__connection

    def get_tasmota_devices(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tasmota_devices;")
            return cursor.fetchall()

    def append_watt_readings(self, host, reading):
        with self.__connection.cursor() as cursor:
            cursor.execute("DELETE FROM watt_readings WHERE `datetime` < DATE_SUB(NOW(), INTERVAL 1 DAY);")
            cursor.execute("INSERT INTO watt_readings (host, reading) VALUES (%s, %s);", (host, reading))

    def append_kwh_readings(self, host, reading):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO kwh_readings (host, reading) VALUES (%s, %s);", (host, reading))

if __name__ == "__main__":
    if not os.path.exists(".docker"):
        import dotenv
        dotenv.load_dotenv(dotenv_path = "db.env")
        host = "srv.home"
    else:
        host = "db"

    with PowerDatabase(host = host) as db:
        print(db.get_tasmota_devices())

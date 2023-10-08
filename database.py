from dataclasses import dataclass
import pymysql
import os

@dataclass
class PowerDatabase:
    host: str = None
    user: str = "root"
    passwd: str = None
    db: str = "power"
    port: int = 3306

    def __enter__(self):
        if self.passwd is None:
            self.passwd = os.environ["MYSQL_ROOT_PASSWORD"]

        if self.host is None:
            self.host = os.environ["MYSQL_HOST"]
            
        try:
            self.__connection = self.__get_connection()
        except Exception as e:
            print(e)
            if e.args[0] == 1049:
                self.__connection = self.__build_db()
            elif e.args[0] == 2003:
                raise ConnectionError(e.args[1])

        with self.__connection.cursor() as cursor:
            if "TASMOTA_DEVICES" in os.environ.keys():
                for host, username, password in self.get_tasmota_devices():
                    cursor.execute("""
                    INSERT INTO tasmota_devices (host, username, password) 
                    VALUES (%s, %s, %s) 
                    ON DUPLICATE KEY UPDATE username = %s, password = %s;
                    """, (host, username, password, username, password))

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
        o = []
        for d in os.environ["TASMOTA_DEVICES"].split(","):
            o.append(d.split(":"))
        return o

    def append_watt_readings(self, host, reading):
        with self.__connection.cursor() as cursor:
            cursor.execute("DELETE FROM watt_readings WHERE `datetime` < DATE_SUB(NOW(), INTERVAL 1 DAY);")
            cursor.execute("INSERT INTO watt_readings (host, reading) VALUES (%s, %s);", (host, reading))

    def append_kwh_readings(self, host, reading):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO kwh_readings (host, reading) VALUES (%s, %s);", (host, reading))

    def get_last_plug_readings(self):
        plugs = [i[0] for i in self.get_tasmota_devices()]
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT host, MAX(datetime) FROM watt_readings WHERE host IN %s GROUP BY host;", (plugs, ))
            plugtimes = cursor.fetchall()

            readings = []
            for host, datetime in plugtimes:
                cursor.execute("SELECT host, datetime, reading FROM watt_readings WHERE host = %s AND datetime = %s;", (host, datetime))
                readings.append(cursor.fetchone())
        return readings

    def get_watt_chart(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT host FROM watt_readings;")
            hosts = [i[0] for i in cursor.fetchall()]
            
            out = {}
            for host in hosts:
                cursor.execute("SELECT datetime, reading FROM watt_readings WHERE host = %s ORDER BY datetime;", (host, ))
                out[host] = cursor.fetchall()

        return out

    def get_kwh_chart(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT host FROM kwh_readings;")
            hosts = [i[0] for i in cursor.fetchall()]
            
            out = {}
            for host in hosts:
                cursor.execute("SELECT datetime, reading FROM kwh_readings WHERE host = %s ORDER BY datetime;", (host, ))
                out[host] = cursor.fetchall()

        return out

def to_series(timeseriesforeach):
    print(timeseriesforeach)

if __name__ == "__main__":
    if not os.path.exists(".docker"):
        import dotenv
        dotenv.load_dotenv(dotenv_path = "power.env")
        host = "srv.athome"
    else:
        host = None

    with PowerDatabase(host = host) as db:
        print(to_series(db.get_kwh_chart()))

import sqlite3
from functions.log import create_logger

logger = create_logger('SqLiteConnector')


class SqLiteConnector:

    def __init__(self):
        self.dn = 'stData'
        self.__connector = None
        self.__cursor = None
        # Note to Moritz: Add here the tables you need:
        self.__legal_tables = {
            'cborTable': True
        }

    def name_database(self, dname):
        self.dn = dname

    def start_database_connection(self):
        message = ('%s.db' % self.dn)
        self.__connector = sqlite3.connect(message)
        self.__cursor = self.__connector.cursor()

    def create_table(self, tname, *argv):
        if not self.__legal_tables.get(tname):
            logger.error('Illegal table creation attempt.')
            return False
        if not self.__connector:
            logger.error('Connection not open during table creation.')
            raise ConnectorNotOpenError('while creating a table.')
        message = ('CREATE TABLE IF NOT EXISTS %s (' % tname)
        for arg in argv:
            if not isinstance(arg, str):
                logger.error('% is not a string' % arg)
                return False
            message += arg
            message += ', '
        message = message[:-2]
        message += ');'
        self.__connector.execute(message)
        return True

# TODO: Implement custom insert method for event handler
    def insert_to_table(self, tname, *argv):
        if not self.__connector:
            raise ConnectorNotOpenError('while inserting into a table.')
        message = ('INSERT INTO %s VALUES(' % tname)
        for arg in argv:
            if isinstance(arg, bytes):
                arg = arg.decode('utf-8', errors='replace')
            message += '\'' + arg + '\''
            message += ', '
        message = message[:-2]
        message += ')'
        self.__connector.execute(message)

    def insert_cbor_event(self, tname, feed_id, seq_no, event_as_cbor):
        if not self.__legal_tables.get(tname):
            return False
        if not self.__connector:
            raise ConnectorNotOpenError('while inserting into a table.')
        sql = ''' INSERT INTO %s(feed_id,seq_no,event_as_cbor)
                      VALUES(?,?,?); ''' % tname
        try:
            self.__connector.execute(sql, (feed_id, seq_no, memoryview(event_as_cbor)))
        except sqlite3.IntegrityError:
            logger.error('Already in the database')
            return False
        return True

    def commit_changes(self):
        if self.__connector:
            self.__connector.commit()

    def close_database_connection(self):
        if self.__connector:
            self.__connector.close()

    def remove_table(self, tname):
        if not self.__legal_tables.get(tname):
            return False
        self.__connector.execute('DROP TABLE IF EXISTS %s; ' % tname)
        return True

    def get_all_from_table(self, tname):
        if not self.__legal_tables.get(tname):
            return None
        self.__cursor.execute('SELECT * FROM %s;' % tname)
        return self.__cursor.fetchall()

    def search_in_table(self, tname, typ, name):
        if not self.__legal_tables.get(tname):
            return None
        self.__cursor.execute("SELECT * from %s WHERE %s = ?" % (tname, typ), (name,))
        return self.__cursor.fetchall()

    def get_current_seq_no(self, tname, feed_id):
        if not self.__legal_tables.get(tname):
            return None
        # self.__cursor.execute("SELECT seq_no FROM cborTable WHERE seq_no = (SELECT MAX(seq_no) FROM cborTable) AND feed_id = ?", (feed_id,))
        return self.__cursor.fetchall()

    def get_event(self, tname, feed_id, seq_no):
        if not self.__legal_tables.get(tname):
            return None
        self.__connector.execute("SELECT event_as_cbor FROM cborTable WHERE feed_id = ?", (seq_no, feed_id,))
        return self.__cursor.fetchall()

    def get_current_event_as_cbor(self, tname, feed_id):
        # logger.debug('searching for %s', feed_id)
        if not self.__legal_tables.get(tname):
            return None
        self.__connector.execute('SELECT COUNT(Name) FROM "{}" WHERE Name=?'.format(group.replace('"', '""')), (food,))
        res = self.__cursor.fetchall()
        return res


class ConnectorNotOpenError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'Connector to Database not open, {0}'.format(self.message)
        else:
            return 'Connector to Database not open'

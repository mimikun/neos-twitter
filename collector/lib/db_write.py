from common import configs
from common.lib import db
import sqlite3
import datetime
from logging import getLogger, DEBUG, StreamHandler

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel(DEBUG)

db_path = configs.db_path
DATETIME_FORMAT = configs.datetime_format


def get_connection():
    return sqlite3.connect(db_path)


def put_messages(messages):
    con = get_connection()
    cur = con.cursor()

    logger.info('inserting messages')
    for mes in messages:
        mes['created_datetime'] = mes['created_datetime'].strftime(DATETIME_FORMAT)
        try:
            sql = """replace into messages values(
                '%(message_id)s',
                '%(message)s',
                '%(attachments)s',
                '%(user_id)s',
                '%(created_datetime)s',
                '%(client)s',
                '%(neotter_user_id)s'
            )""" % mes
            cur.execute(sql)
        except sqlite3.OperationalError as e:
            logger.error('failed to put a message')
            logger.error(sql)
            logger.error(e)
            continue
    con.commit()
    con.close()
    logger.info(f'inserted {len(messages)} messages')


def put_user(user_list):
    con = get_connection()
    cur = con.cursor()

    logger.info('inserting users')
    for user in user_list:
        try:
            cur.execute("""replace into users values(
                '%(user_id)s',
                '%(name)s',
                '%(icon_url)s',
                '%(client)s'
            )""" % user)
        except sqlite3.OperationalError as e:
            logger.error('failed to put an user')
            logger.error(user)
            logger.error(e)
            continue
    con.commit()
    con.close()
    logger.info(f'inserted {len(user)} users')


def delete_old_messages(hour_before: int=48):
    con = get_connection()
    cur = con.cursor()

    delete_from = (datetime.datetime.now() - datetime.timedelta(hours=hour_before)).strftime(DATETIME_FORMAT)
    sql = f"""
        %s from messages
        where created_datetime <= '{delete_from}'
    """
    cur.execute(sql % 'select count(*)')
    count = cur.fetchone()[0]
    logger.info(f'deleting {count} messages')
    cur.execute(sql % 'delete')
    con.commit()
    con.close()


def delete_expired_users():
    con = get_connection()
    cur = con.cursor()

    now = datetime.datetime.now().strftime(DATETIME_FORMAT)
    sql = f"""
        %s from neotter_users
        where expired < '{now}'
    """
    cur.execute(sql % 'select count(*)')
    count = cur.fetchone()[0]
    if count > 0:
        logger.info(f'deleting {count} users')
        cur.execute(sql % 'delete')
        con.commit()
    con.close()


if __name__ == '__main__':
    db.migration()

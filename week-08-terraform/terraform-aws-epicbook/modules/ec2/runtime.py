#!/usr/bin/env python3
"""EC2-only credential/config/SQL helper. Unit tests inject all external operations."""
import grp
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time

APP_DB_USERNAME = 'epicbookapp'
APP = Path('/opt/epicbook')
RUNTIME = Path('/run/epicbook')
CA = Path('/etc/ssl/certs/rds-global-bundle.pem')
FILES = ('BuyTheBook_Schema.sql', 'author_seed.sql', 'books_seed.sql')


def retry(operation, attempts=12, delay=10):
    for attempt in range(attempts):
        try:
            return operation()
        except Exception:
            if attempt + 1 == attempts:
                raise RuntimeError('Bounded operation failed; inspect privately, never publish raw credentials') from None
            time.sleep(delay)


def fetch_credentials(config):
    import boto3
    from botocore.config import Config
    client = boto3.client('secretsmanager', region_name=config['region'], config=Config(
        connect_timeout=5, read_timeout=15, retries={'total_max_attempts': 3}))
    response = retry(lambda: client.get_secret_value(SecretId=config['secret_arn']))
    credentials = json.loads(response['SecretString'])
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,15}', credentials['username']):
        raise ValueError('Unsupported database username')
    if credentials['username'].lower() == APP_DB_USERNAME:
        raise ValueError('Database username is reserved for the application')
    if not re.fullmatch(r'[A-Za-z0-9!#%^*+=_-]{24,41}', credentials['password']):
        raise ValueError('Unsupported password format')
    if not re.fullmatch(r'[A-Za-z0-9.-]+', config['host']):
        raise ValueError('Unsupported database host')
    return credentials


def mysql_option_value(value):
    escapes = {'\\': '\\\\', '"': '\\"', '\b': '\\b', '\t': '\\t', '\n': '\\n', '\r': '\\r'}
    return '"' + ''.join(escapes.get(char, char) for char in value) + '"'


def mysql_options(config, credentials):
    return ('[client]\nuser=' + mysql_option_value(credentials['username'])
            + '\npassword=' + mysql_option_value(credentials['password'])
            + '\nhost=' + mysql_option_value(config['host']) + '\nport=3306\nssl-mode=VERIFY_IDENTITY\nssl-ca='
            + mysql_option_value(str(CA)) + '\nconnect-timeout=10\n')


def run_sql(options, sql):
    result = subprocess.run(['mysql', '--defaults-extra-file=' + str(options), '--batch', '--skip-column-names'],
                            input=sql, text=True, capture_output=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError('Database operation failed (details suppressed to protect credentials)')
    return result.stdout.strip()


def initialize_database(execute, app=APP):
    count = execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='bookstore';")
    if count == '0':
        for filename in FILES:
            execute((app / 'db' / filename).read_text())
    elif not count.isdecimal():
        raise RuntimeError('Unexpected schema inventory')
    # Partial imports fail closed; never re-import seeds over existing rows.
    counts = execute('SELECT (SELECT COUNT(*) FROM bookstore.Author), (SELECT COUNT(*) FROM bookstore.Book);')
    values = counts.split('\t')
    if len(values) != 2 or not all(v.isdecimal() and int(v) > 0 for v in values):
        raise RuntimeError('Missing or partial seed data; explicit recovery is required')


def app_config(host, password, ca):
    return {'production': {'username': APP_DB_USERNAME, 'password': password, 'database': 'bookstore',
            'host': host, 'port': 3306, 'dialect': 'mysql', 'logging': False,
            'dialectOptions': {'ssl': {'ca': ca, 'rejectUnauthorized': True}}}}


def prepare(config):
    credentials = fetch_credentials(config)
    RUNTIME.mkdir(mode=0o750, exist_ok=True)
    os.chmod(RUNTIME, 0o750)
    os.chown(RUNTIME, 0, grp.getgrnam('epicbook').gr_gid)
    with tempfile.TemporaryDirectory(prefix='epicbook-db-', dir='/run') as private:
        options = Path(private) / 'mysql.cnf'
        options.write_text(mysql_options(config, credentials))
        options.chmod(0o600)
        execute = lambda sql: run_sql(options, sql)
        retry(lambda: execute('SELECT 1;'))
        initialize_database(execute)
        password = secrets.token_hex(24)
        execute(f"CREATE USER IF NOT EXISTS '{APP_DB_USERNAME}'@'%' IDENTIFIED BY '{password}' REQUIRE SSL;\n"
                f"ALTER USER '{APP_DB_USERNAME}'@'%' IDENTIFIED BY '{password}' REQUIRE SSL;\n"
                "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES "
                f"ON bookstore.* TO '{APP_DB_USERNAME}'@'%';")
        target = RUNTIME / 'config.json'
        target.write_text(json.dumps(app_config(config['host'], password, CA.read_text())))
        target.chmod(0o640)
        os.chown(target, 0, grp.getgrnam('epicbook').gr_gid)


def verify(config):
    credentials = fetch_credentials(config)
    with tempfile.TemporaryDirectory(prefix='epicbook-verify-', dir='/run') as private:
        options = Path(private) / 'mysql.cnf'
        options.write_text(mysql_options(config, credentials))
        options.chmod(0o600)
        print(run_sql(options, "SELECT DATABASE(); USE bookstore; SHOW TABLES; "
                      "SELECT COUNT(*) AS authors FROM Author; SELECT COUNT(*) AS books FROM Book; "
                      "SELECT id,quantity,price,createdAt FROM Cart ORDER BY id DESC LIMIT 5; "
                      "SELECT CartId,BookId FROM Cartbook ORDER BY CartId DESC LIMIT 5; "
                      "SELECT id,CartId,createdAt FROM Checkout ORDER BY id DESC LIMIT 5; "
                      "SHOW SESSION STATUS LIKE 'Ssl_cipher';"))


if __name__ == '__main__':
    os.umask(0o077)
    try:
        configuration = json.loads(Path('/etc/epicbook-runtime.json').read_text())
        if sys.argv[1:] == ['verify']:
            verify(configuration)
        elif sys.argv[1:] == ['prepare']:
            prepare(configuration)
        else:
            raise ValueError('Use prepare or verify')
    except Exception:
        print('EpicBook runtime step failed; credentials and raw exceptions withheld.', file=sys.stderr)
        sys.exit(1)

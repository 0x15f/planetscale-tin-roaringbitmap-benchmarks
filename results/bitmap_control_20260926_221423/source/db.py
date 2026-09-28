"""Credential-safe PlanetScale connections; no local fallback."""
import os
import certifi
import psycopg
from dotenv import load_dotenv


def connect():
    load_dotenv()
    required = ['DB_HOST', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD']
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError('Missing PlanetScale credentials: ' + ', '.join(missing))
    host = os.environ['DB_HOST']
    if not host.endswith('.psdb.cloud'):
        raise RuntimeError('Expected PlanetScale .psdb.cloud host; refusing another target')
    return psycopg.connect(host=host, port=os.getenv('DB_PORT', '5432'),
        dbname=os.environ['DB_DATABASE'], user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD'], sslmode='verify-full', sslrootcert=certifi.where(),
        connect_timeout=15, autocommit=True, application_name='tin-bitmap-bench')

"""Enable required extensions on the user-authorized benchmark target."""
from harness.db import connect
from harness.discover import main

if __name__ == '__main__':
    with connect() as conn:
        for extension in ('tin', 'roaringbitmap'):
            conn.execute(f'CREATE EXTENSION IF NOT EXISTS {extension}')
            print('Enabled', extension)
    main()

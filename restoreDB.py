import sqlite3
from datetime import datetime, timedelta

fecha = datetime.now() - timedelta(days=1)
hoy = fecha.strftime('%Y-%m-%d')

con = sqlite3.connect('data.db')
cur = con.cursor()

query = f"DELETE FROM articles WHERE created_at = '{hoy}'"
cur.execute(query)
con.commit()
con.close()

'''
Created on 22 Apr 2016

@author: Davey
'''
import sqlite3

conn = sqlite3.connect('wikileaks.db')

conn.execute('INSERT INTO LOC2 (NAME, LATITUDE, LONGTITUDE) SELECT NAME, LATITUDE, LONGTITUDE FROM LOCATIONS ORDER BY NAME')
conn.execute('ALTER TABLE LOCATIONS RENAME TO LOC1')
conn.execute('ALTER TABLE LOC2 RENAME TO LOCATIONS')
conn.commit()
conn.close()
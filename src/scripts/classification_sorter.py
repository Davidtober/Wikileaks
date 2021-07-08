'''
Created on 22 Apr 2016

@author: Davey
'''
import sqlite3

conn = sqlite3.connect('wikileaks.db')
conn.execute('ALTER TABLE FEATS ADD COLUMN ID INT')
data = conn.execute('SELECT * FROM FEATS')
count = 0
for row in data:
    conn.execute('UPDATE FEATS SET ID=? WHERE WORD=?', (count, row[0]))
    count+=1
conn.commit()
conn.close()
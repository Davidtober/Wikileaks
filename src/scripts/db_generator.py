'''
Created on 10 Mar 2016

@author: Davey
'''
import sqlite3

conn = sqlite3.connect('wikileaks.db')
print "Database successfully opened"

conn.execute('DROP TABLE CABLES')
#conn.execute('DROP TABLE LOCATIONS')
#conn.execute('DROP TABLE CLASSIFICATIONS')

# conn.execute('''CREATE TABLE LOCATIONS
#             (ID INTEGER PRIMARY KEY,
#             NAME VARCHAR(50) UNIQUE,
#             LATITUDE REAL,
#             LONGTITUDE REAL
#             );''')

# conn.execute('''CREATE TABLE CLASSIFICATIONS
#             (ID INTEGER PRIMARY KEY,
#             DESCRIPTION VARCHAR(50) UNIQUE
#             );''')

conn.execute('''CREATE TABLE CABLES
       (ID INTEGER PRIMARY KEY,
       RECEIVED           DATETIME    NOT NULL,
       CODE INT NOT NULL,
       LOCATION INT,
       CLASSIFICATION INT,
       TEXT           CHAR,
       CONSTRAINT LOC_FK FOREIGN KEY(LOCATION) REFERENCES LOCATIONS(ID),
       CONSTRAINT CLASS_FK FOREIGN KEY(CLASSIFICATION) REFERENCES CLASSIFICATIONS(ID)
       );''')

conn.execute('PRAGMA foreign_keys = ON;')
print "Table for cables created"
conn.commit()
conn.close()
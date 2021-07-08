'''
Created on 9 Mar 2016

@author: Davey
'''
import csv
import re
import sqlite3

conn = sqlite3.connect('wikileaks.db')
conn.execute('PRAGMA foreign_keys = ON')
with open('cables.csv', 'rb') as csvfile:
    filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    count = 1
    conn.execute('DELETE FROM CABLES')
    #conn.execute('ALTER TABLE CABLES ADD COLUMN SUBJECT varchar(50)')
    cable_text = ''
    new_cable = re.compile('\"\d*\",\"\d*/\d*/\d\d\d\d')
    date_exp = re.compile('\d*/\d*/\d\d\d\d')#Matches date constructs used in the data
    time_exp = re.compile('\d\d*:\d\d*')#Matches time strings
    end_meta = re.compile('\",\"')#ends meta data
    print 'Processing csv file'
    for current in filereader:
        if len(current) > 1:
            if new_cable.match(current[0]):#Indicates a new cable
                in_body = False
                datestring = date_exp.search(current[0]).group().split('/')
                if len(datestring[0]) == 1:
                    datestring[0] = '0'+datestring[0]
                if len(datestring[1]) == 1:
                    datestring[1] = '0'+datestring[1]
                datestring = datestring[2] + '-' + datestring[0] + '-' + datestring[1] +' '
                time = time_exp.match(current[1])
                if time:
                    if len(time.group()) == 5:
                        datestring = datestring + time.group() + ':00'
                    else:
                        datestring += '0'+ time.group() + ':00'
                else:
                    datestring = datestring + '00:00:00'
                meta_data = current[1].split(',')
                for i in range(2,len(current)):
                    meta_data = meta_data + current[i].split(',')
                    
                location = meta_data[2]
                pos = 2
                while not (location[-1] == '\"'):
                    pos +=1
                    location = location + ' ' + meta_data[pos] #Special case for two word place names
                location = location[1:-1] #strip trailing " character                
                classification = meta_data[pos+1]
                pos+=1
                while not (classification[-1] == '\"'):   
                    pos+=1
                    classification = classification + ' ' + meta_data[pos]                
                classification = classification[1:-1]
                conn.execute('INSERT OR IGNORE INTO CLASSIFICATIONS(DESCRIPTION) VALUES (\''+classification+'\');')
                
                loc_id = conn.execute('SELECT ID FROM LOCATIONS WHERE NAME = ?', [location]).fetchone()[0]
                class_id = conn.execute('SELECT ID FROM CLASSIFICATIONS WHERE DESCRIPTION = ?', [classification]).fetchone()[0]
                conn.execute('INSERT INTO CABLES (RECEIVED, CODE, LOCATION, CLASSIFICATION) VALUES (?, ?, ?, ?)', [datestring, meta_data[1][1:-1], loc_id, class_id])
                if count > 0:
                    cable_text = re.sub('\\\\\'','\'\'', cable_text)#Replaces any ' characters from the string with ''
                    cable_text = re.sub('\\\\\"', '"', cable_text)
                    insert_previous_command = 'UPDATE CABLES SET TEXT = \'' +cable_text +'\' WHERE ID = '+str(count-1)
                    conn.execute(insert_previous_command)
                cable_text = ''#Throw away first line
                print 'Processing cable ' + str(count)
                count = count +1
            elif current[0] == 'TAGS:':
                tags = re.sub('\\\'', '\'\'', ' '.join(current[1:]))
                tags = re.sub(' ', '', tags)
                tags = re.sub(',', ', ', tags)
                conn.execute('UPDATE CABLES SET TAGS = {} WHERE ID = {}'.format('\''+tags+'\'', str(count-1)))
            elif current[0] == 'FM' and not in_body:
                pass
            elif current[0] == 'TO' and not in_body:
                recipients = ' '.join(current[1:])
                #while len(current)<1 or current[0] != 'INFO' or end_meta.search(''.join(current)) is None:
                #    recipients+= ', ' + ' '.join(current)
                #    current = filereader.next()
                print recipients
                conn.execute('UPDATE CABLES SET RECIPIENTS = ? WHERE ID = ?',[recipients, count-1])
            elif current[0] == 'SUBJECT:' or current[0] == 'SUBJ:':
                subject = ' '.join(current[1:])
                subject = re.sub('\\\'', '\'\'', subject)
                conn.execute('UPDATE CABLES SET SUBJECT = ? WHERE ID = ?', [subject, count-1])
            else:#It is just the next line of the current cable
                in_body = True
                new_line = ' '.join(current)
                cable_text = '\n'.join([cable_text, new_line])
        #if count > 20000:
        #    break
    cable_text = re.sub('\'','', cable_text)#Removes any ' characters from the string
    insert_previous_command = 'UPDATE CABLES SET TEXT = \'' +cable_text +'\' WHERE ID = '+str(count-1)
    conn.execute(insert_previous_command)
    print count
    conn.commit()
    conn.close()
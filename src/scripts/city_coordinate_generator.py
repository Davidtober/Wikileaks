'''
Created on 18 Mar 2016

@author: Davey
'''
import sqlite3

from geopy.geocoders import Nominatim

conn = sqlite3.connect('wikileaks.db')
data = conn.execute("SELECT * FROM LOCATIONS")
geolocator = Nominatim()
        
for row in data:
    location = row[1].split(' ')
    location = ' '.join(location[1:])#First word is typically consulate or embassy so can be omitted
    if row[1] == 'Secretary of State':
        location = geolocator.geocode('Secretary of State')
    elif row[1] == "US Interests Section Havana":
        location = geolocator.geocode("Havana")
    elif row[1] == "Mission USNATO":
        location = geolocator.geocode("Brussels")#NATO is located in brussels
    elif 'Delegation' in row[1]:
        location = geolocator.geocode("Washington")
    elif row[1] == 'Mission USOSCE' or row[1] == 'UNVIE':
        location = geolocator.geocode("Vienna")#OSCE and UNVIE are located in Vienna
    elif row[1]=="US OFFICE FSC CHARLESTON":
        location = geolocator.geocode('Charleston')
    elif row[1] == 'USMISSION USTR GENEVA' or row[1] == 'US Mission CD Geneva':
        location = geolocator.geocode('geneva')
    elif row[1] == 'DIR FSINFATC':
        location = geolocator.geocode('washington dc')
    elif row[1] == 'Iran RPO Dubai':
        location = geolocator.geocode('dubai')
    else:
        location = geolocator.geocode(location, True, 10)
    print row[1] + ':'
    print '('+str(location.latitude) +', '+ str(location.longitude)+')'
    #conn.execute('UPDATE LOCATIONS SET LATITUDE = ?, LONGTITUDE =? WHERE ID = ?', [location.latitude, location.longitude, row[0]])
conn.commit()
conn.close()
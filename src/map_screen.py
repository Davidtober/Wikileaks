'''
Created on 18 Mar 2016

@author: Davey
'''
import kivy
import sqlite3
import pickle
import os.path

from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.core.window import Window
from kivy.uix.slider import Slider
from kivy.graphics import Instruction
from kivy.graphics import InstructionGroup
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy import args

class MapScreen(Screen):
    conn = sqlite3.connect('wikileaks.db')
    locations = {}
    totals = []
    def __init__(self, **kwargs):
        super(MapScreen, self).__init__(**kwargs)
        #If data is saved to file load from there
        if os.path.isfile("locations.pickle"):
            pickle_in = open("locations.pickle", "rb")
            self.locations = pickle.load(pickle_in)
        #Otherwise generate cache and save it to file
        else:    
            for year in range(1966, 2011):
                results = self.conn.execute('SELECT NAME, COUNT(LOCATION) FROM CABLES JOIN LOCATIONS ON LOCATIONS.ID = CABLES.LOCATION WHERE strftime(\'%Y\', RECEIVED) = ? GROUP BY NAME', [str(year)])
                for row in results:
                    self.locations[row[0]].append(row[1])
                for location in self.locations.keys():
                    entry = self.locations[location]
                    if len(entry) < year-1966+1:
                        entry.append(0)
            save_classifier = open("locations.pickle", "wb")
            pickle.dump(self.locations, save_classifier)
            save_classifier.close()
        #Initialize all the markers ont the map corresponding to locations
        data = self.conn.execute('SELECT * FROM LOCATIONS')
        for row in data:
            pix_co =  self.get_pixel_coordinates(row[3], row[2])
            m = MapDot(pix_co, row)
            self.ids.world.add_widget(m)

    #Converts a longtitude and latitude to a pixel coordinate on the map            
    def get_pixel_coordinates(self, longtitude, latitude):
        sc_size = Window.system_size
        im_size = (sc_size[0], sc_size[0]/2)
        max_lat = 90.0
        max_lon = 180.0
        x = ((longtitude + max_lon)/(2*max_lon))*(im_size[0]-1)
        y = ((latitude + max_lat)/(2*max_lat))*(im_size[1]-1)
        return (x, y)
    
    def display_heat_map(self, min_year, max_year):
        start_index = int(min_year -1966)
        end_index = int(max_year - 1965)
        count = 1
        for key, value in self.locations.iteritems():
            count += sum(value[start_index:end_index])

        cables_sent = count
        if max_year >= 2004:
            count = count/4 #Amplifies circles for large data sets
        for dot in self.ids.world.children:
            loc = self.locations[dot.name]
            total = sum(loc[start_index:end_index])
            dot.change_intensity(float(total)/float(count), total)
            #dot.change_intensity(float(self.locations[dot.name])/float(count))
    
    #Simple animation script that ticks through each of the years one by one
    def animate(self):
        #self.ids.max_year.value = 1966
        def increment_year(*args):
            self.ids.max_year.value += 1
            self.ids.min_year.value += 1
            if self.ids.max_year.value == 2010:
                Clock.unschedule(increment_year)
        Clock.schedule_interval(increment_year, 0.5)
        
    def adjust_max_slider(self):
        max_slider = self.ids.max_year
        if self.ids.min_year.value > max_slider.value:
            max_slider.value = self.ids.min_year.value

    def adjust_min_slider(self):
        min_slider = self.ids.min_year
        if self.ids.max_year.value < min_slider.value:
            min_slider.value = self.ids.max_year.value        

class MapDot(Widget):
    image = InstructionGroup()
    radius = 5
    def __init__(self, coordinates, csv, **kwargs):
        super(MapDot, self).__init__(**kwargs)
        self.name = csv[1]
        self.pos = coordinates
        self.image.add(Color(1,1,1))
        self.image.add(Line(circle=(coordinates[0], coordinates[1], 1)))
        [self.canvas.add(group) for group in [self.image]]
            
    
    def on_touch_up(self, touch):
        if abs(self.pos[0]-(touch.pos[0]))<self.radius and abs(self.pos[1]-(touch.pos[1]))<self.radius:
            print "Displaying city"
            print '{}: {} cables sent'.format(self.name, self.cables_sent)
            p = CityPopup('{}: {} cables sent'.format(self.name, self.cables_sent), self.pos)
            p.open()
            return True
     
    def change_intensity(self, intensity, cables_sent):
        d = 100*intensity
        self.canvas.remove(self.image)
        self.image = InstructionGroup()
        self.image.add(Color(1,0,0))
        circle = Ellipse(pos = (self.pos[0]-d/2, self.pos[1]-d/2), size = (d, d))
        self.radius = d/2
        self.image.add(circle)
        [self.canvas.add(group) for group in [self.image]]
        self.cables_sent = cables_sent
       
class CityPopup(Popup):
    def __init__(self, text, pos, **kwargs):
        super(CityPopup, self).__init__(**kwargs) 
        self.ids.content.text = text
        self.pos = pos
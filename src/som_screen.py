'''
Created on 26 Apr 2016

@author: Davey
'''

import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
import numpy as np
import sqlite3
import matplotlib.pyplot as pl
import kivy
import pickle
import os.path
import threading
import cable_screen

from kivy.garden.matplotlib.backend_kivyagg import FigureCanvas,\
                                                NavigationToolbar2Kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from matplotlib.transforms import Bbox
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.widget import Widget
from kivy.graphics import InstructionGroup

from mvpa2.suite import *
from tables import *
from datetime import datetime
conn = sqlite3.connect('wikileaks.db')
conn.text_factory = str
num_cables = 251209
set_size = 1000
#fetch data for SOM from database
data = conn.execute("SELECT FEATURE_VECTOR FROM CABLES")
feat_size = conn.execute("SELECT COUNT(WORD) FROM FEATS").fetchall()[0][0]
canvas = None
fig, ax = pl.subplots()
som_size = (10,10)
sm=None

def on_pick(artist, event): 
    pos = artist.get_position()
    if int(round(event.xdata))==pos[0] and int(round(event.ydata))==pos[1]:
        print "{} clicked!".format(artist)
        popup = WaitPopup()
        popup.open()
        threading.Thread(target=select_cluster, args=[pos, popup]).start()
        return False, False
    return False, False

def select_cluster(pos, popup, *args):
    p = ClusterPopup(pos)
    popup.dismiss()
    p.open()
    

def get_rgb(minimum, maximum, value):
    minimum, maximum = float(minimum), float(maximum)
    ratio = 2 * (value-minimum) / (maximum - minimum)
    b = int(max(0, 255*(1 - ratio)))
    r = int(max(0, 255*(ratio - 1)))
    g = 255 - b - r
    return r, g, b

def mine_topics(feature_vector):
    feature_vector = feature_vector.tolist()
    #feature_vectors = []
    #print cable_ids
#     for d in cable_ids:
#         cable_features = conn.execute("SELECT FEATURE_VECTOR FROM CABLES WHERE ID=?", [str(d)]).fetchall()[0][0]
#         cable_features = cable_features.split(', ')
#         cable_features = np.array([ int(n) for n in cable_features ], dtype=np.uint8)
#         feature_vectors.append(cable_features)
#     totals = len(feature_vectors[0])*[0]
#     for f in feature_vectors:
#         i=0
#         for t in f:
#             totals[i]+=t
#             i+=1
    vals = sorted(feature_vector, reverse=True)[0:3]
    index = []
    for v in vals:
        index.append(feature_vector.index(v))
    topics = []
    for i in index:
        topics.append(conn.execute("SELECT WORD FROM FEATS WHERE ID=?", [str(i)]).fetchone())
    #print "These were the top indexes: {}".format(index)
    #print "Topic determined to be: {}".format(topics)
    ret_val = ""
    for topic in topics:
        if topic is not None:
            ret_val+=topic[0]+"\n"
    return topics[0][0]+"\n"+topics[1][0]

#This function plots a trained SOM to a matplotlib figure   
def show_som(somK):
    print "Size of som.k: {}, {}, {}".format(len(somK), len(somK[0]), len(somK[0][0]))
    mapped_totals = som_size[0]*[som_size[1]*[0]]
    mapped_cables = [som_size[1]*[None] for _ in range(som_size[0])]
    
    for i in range(som_size[0]):
        for j in range(som_size[1]):
            mapped_cables[i][j] = []
    i=1
    #for m in mapped:
    #    mapped_totals[m[0]][m[1]]+=1
    #    mapped_cables[m[0]][m[1]].append(i)
    #    i+=1

    mapped_topics = [som_size[1]*['None'] for _ in range(som_size[0])]
    for i in range(som_size[0]):
        for j in range(som_size[1]):
            mapped_topics[i][j] = mine_topics(somK[i][j])
    
    image = [som_size[1]*['None'] for _ in range(som_size[0])]
    for i in range(som_size[0]):
        for j in range(som_size[1]):
            image[i][j] = get_rgb(0, 1, float(mapped_totals[i][j])/set_size)#RGB value based on fraction of cables in that point
    pl.imshow(image, origin='lower')
    for i in range(som_size[0]):
        for j in range(som_size[1]):
            pl.text(i, j, mapped_topics[i][j], ha='center', va='center', size='smaller',
                bbox=dict(facecolor='white', alpha=0.5, lw=0), picker=on_pick)
            
    #fig.canvas.mpl_connect('pick_event', on_pick)
    global canvas
    canvas = fig.canvas
#This function maps all cables and saves their coordinates in the database
def map_all_cables(som):
    #conn.execute("ALTER TABLE CABLES ADD COLUMN MAPPING_X INT")
    #conn.execute("ALTER TABLE CABLES ADD COLUMN MAPPING_Y INT")
    print "mapping cables"
    cables = conn.execute("SELECT ID, FEATURE_VECTOR FROM CABLES")
    count = 0
    next_perc = 1
    for c in cables:
        feat_vec = c[1].split(', ')
        feat_vec = [ int(n) for n in feat_vec ]
        m = som([feat_vec])[0]
        print m[0], m[1]
        conn.execute("UPDATE CABLES SET MAPPING_X=?, MAPPING_Y=? WHERE ID = ?", [str(m[0]), str(m[1]), str(c[0])])
        if (float(count)/float(num_cables))*100>next_perc:
            print "{}% complete".format(next_perc)
            next_perc += 1
        conn.commit()
#Fetches the feature vectors from memory and trains the SOM
def train_som():   
    #feat_vecs = np.array(num_cables*[feat_size*[0]])
    i = 0
    #g = Group(None, 'feature_vectors', "fv", True, None)
    #f = open_file('feature_vectors.hdf', 'w')
    feat_vecs = np.array(set_size*[feat_size*[0]])
    for row in data:
        nums = row[0].split(', ')
        nums = np.array([ int(n) for n in nums ], dtype=np.uint8)
        #nums = np.reshape(nums, (len(nums),1))
        #feat_vecs.append(nums)
        feat_vecs[i]=nums
        print "Cable {} processed".format(i)
        i+=1
        if i== set_size:
            break#testing only
        
    som = SimpleSOMMapper(som_size, 100, learning_rate=0.1)
    print "Training..."
    start = datetime.now()
    som.train(feat_vecs)
    end = datetime.now()
    print "complete in {}s".format(end-start)
    mapped = som(range(set_size))
    map_all_cables(som)
    #Save SOM to file for future use
    print "Pickling SOM"
    out_file = open("som.pickle", "wb")
    pickle.dump(som.K, out_file)
    out_file.close()
    show_som(som.K, mapped)
    #f.close() 
def initialise_som():
    #Check to see if the feature vectors have been saved to file
    if os.path.isfile("som.pickle"):
        print "Loading from file"
        pickle_in = open("som.pickle", "rb")
        som = pickle.load(pickle_in)
        show_som(som)
    #Otherwise load them in from the database
    else:
        train_som()

initialise_som()#Load SOM on startup

class SOMScreen(Screen):
    title = 'SOM Test'

    def __init__(self, **kwargs):
        super(SOMScreen, self).__init__(**kwargs)
        fl = self.ids.layout
        global sm
        sm = self.manager
        #a = Button(text="press me", height=40, size_hint_y=None)
        #a.bind(on_press=self.callback)
        #nav1 = NavigationToolbar2Kivy(canvas)
        #fl.add_widget(nav1.actionbar)
        fl.add_widget(canvas)
        #fl.add_widget(a)
    
    def callback(self, instance):
        print self
        canvas.draw()  
    
    def set_manager(self):
        global sm
        sm = self.manager
        
class ClusterPopup(Popup):
    def __init__(self, coords, **kwargs):
        super(ClusterPopup, self).__init__(**kwargs)
        conn = sqlite3.connect('wikileaks.db')
        print "Fetching {}".format(coords)
        results = conn.execute("SELECT SUBJECT, TEXT FROM CABLES WHERE MAPPING_X=? AND MAPPING_Y=? LIMIT 50", coords)
        grid = self.ids.results_grid
        for row in results:
            #print row
            l = ClusterRow(row)
            grid.add_widget(l)
            
class ClusterRow(Widget):
    data = []
    selected = False
    bg = None    
    def __init__(self,row,**kwargs):
        super(ClusterRow, self).__init__(**kwargs)
        self.data = row
        self.ids.lbl.text = row[0]
        
    
    def on_touch_up(self, touch):
        global sm
        if self.collide_point(*touch.pos):
            if self.selected:
                sm.current = 'cable'
                sm.transition.direction = 'left'
                cable_screen.CableScreen.cable_data(self.data[1], sm, 'som')
                self.parent.parent.parent.parent.parent.parent.dismiss()
            else:
                self.selected = True
                self.bg = InstructionGroup()
                #with self.children[0].canvas:
                self.bg.add(Color(1,0,0, 0.1))
                self.bg.add(Rectangle(pos = self.pos, size = self.size))
                [self.children[0].canvas.add(group) for group in [self.bg]]
        else:
            self.selected = False
            if self.bg is not None:
                self.children[0].canvas.remove(self.bg)
                
class WaitPopup(Popup):
    pass
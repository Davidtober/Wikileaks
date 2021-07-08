'''
Created on 19 Mar 2016

@author: Davey
'''
import sqlite3
import kivy

import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
#matplotlib.use('Gtk')

import numpy as np
import matplotlib.pyplot as plt
import threading
import pickle
import os

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.button import Button

start_year = 1966
end_year = 2010
colours = [[0.7411764705882353, 0.8352941176470589, 0.3215686274509804, 1], [0.4196078431372549, 0.5333333333333333, 0.9607843137254902, 1], [0.0392156862745098, 0.6313725490196078, 0.11764705882352941, 1], [0.8941176470588236, 0.07058823529411765, 0.5254901960784314, 1], [0.44313725490196076, 0.8431372549019608, 0.5843137254901961, 1], [0.5764705882352941, 0.32941176470588235, 0.7372549019607844, 1], [0.7215686274509804, 0.6039215686274509, 0.09803921568627451, 1], [0.17647058823529413, 0.6745098039215687, 0.8, 1], [0.9764705882352941, 0.5137254901960784, 0.20784313725490197, 1], [0.054901960784313725, 0.7254901960784313, 0.6274509803921569, 1], [0.7176470588235294, 0.2235294117647059, 0.403921568627451, 1], [0.2901960784313726, 0.4549019607843137, 0.03529411764705882, 1], [0.8235294117647058, 0.6392156862745098, 0.8196078431372549, 1], [0.9333333333333333, 0.4980392156862745, 0.4196078431372549, 1]]
#Above are 14 visually distinct colours from the website iwanthue
colour_index = 0
class PlotScreen(Screen):
    plots = []
    fig = None
    ax = None
    def __init__(self, **kwargs):
        super(PlotScreen, self).__init__(**kwargs)
        self.pop_up = PlotPopupBox()
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Year')
        self.ax.set_ylabel('Occurrences')
        self.ax.set_title('TAGS occurrences over time')
        self.ids.layout.add_widget(self.fig.canvas)
         #If data is saved to file load from there
        if os.path.isfile("tags.pickle"):
            pickle_in = open("tags.pickle", "rb")
            print "Loading tags from file"
            self.tags = pickle.load(pickle_in)
        #Otherwise generate cache and save it to file
        else:
            self.tags = {}
            conn = sqlite3.connect('wikileaks.db')
            conn.text_factory = str
            tags = conn.execute("SELECT TAG FROM POPULAR_TAGS")
            for tag in tags:
                self.tags[tag[0]] = []
                for year in range(1966, 2011):
                    results = conn.execute('SELECT COUNT(*) FROM CABLES WHERE strftime(\'%Y\', RECEIVED) = ? AND TAGS LIKE ?', [str(year), '%'+tag[0]+'%']).fetchone()
                    print results
                    self.tags[tag[0]].append(results[0])
            print "Saving cache to file"
            save_classifier = open("tags.pickle", "wb")
            pickle.dump(self.tags, save_classifier)
            save_classifier.close()
        
        def select_tag(btn):
            self.ids.tags_dropdown.select(btn.text)
        
        conn = sqlite3.connect('wikileaks.db')
        tags = conn.execute("SELECT TAG FROM POPULAR_TAGS")
        btn = Button(text = 'ANY', size_hint_y=None, height= '48dp')
        btn.bind(on_release=select_tag)
        self.ids.tags_dropdown.add_widget(btn)
        for t in tags:
            btn = Button(text= t[0], size_hint_y=None, height = '48dp')
            btn.bind(on_release = select_tag)
            self.ids.tags_dropdown.add_widget(btn)
        #plt.show()
    @staticmethod 
    def get_next_color():
        global colours
        global colour_index
        c = colours[colour_index]
        colour_index = (colour_index+1)%len(colours)
        return c
        
    def search(self, text):
        self.pop_up.open()
        threading.Thread(target=self.asynch_search, args=(text, )).start()
        print self.tags
        
    def asynch_search(self, text):
        c = PlotScreen.get_next_color()
        plot_points_y = [0]*(end_year-start_year+1)
        plot_points_x = range(start_year, end_year+1)
        if self.tags is not None:
            plot_points_y = self.tags[text]
        else:
            if text is not "" and text is not None:
                conn = sqlite3.connect('wikileaks.db')
                data = conn.execute("""SELECT 
                strftime('%Y', RECEIVED), COUNT(*), TAGS
                 FROM CABLES WHERE TAGS LIKE ? 
                 GROUP BY strftime('%Y', RECEIVED)""", ['%'+text+'%'])
                
                conn.close()
                for row in data:
                    year = int(row[0])
                    plot_points_y[year-start_year] += row[1]
                
        plt.plot(plot_points_x, plot_points_y, label=text, color= c)
        self.ids.user_tags_input.text = 'Select Tag'
            #if self.ax.legend_ is not None:
            #    self.ax.legend_.remove()
            #self.ax.legend(loc=2, ncol=2, fancybox=True, shadow=True)
        l = Label(text = text, color = c, height = 40)
        self.ids.legend.add_widget(l)
        plt.draw()
        self.fig.canvas.draw()
        self.pop_up.dismiss()
        
            
    def clear_plots(self):
        colour_index = 0
        plt.clf()
        #Reset axes labels and title
        self.ids.layout.remove_widget(self.fig.canvas)
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('Year')
        self.ax.set_ylabel('Occurrences')
        self.ax.set_title('TAGS occurrences over time')
        self.ids.layout.add_widget(self.fig.canvas)
        #Clear all entries to the legend
        self.ids.legend.clear_widgets()
        
class PlotPopupBox(Popup):
    pass         
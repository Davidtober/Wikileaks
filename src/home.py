'''
Created on 13 Mar 2016

@author: Davey
'''
import sqlite3, kivy, map_screen, plot_screen, som_screen
import cable_screen, time, threading

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.listview import ListView
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.graphics import Instruction
from kivy.graphics import InstructionGroup
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.popup import Popup
from math import ceil

from kivy.garden.navigationdrawer import NavigationDrawer
from kivy.garden.progressspinner import ProgressSpinner

kivy.require('1.0.8')

Builder.load_file('home.kv')
Builder.load_file('map.kv')
Builder.load_file('cable.kv')
Builder.load_file('plot.kv')
Builder.load_file('som.kv')
class HomeScreen(Screen):
    conn = sqlite3.connect('wikileaks.db')
    conn.execute('PRAGMA foreign_keys = ON')#necessary for sqlite3 databases
    page = 1
    sort_col = 'RECEIVED'
    sort_mode = 'ASC'
    caret_up = u'\uf0d8'
    caret_down = u'\uf0d7'
    current_query ="""SELECT RECEIVED, NAME, DESCRIPTION, TAGS, TEXT FROM CABLES 
    JOIN LOCATIONS ON CABLES.LOCATION = LOCATIONS.ID 
    JOIN CLASSIFICATIONS ON CABLES.CLASSIFICATION = CLASSIFICATIONS.ID
    """
    count_query = 'SELECT COUNT(ID) FROM CABLES'
    items_per_page = 50
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.pop_up = PopupBox()
        #Obtain number of pages in current query
        num_items = self.conn.execute(self.count_query).fetchall()[0]
        self.total_pages = ceil(float(num_items[0])/float(self.items_per_page))
        self.ids.total_pages.text = '/' + str(int(self.total_pages))
        self.populate_table()
        
        #Initialize drop-down items
        def select(btn):
            if(self.ids.max_btn.text == 'max year' or int(self.ids.max_btn.text)>=int(btn.text)):
                self.ids.min_dropdown.select(btn.text)
                self.search(btn.text, self.ids.max_btn.text, self.ids.user_location_input.text, self.ids.user_classification_input.text)
            else:
                print 'Invalid date entered'
        def select_max(btn):
            if(self.ids.min_btn.text == 'min year' or int(self.ids.min_btn.text)<=int(btn.text)):
                self.ids.max_dropdown.select(btn.text)
                self.search(self.ids.min_btn.text, btn.text, self.ids.user_location_input.text, self.ids.user_classification_input.text)
            else:
                print 'Invalid date entered'
        for i in range(1966, 2011):
            btn= Button(text=str(i), size_hint_y= None, height= '48dp')
            btn.bind(on_release= select)
            self.ids.min_dropdown.add_widget(btn)
            btn2= Button(text=str(i), size_hint_y= None, height= '48dp')
            btn2.bind(on_release= select_max)
            self.ids.max_dropdown.add_widget(btn2)
            
        def select_classification(btn):
            self.search(self.ids.min_btn.text, self.ids.max_btn.text, self.ids.user_location_input.text, btn.text, self.ids.user_tags_input, self.ids.user_search_input.text)
            self.ids.classification_dropdown.select(btn.text)
            
        classifications = self.conn.execute("SELECT DESCRIPTION FROM CLASSIFICATIONS")
        btn = Button(text = 'ANY', size_hint_y=None, height= '48dp')
        btn.bind(on_release=select_classification)
        self.ids.classification_dropdown.add_widget(btn)
        for classification in classifications:
            btn = Button(text= classification[0], size_hint_y=None, height = '48dp')
            btn.bind(on_release = select_classification)
            self.ids.classification_dropdown.add_widget(btn)
        
        def select_tag(btn):
            self.search(self.ids.min_btn.text, self.ids.max_btn.text, self.ids.user_location_input.text, self.ids.user_classification_input.text, btn.text)
            self.ids.tags_dropdown.select(btn.text)
            
        tags = self.conn.execute("SELECT TAG FROM POPULAR_TAGS")
        btn = Button(text = 'ANY', size_hint_y=None, height= '48dp')
        btn.bind(on_release=select_tag)
        self.ids.tags_dropdown.add_widget(btn)
        for t in tags:
            btn = Button(text= t[0], size_hint_y=None, height = '48dp')
            btn.bind(on_release = select_tag)
            self.ids.tags_dropdown.add_widget(btn)
            
    def populate_table(self, *args):
        thread_connection = sqlite3.connect('wikileaks.db')#We require one sqlite connection per thread
        result_table = self.ids.scroll_results.children[0]
        
        new_query = '{} ORDER BY {} {}'.format(self.current_query, self.sort_col, self.sort_mode)
        new_query +=' LIMIT '+ str(self.items_per_page)+' OFFSET '+ str((self.page-1)*self.items_per_page)
        
        data = thread_connection.execute(new_query)
        new_widgets = []
        for row in data:
            row_widget = TableRow(row)
            cols = row_widget.children[0].children
            cols[3].text = row[0]#date
            cols[2].text = row[1]#location
            cols[1].text = row[2]#classification
            cols[0].text = row[3]#tags
            new_widgets.append(row_widget)
        for widg in new_widgets:
            result_table.add_widget(widg)
        thread_connection.close()
        self.ids.scroll_results.scroll_y = 1
        self.pop_up.dismiss()
    
    #Updates the page number, triggered by user actions
    def change_page(self, new_page):
        if new_page<= self.total_pages and new_page>0:
            self.page = int(new_page)
            self.pop_up.open()
            #Clear before thread to avoid asynchronous draw() issues
            self.ids.scroll_results.children[0].clear_widgets()
            threading.Thread(target=self.populate_table).start()
            self.ids.user_page_input.text = str(self.page)
    
    def search(self, min_year, max_year, location, classification, tag, search_term):
        #Handle cases where user hasn't input anything to a field
        if min_year == 'min year':
            min_year = '1966'
        if max_year == 'max year':
            max_year = '2010'
        date_range = (min_year+'-01-01', max_year+'-12-31')
        self.count_query = """SELECT COUNT(*) FROM CABLES"""
        self.current_query = """SELECT CABLES.RECEIVED, LOCATIONS.NAME, CLASSIFICATIONS.DESCRIPTION, CABLES.TAGS, CABLES.TEXT FROM CABLES 
    JOIN LOCATIONS ON CABLES.LOCATION = LOCATIONS.ID 
    JOIN CLASSIFICATIONS ON CABLES.CLASSIFICATION = CLASSIFICATIONS.ID"""
        #self.ids.user_search_input.text = ''
        if classification == 'classification' or classification=='ANY':
            self.count_query = """SELECT COUNT(*) FROM CABLES
            JOIN LOCATIONS ON CABLES.LOCATION = LOCATIONS.ID
             WHERE NAME LIKE \'%{}%\' AND RECEIVED BETWEEN \'{}\' AND \'{}\' AND TEXT LIKE \'%{}%\'
            """.format(location, date_range[0], date_range[1], search_term)
            self.current_query = """SELECT CABLES.RECEIVED, LOCATIONS.NAME, CLASSIFICATIONS.DESCRIPTION, CABLES.TAGS, CABLES.TEXT FROM CABLES 
    JOIN LOCATIONS ON CABLES.LOCATION = LOCATIONS.ID 
    JOIN CLASSIFICATIONS ON CABLES.CLASSIFICATION = CLASSIFICATIONS.ID
    WHERE LOCATIONS.NAME LIKE \'{}\' AND CABLES.RECEIVED BETWEEN \'{}\' AND \'{}\' AND CABLES.TEXT LIKE \'%{}%\'
    """.format('%'+location+'%', date_range[0], date_range[1], search_term)
        else:
            self.count_query = """SELECT COUNT(*) FROM CABLES 
            JOIN LOCATIONS ON CABLES.LOCATION = LOCATIONS.ID
            JOIN CLASSIFICATIONS ON CABLES.CLASSIFICATION =CLASSIFICATIONS.ID
            WHERE NAME LIKE \'%{}%\' AND DESCRIPTION= \'{}\' AND RECEIVED BETWEEN \'{}\' AND \'{}\' AND TEXT LIKE \'%{}%\'
            """.format(location, classification, date_range[0], date_range[1], search_term)
            self.current_query = """SELECT CABLES.RECEIVED, LOCATIONS.NAME, CLASSIFICATIONS.DESCRIPTION, CABLES.TAGS, CABLES.TEXT FROM CABLES 
    JOIN LOCATIONS ON CABLES.LOCATION = LOCATIONS.ID
    JOIN CLASSIFICATIONS ON CABLES.CLASSIFICATION = CLASSIFICATIONS.ID
    WHERE NAME LIKE \'%{}%\' AND DESCRIPTION= \'{}\' AND RECEIVED BETWEEN \'{}\' AND \'{}\' AND TEXT LIKE \'%{}%\'
    """.format(location, classification, date_range[0], date_range[1], search_term)
        
        #Reset to first page for new search results
        self.page = 1
        self.ids.user_page_input.text = '1'
        self.pop_up.open()
        
        #Result widgets need to be cleared here to avoid asynchronous kivy draw() errors
        self.ids.scroll_results.children[0].clear_widgets()
        #Asynchronously begin collecting and displaying data
        threading.Thread(target=self.update_pages).start()
        threading.Thread(target=self.populate_table).start()
    
    def update_pages(self):
        thread_conn = sqlite3.connect('wikileaks.db')
        num_items = thread_conn.execute(self.count_query).fetchall()[0]        
        self.total_pages = ceil(float(num_items[0])/float(self.items_per_page))
        self.ids.total_pages.text = '/' + str(int(self.total_pages))
        thread_conn.close()
    
    def order_by(self, col, btn):
        current = self.sort_col
        if(current == col):
            if self.sort_mode == 'ASC':
                self.sort_mode = 'DESC'
                btn.text = btn.text.split(' ')[0]
                btn.text = btn.text+' [font=fonts/fontawesome-webfont.ttf]'+  self.caret_down + '[/font]'
            else:
                self.sort_mode = 'ASC'
                btn.text = btn.text.split(' ')[0]
                btn.text = btn.text+' [font=fonts/fontawesome-webfont.ttf]'+ self.caret_up +'[/font]'
        else:
            if current == 'RECEIVED':
                self.ids.received_header.text = self.ids.received_header.text.split(' ')[0]
            elif current == 'LOCATION':
                self.ids.location_header.text = self.ids.location_header.text.split(' ')[0]
            else:
                self.ids.classification_header.text = self.ids.classification_header.text.split(' ')[0]
            self.sort_col = col
            btn.text = btn.text + ' [font=fonts/fontawesome-webfont.ttf]'+  self.caret_up + '[/font]'
            self.sort_mode = 'ASC'
        self.pop_up.open()
        #Clear now to avoid asynchronous draw() issues
        self.ids.scroll_results.children[0].clear_widgets()
        threading.Thread(target=self.populate_table).start()


class TableRow(Widget):
    data = []
    selected = False
    bg = None    
    def __init__(self,row,**kwargs):
        self.data = row
        super(TableRow, self).__init__(**kwargs)
    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if self.selected:
                sm.current = 'cable'
                sm.transition.direction = 'left'
                cable_screen.CableScreen.cable_data(self.data[4], sm, 'home')
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

class PopupBox(Popup):
    pass

# Create the screen manager
sm = ScreenManager()
sm.add_widget(HomeScreen(name='home'))
sm.add_widget(map_screen.MapScreen(name='map'))
sm.add_widget(cable_screen.CableScreen(name='cable'))
sm.add_widget(plot_screen.PlotScreen(name='plot'))
ss = som_screen.SOMScreen(name='som')
sm.add_widget(ss)
ss.set_manager()

class CableViewerApp(App):

    def build(self):
        Clock.max_iteration = 200
        return sm
    
if __name__ == '__main__':
    CableViewerApp().run()
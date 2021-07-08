'''
Created on 24 Apr 2016

@author: Davey
'''
from kivy.uix.screenmanager import ScreenManager, Screen
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize
from nltk.tag.stanford import StanfordPOSTagger
from nltk.tag.stanford import StanfordNERTagger
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
import string
import threading

class CableScreen(Screen):
    @staticmethod
    def cable_data(data, sm, source):
        sc = sm.get_screen('cable')
        sc.data = data
        sc.ids.cable_data.text = data
        sc.source = source
        
    def highlight_sentiment(self):
        num_sentences = 6
        text = self.data
        sent_with_score = self.get_top_sentences(num_sentences)
        total_sent = 0
        for s in sent_with_score:
            total_sent += s[1]['compound']
            if abs(s[1]['compound'])>0.1:#Avoid sentences with weak sentiment
                print s[1]['compound']
                if s[1]['compound']>0:
                    print 'Positive sentiment found'
                    text = text.replace(s[0], '[color=2eb82e]'+s[0]+'[/color]')
                else:
                    text = text.replace(s[0], '[color=e60000]'+s[0]+'[/color]')
                    print 'Negative sentiment found'
        
        if abs(total_sent)>0.5:
            if total_sent>0:
                sent = "Strong Positive"
            else:
                sent = "Strong Negative"
        else:
            if total_sent>0:
                sent = "Positive"
            else:
                sent = "Negative"
        p = Popup(size_hint = (0.4,0.2))
        p.title = "Overall Sentiment"
        p.content = Label(text=sent)
        p.open()
        self.ids.cable_data.text = text
    
    def get_top_sentences(self, num_sentences):
        #Helper function to sort based on absolute strength of sentiment
        def get_key(item):
            return abs(item[1]['compound'])
        sid = SentimentIntensityAnalyzer()
        text = self.data
        sentences = tokenize.sent_tokenize(text)
        sent_with_score = []
        print sentences[0]
        #Ignore first two sentences as these are never part of the body.
        for s in sentences[2:]:
            sent_with_score.append((str(s), sid.polarity_scores(s)))
        sent_with_score = sorted(sent_with_score, key=get_key, reverse=True)
        if len(sent_with_score)>num_sentences:
            return sent_with_score[0:num_sentences-1]
        return sent_with_score
    
    def display_summary(self):
        self.p = SummaryPopUpBox()
        self.p.open()
        threading.Thread(target=self.display_summary_thread).start()
    
    def display_summary_thread(self):
        summary=''
        num_sentences = 4
        sent_with_score= self.get_top_sentences(num_sentences)
        for s in sent_with_score:
            if abs(s[1]['compound'])>0.1:#Avoid sentences with weak sentiment
                summary+=s[0]+'\n'
        layout = SummaryContent()
        self.get_tags(layout)
        layout.ids.summary.text += summary
        layout.p = Popup(title="Summary", size_hint=(0.7,0.7), content=layout)
        self.p.dismiss()
        layout.p.open()
        
    def get_tags(self, layout):
        st = StanfordNERTagger(r'stanford-ner-2014-06-16/classifiers/english.all.3class.distsim.crf.ser.gz', r'stanford-ner-2014-06-16/stanford-ner.jar')
        tagged_words = st.tag(self.data.split())
        current_tag = ""
        current_word = ""
        NEs = []
        for word in tagged_words:
            if not(word[1] == u'O'):
                #Word is a continuation of the previous NE
                if(word[1] == current_tag):
                    current_word += ' ' + word[0]
                #Found a new phrase to be tagged
                elif current_tag == "":
                    current_word = word[0]
                    current_tag = word[1]
                else:
                    NEs.append([current_word, current_tag])
                    current_word = word[0]
                    current_tag = word[1]
            else:
                if not(current_tag== ''):
                    NEs.append([current_word, current_tag])
                current_tag = ""
        #Filter out punctuation
        punct = "".join(string.punctuation)
        for s in NEs:  
            s[0] = "".join(c for c in s[0] if c not in (punct))
        #Now pick out unique words only
        filtered_nes = []
        for ne in NEs:
            if ne not in filtered_nes:
                filtered_nes.append(ne)
        locs = ''
        orgs = ''
        people = ''
        for ne in filtered_nes:
            if ne[1] == u'LOCATION':
                locs+=ne[0]+', '
            elif ne[1] == u'ORGANIZATION':
                orgs += ne[0]+', '
            elif ne[1] == u'PERSON':
                people += ne[0]+', '
        layout.ids.summary.text = "People: "+people[:-2]+".\n"
        layout.ids.summary.text += "\nLocations: "+locs[:-2]+".\n"
        layout.ids.summary.text += "\nOrganizations: "+orgs[:-2]+".\n\n"
        
        
class SummaryContent(Widget):
    def __init__(self, **kwargs):
        self.p = Popup()
        super(SummaryContent, self).__init__(**kwargs)
        
class SummaryPopUpBox(Popup):
    pass
'''
Created on 27 Apr 2016

@author: Davey
'''
import sqlite3
import nltk
import sys
import string
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from collections import Counter

conn = sqlite3.connect('wikileaks.db')
num_cables = 251209
rows = conn.execute("SELECT TEXT FROM CABLES")
#conn.execute("CREATE TABLE FEATS (WORD CHAR[20] NOT NULL, COUNT INT)")
stops = set(stopwords.words("english"))
table = string.maketrans("","")
word_list = []
tokenizer = RegexpTokenizer('[a-z]+')
count =0
one_perc = int(num_cables/100)
next_perc = 1
print 'Reading'
sys.stdout.write("\r{}% complete".format(0))
sys.stdout.flush()
for item in rows:
    next(rows, None)
    next(rows, None)
    next(rows, None)
    next(rows, None)
    next(rows, None)
    text = tokenizer.tokenize(item[0].lower())
    filtered_text = [word for word in text if word not in stops]
    #Now pick out unique words only
    filtered_text = [k for k, c in Counter(filtered_text).iteritems() if c == 1]
    for word in filtered_text:
        if not any(word in w for w in word_list):
            word_list.append([word, 1])
        else:
            w = next(x for x in word_list if x[0]==word)
            w[1] += 1
    count += 6
    if count> next_perc*one_perc:
        sys.stdout.write("\r{}% complete".format(next_perc))
        sys.stdout.flush()
        next_perc+=1
        

half_cables = int(num_cables/12)
next_perc = 1
one_perc_prog = int(len(word_list)/100)
one_perc = one_perc/6
count = 1
print 'Writing to database'
sys.stdout.write("\r{}% complete".format(0))
sys.stdout.flush()
for word in word_list:
    if word[1]>one_perc and word[1]<half_cables:
        #Omit too common or too rare words
        conn.execute("INSERT INTO FEATS (WORD, COUNT) VALUES (?, ?)", (word[0], word[1]))
        #print word
    else:
        word_list.remove(word)
    count += 1
    if count> next_perc*one_perc_prog:
        sys.stdout.write("\r{}% complete".format(next_perc))
        sys.stdout.flush()
        next_perc+=1

conn.commit()
conn.close()   
print "Done :)"

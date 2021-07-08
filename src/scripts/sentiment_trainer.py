'''
Created on 20 Apr 2016

@author: Davey

This script trains a sentiment analyzer and saves the feature waits to a file
'''
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer

n_instances = 1500
subj_docs = [(sent, 'subj') for sent in subjectivity.sents(categories='subj')[:n_instances]]
obj_docs = [(sent, 'obj') for sent in subjectivity.sents(categories='obj')[:n_instances]]

split_point = int(0.8*len(subj_docs))
obj_train_set = obj_docs[:split_point]
obj_test_set = obj_docs[split_point:]
subj_train_set = subj_docs[:split_point]
subj_test_set = subj_docs[split_point:]

train_set = obj_train_set+subj_train_set
test_set = subj_test_set +obj_test_set
sent_analyzer = SentimentAnalyzer()
neg_words = sent_analyzer.all_words([mark_negation(item) for item in train_set])

unigram_feats = sent_analyzer.unigram_word_feats(neg_words, min_freq = 4)
sent_analyzer.add_feat_extractor(extract_unigram_feats, unigrams = unigram_feats)
training_set = sent_analyzer.apply_features(train_set)
test_set = sent_analyzer.apply_features(test_set)

trainer = NaiveBayesClassifier.train
classifier = sent_analyzer.train(trainer, training_set)
for key,value in sorted(sent_analyzer.evaluate(test_set).items()):
    print('{0}: {1}'.format(key, value))
    
save_classifier = open("naivebayes.pickle", "wb")
pickle.dump(classifier, save_classifier)
sid = SentimentIntensityAnalyzer()
print sid.polarity_scores("This app is shit")
save_classifier.close()

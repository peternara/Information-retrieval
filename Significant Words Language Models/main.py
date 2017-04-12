import os
import fileinput
import collections
from math import log
import operator
import numpy as np
import readAssessment
import ProcDoc
import Expansion

data = {}				# content of document (doc, content)
background_model = {}	# word count of 2265 document (word, number of words)
general_model = {}
query = {}				# query
query_lambda = 0.4
doc_lambda = 0.8

document_path = "../Corpus/SPLIT_DOC_WDID_NEW"
query_path = "../Corpus/QUERY_WDID_NEW_middle"

# document model
data = ProcDoc.read_file(document_path)
doc_wordcount = ProcDoc.doc_preprocess(data)
doc_unigram = ProcDoc.unigram(doc_wordcount)

# background_model
background_model = ProcDoc.read_background_dict()

# general model
collection = {}
for key, value in doc_wordcount.items():
	for word, count in value.items():
		if word in collection:
			collection[word] += count
		else:
			collection[word] = count
			
collection_word_sum = 1.0 * ProcDoc.word_sum(collection)
general_model = {k : v / collection_word_sum for k, v in collection.items()}

# query model
query = ProcDoc.read_file(query_path)
query = ProcDoc.query_preprocess(query)
query_wordcount = {}

for q, q_content in query.items():
	query_wordcount[q] = ProcDoc.word_count(q_content, {})

query_unigram = ProcDoc.unigram(query_wordcount)
query_model = ProcDoc.modeling(query_unigram, background_model, query_lambda)

# query process
print "query ..."
assessment = readAssessment.get_assessment()
for step in range(2):
	query_docs_point_dict = {}
	AP = 0
	mAP = 0
	for q_key, q_word_prob in query_model.items():
		docs_point = {}
		for doc_key, doc_words_prob in doc_unigram.items():
			point = 0
			# calculate each query value for the document
			for query_word, query_prob in q_word_prob.items():
				word_probability = 0			# P(w | D)
				# check if word at query exists in the document
				if query_word in doc_words_prob:
					word_probability = doc_words_prob[query_word]
				# KL divergence 
				# (query model) * log(doc_model) 			
				point += query_model[q_key][query_word] * log((1-doc_lambda) * word_probability + doc_lambda * background_model[query_word])
			docs_point[doc_key] = point
			# sorted each doc of query by point
		docs_point_list = sorted(docs_point.items(), key=operator.itemgetter(1), reverse = True)
		query_docs_point_dict[q_key] = docs_point_list
	# mean average precision	
	mAP = readAssessment.mean_average_precision(query_docs_point_dict, assessment)
	print "mAP"
	print mAP
	if step < 1:
		ProcDoc.outputRank(query_docs_point_dict)
		query_model = Expansion.feedback(dict(query_docs_point_dict), dict(query_model), dict(doc_unigram), dict(doc_wordcount), dict(general_model), dict(background_model), 10)
	
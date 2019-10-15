from __future__ import print_function
import sys, os
rootDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(rootDir)
sys.path.append(rootDir +"/../Tools")

import fileinput
import collections
from math import log
import operator
import numpy as np
import ProcDoc
import Expansion
from Evaluate import EvaluateModel
import cPickle as Pickle
import codecs

def outputRank(query_docs_point_dict, mAP):
    cquery_docs_point_dict = sorted(query_docs_point_dict.items(), key=operator.itemgetter(0))
    operation = "w"
    with codecs.open("train-qry-results-" + str(mAP) + ".txt", operation, "utf-8") as outfile:
        for query, docs_point_list in query_docs_point_dict.items():
            outfile.write(query + "\n")    
            out_str = ""
            for docname, score in docs_point_list:
                out_str += docname + " " + str(score) + "\n"
            outfile.write(out_str)
            outfile.write("\n")

data = {}                # content of document (doc, content)
background_model = {}    # word count of 2265 document (word, number of words)
general_model = {}
query = {}                # query
query_lambda = 0.4
doc_lambda = 0.8

document_path = "../Corpus/TDT2/SPLIT_DOC_WDID_NEW"
query_path = "../Corpus/TDT2/QUERY_WDID_NEW_middle"
#query_path = "../Corpus/TDT2/Train/XinTrainQryTDT2/QUERY_WDID_NEW"
#rel_path = "../Corpus/TDT2/Train/QDRelevanceTDT2_forHMMOutSideTrain"
rel_path = "../Corpus/TDT2/AssessmentTrainSet/AssessmentTrainSet.txt"
#query_path = "../Corpus/Train/XinTrainQryTDT2/QUERY_WDID_NEW"

# document model
data = ProcDoc.read_file(document_path)
doc_wordcount = ProcDoc.doc_preprocess(data)
doc_unigram = ProcDoc.unigram(doc_wordcount)

with open("doc_unimdl.dict", "wb") as f: Pickle.dump(doc_unigram, f, True)

#word_idf = ProcDoc.inverse_document_frequency(doc_wordcount)

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

# HMMTraingSet
HMMTraingSetDict = ProcDoc.read_relevance_dict()

# query model
query = ProcDoc.read_file(query_path)
query = ProcDoc.query_preprocess(query)
query_wordcount = {}

for q, q_content in query.items():
    query_wordcount[q] = ProcDoc.word_count(q_content, {})

query_unigram = ProcDoc.unigram(query_wordcount)
with open("qry_unimdl.dict", "wb") as f: Pickle.dump(query_unigram, f, True)
query_model = ProcDoc.modeling(query_unigram, background_model, query_lambda)

#for q, w_uni in query_model.items():
#    if q in HMMTraingSetDict:
#        continue
#    else:
#        query_model.pop(q, None)

print(len(query_model.keys()))

# query process
print("query ...")

evaluate_model = EvaluateModel(rel_path, False)
query_docs_point_fb = {}
query_model_fb = {}
mAP_list = []
for step in [9]:
    query_docs_dict = {}
    query_docs_point_dict = {}
    AP = 0
    mAP = 0
    for q_key, q_word_prob in query_model.items():
        print(step -1, end='\r')
        docs_point = {}
        for doc_key, doc_words_prob in doc_unigram.items():
            point = 0
            # calculate each query value for the document
            for query_word, query_prob in q_word_prob.items():
                word_probability = 0            # P(w | D)
                # check if word at query exists in the document
                if query_word in doc_words_prob:
                    word_probability = doc_words_prob[query_word]
                # KL divergence 
                # (query model) * log(doc_model)             
                point += -1 * query_model[q_key][query_word] * log((1-doc_lambda) * word_probability + doc_lambda * background_model[query_word])
            docs_point[doc_key] = point
            # sorted each doc of query by point
        docs_point_list = sorted(docs_point.items(), key=operator.itemgetter(1))
        docs_list = zip(*docs_point_list)[0]
        query_docs_point_dict[q_key] = docs_point_list
        query_docs_dict[q_key] = docs_list
    # mean average precision
    #print(query_docs_point_dict.keys())
    mAP = evaluate_model.mAP(query_docs_dict)
    mAP_list.append(mAP)
    #outputRank(query_docs_point_dict, mAP)    
    print("")
    print("mAP")
    print(mAP)

    if step < 2:
        # save one shot result
        Pickle.dump(query_model, open("query_model.pkl", "wb"), True)
        Pickle.dump(query_docs_dict, open("query_docs_dict.pkl", "wb"), True)
        # save load shot result
    query_docs_point_fb = Pickle.load(open("query_docs_dict.pkl", "rb"))
    query_model_fb = Pickle.load(open("query_model.pkl", "rb"))
    query_model = Expansion.feedback(HMMTraingSetDict, query_model_fb, doc_unigram, doc_wordcount, general_model, background_model, None)
    for q_key, q_cont in query_model.items():
        print(q_key)
        for word, prob in q_cont.items():
            print(word, prob)
        print()
    print("Expansion end")
#plot_diagram.plotList(mAP_list)
    

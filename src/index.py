# -*- coding: UTF-8 -*-
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import time
from utils.StopWords import remove_stopwords, read_EN_stopwords
from _1_question_retrieval.get_dq import get_dq, init_doc_matrix, init_doc_idf_vector
from _2_sentence_selection.get_ss import get_ss
from _3_summarization.get_summary import get_summary
from pathConfig import res_dir
from utils.csv_utils import write_list_to_csv
from utils.data_util import load_idf_vocab, load_w2v_model
from utils.data_util import preprocessing_for_query
from utils.db_util import read_all_questions_from_repo
from nltk.tokenize import WordPunctTokenizer
from nltk.stem import SnowballStemmer

def get_querylist(list_path):
    filr = open(list_path)
    query_list = []
    i = 0
    for line in filr:
        if i % 2 == 1:
            line = line.strip('\n')
            query_list.append(line)
        i += 1
    return query_list

def preprocess_all_questions(questions, idf, w2v, stopword):
    processed_questions = list()
    stopwords = stopword
    for question in questions:
        title_words = remove_stopwords(question.title, stopwords)
        if len(title_words) <= 2:
            continue
        if title_words[-1] == '?':
            title_words = title_words[:-1]
        question.title_words = title_words
        question.matrix = init_doc_matrix(question.title_words, w2v)
        question.idf_vector = init_doc_idf_vector(question.title_words, idf)
        processed_questions.append(question)
    return processed_questions

topnum = 10
# load word2vec model
print 'load_textual_word2vec_model() : ', time.strftime('%Y-%m-%d %H:%M:%S')
w2v_model = load_w2v_model()
# load repo
print 'load repo :', time.strftime('%Y-%m-%d %H:%M:%S')
repo = read_all_questions_from_repo()
# load idf
print 'load textual voc : ', time.strftime('%Y-%m-%d %H:%M:%S')
idf_vocab = load_idf_vocab()

stopword = read_EN_stopwords()

#process questions
questions = preprocess_all_questions(repo, idf_vocab, w2v_model, stopword)

from flask import Flask, redirect, url_for, request, render_template, jsonify
app = Flask(__name__)

@app.route('/index/<query_x>')
def get_result(query_x):
    query = query_x
    dq_res = list()
    print("query : %s...%s" % (query, time.strftime('%Y-%m-%d %H:%M:%S')))
    query_word = preprocessing_for_query(query)
    print query_word
    query_matrix = init_doc_matrix(query_word, w2v_model)
    query_idf = init_doc_idf_vector(query_word , idf_vocab)
    top_dq = get_dq(query_word, topnum, questions, query_idf, query_matrix)
    cur_res_dict = []
    for i in range(len(top_dq)):
        q = top_dq[i][0]
        sim = top_dq[i][1]
        # print "#%s\nId : %s\nTitle : %s\nSimilarity : %s\n" % (i, q.id, q.title, sim)
        cur_res_dict.append((q.id, round(sim, 2)))
    dq_res.append([query, cur_res_dict])

    #dqres_fpath = os.path.join(res_dir, 'rq_res.csv')
    #header = ["query", "rq_id_list"]
    #write_list_to_csv(dq_res, dqres_fpath, header)

    print 'sentence selection...', time.strftime('%Y-%m-%d %H:%M:%S')
    ss_res = list()
    ss_qid = list()
    for query, top_dq_id_and_sim in dq_res:
        top_ss = get_ss(query_word, topnum, top_dq_id_and_sim, stopword)
        ss_res.append((query, top_ss[0]))
        ss_qid.append((query, top_ss[1]))
    #print ss_qid
    #print ss_res
    
    print 'get summary...', time.strftime('%Y-%m-%d %H:%M:%S')

    rank_list = []
    summ = []
    for query, ss in ss_res:
        query = ' '.join(preprocessing_for_query(query))
        summ, rank_list= get_summary(query, ss, 5, w2v_model, idf_vocab, stopword)
        # summary = '\n'.join([x.capitalize() for x in summ])
        # res.append([query, summary])

    info = list()
    for i in range(0,len(rank_list)):
        qid = dict()
        qid["string"] = summ[i]
        qid["id"] = ss_qid[0][1][rank_list[i]]
        info.append(qid)
    
    return jsonify({"info": info})
    #return render_template('index.html')

@app.route('/index', methods = ['POST','GET'])
def query():
    if request.method == 'POST':
        qestion_query = request.form['query'].replace("/","")
        if qestion_query:
            return redirect(url_for('get_result',query_x = qestion_query))
        else:
            return redirect(url_for('index'))
    if request.method == 'GET':
        qestion_query = request.args.get['query'].replace("/","")
        if qestion_query:
            return redirect(url_for('get_result',query_x = qestion_query))
        else:
            return redirect(url_for('index'))
        
@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='58888')
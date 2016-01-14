from collections import namedtuple
import psycopg2
from flask import Flask
from flask import render_template
from flask import request
from gensim.models import Doc2Vec
import re
import argparse

app = Flask(__name__)


"""Helpers"""
def get_subjects():
    cur = conn.cursor()
    query = "SELECT DISTINCT subject FROM articles;"
    # query = "SELECT COUNT(*) FROM (SELECT DISTINCT subject FROM articles) AS temp;"
    cur.execute(query)
    subjects = sorted([s[0] for s in cur.fetchall()])
    return subjects
    # d = defaultdict(list)
    # for s in subjects:
    #     parent_child = s.split(' - ')
    #     if len(parent_child) == 2:
    #         d[parent_child[0]].append(parent_child[1])
    #     elif len(parent_child) == 1:
    #         d[parent_child[0]] = []

    # return OrderedDict(sorted(d.items()))

def get_articles(indices):
    with conn.cursor() as cur:
        query = cur.mogrify("SELECT * FROM articles WHERE index IN %s", (tuple(indices),))
        cur.execute(query)
        col_names = [col.name for col in cur.description]
        Article = namedtuple("Article", col_names)
        articles = [Article(*row) for row in cur.fetchall()]
        return articles

def get_articles_by_subject(subject):
    with conn.cursor() as cur:
        query = "SELECT * FROM articles WHERE subject='" + subject + "'"
        cur.execute(query)
        col_names = [col.name for col in cur.description]
        Article = namedtuple("Article", col_names)
        articles = [Article(*row) for row in cur.fetchall()]
        return articles

def get_article(index):
    with conn.cursor() as cur:
        query = "SELECT * FROM articles WHERE index="+str(index)
        cur.execute(query)
        col_names = [col.name for col in cur.description]
        Article = namedtuple("Article", col_names)
        article = [Article(*row) for row in cur.fetchall()][0]
        return article

@app.route('/subjects/')
@app.route('/subjects/<subject>')
def browse_subjects(subject=None):
    if subject is None:
        return render_template("browse.html", subjects=get_subjects())
    else:
        articles = get_articles_by_subject(subject)
        return render_template("articles.html", articles=articles, subject=subject)

@app.route('/article/<article_id>')
def find_similars(article_id=None):
    doc = get_article(article_id)
    sims = model.docvecs.most_similar(int(article_id)) # [(id, similarity), ...]
    d = {int(index): [similarity] for index, similarity in sims}
    sim_articles = get_articles(list(d.keys()))
    return render_template("doc.html", doc=doc, sims=sim_articles)


@app.route('/')
def home():
    return render_template("main.html")

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Fire up flask server with appropriate model')
    parser.add_argument('model_path', help="Name of model file")
    args = parser.parse_args()

    # load model:
    model = Doc2Vec.load(args.model_path)

    # run app in db connection context
    with psycopg2.connect(dbname='arxiv') as conn:
        app.run(debug=True, port=5000, host='0.0.0.0')
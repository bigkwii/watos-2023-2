from flask import Flask, redirect, url_for, request, render_template, make_response, session, flash
import numpy as np
import pandas as pd
import rdflib as rdf
import requests
import json
import re
import sys
import SPARQLWrapper as sw
from AnilistPython import Anilist

WIKIDATA_URL = "https://query.wikidata.org/sparql"

def get_query_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = sw.SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(sw.JSON)
    return sparql.query().convert()

def perform_wikidata_query(anime_name_query):
    query = """
    SELECT ?anime ?animeLabel ?anilist_id ?default_review_score WHERE {
        ?anime wdt:P31/wdt:P279* wd:Q1107 .
        ?anime wdt:P8729 ?anilist_id .
        ?anime rdfs:label ?animeLabel.

        # stuff that may or not be there
        OPTIONAL{?anime wdt:P444 ?default_review_score}
        
        # filters
        FILTER(LANG(?animeLabel) = "en")
        FILTER(REGEX(?animeLabel, "%s", "i"))
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . }
    } ORDER BY ?animeLabel LIMIT 10
    """ % anime_name_query
    results = get_query_results(WIKIDATA_URL, query)
    return results['results']['bindings']

app = Flask(__name__)

# @app.route('/')
# def index():
#     return redirect(url_for('home', name='no name'))

# @app.route('/<name>')
# def home(name):
#     return render_template('index.html', content=name)

# @app.route('/user/<name>')
# def user(name):
#     return f'''
#     <h1>Hello, {name}!</h1>
#     '''

# @app.route('/admin')
# def admin():
#     return redirect(url_for('forbidden'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    results = perform_wikidata_query(query)
    return render_template("index.html", query=query, results=results)

@app.route('/forbidden')
def forbidden():
    return make_response('Forbidden', 403)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=81)
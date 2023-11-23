from flask import Flask, redirect, url_for, request, render_template, make_response, session, flash, jsonify
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
    SELECT DISTINCT ?anime ?animeLabel ?anilist_id ?logo_image WHERE {
        ?anime wdt:P31/wdt:P279* wd:Q1107 .
        ?anime wdt:P8729 ?anilist_id .
        ?anime rdfs:label ?animeLabel.
        OPTIONAL{?anime wdt:P154 ?logo_image}

        # stuff that may or not be there
        # OPTIONAL{?anime wdt:P444 ?default_review_score}
        
        # filters
        FILTER(LANG(?animeLabel) = "en")
        FILTER(REGEX(?animeLabel, "%s", "i"))
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . }
    } ORDER BY ?animeLabel LIMIT 10
    """ % anime_name_query
    results = get_query_results(WIKIDATA_URL, query)
    return results['results']['bindings']

app = Flask(__name__)

SELECTED_ANIMES = []

@app.route('/')
def index():
    return render_template('index.html', selected_animes=SELECTED_ANIMES)

@app.route('/search', methods=['POST'])
def search():
    print(SELECTED_ANIMES)
    query = request.form['query']
    results = perform_wikidata_query(query)
    return render_template("index.html", query=query, results=results, selected_animes=SELECTED_ANIMES)

@app.route('/add_to_selected', methods=['POST'])
def add_to_selected():
    anime_title = request.json['anime_title']
    SELECTED_ANIMES.append(anime_title)
    return jsonify({'success': True})

@app.route('/remove_from_selected', methods=['POST'])
def remove_from_selected():
    anime_title = request.json['anime_title']
    SELECTED_ANIMES.remove(anime_title)
    return jsonify({'success': True})

@app.route('/get_anilist_info', methods=['POST'])
def get_anilist_info():
    anilist_id = request.json.get('anilist_id')
    anilist = Anilist()
    anime_info = anilist.get_anime_with_id(int(anilist_id))
    return jsonify({
        'cover_image': anime_info.get('cover_image', ''),
        'average_score': anime_info.get('average_score', ''),
    })

@app.route('/forbidden')
def forbidden():
    return make_response('Forbidden', 403)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=81)
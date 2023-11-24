from flask import Flask, redirect, url_for, request, render_template, make_response, session, flash, jsonify
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
    SELECT DISTINCT ?anime ?animeLabel ?anilist_id  WHERE {
        ?anime wdt:P31/wdt:P279* wd:Q1107 .
        ?anime wdt:P8729 ?anilist_id .
        ?anime rdfs:label ?animeLabel.
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
    query = request.form['query']
    results = perform_wikidata_query(query)
    # get anilist image and average score
    anilist = Anilist()
    for result in results:
        anilist_id = result['anilist_id']['value']
        anime_info = anilist.get_anime_with_id(int(anilist_id))
        result['cover_image'] = anime_info.get('cover_image', '')
        result['average_score'] = anime_info.get('average_score', '')
    return render_template("index.html", query=query, results=results, selected_animes=SELECTED_ANIMES)

@app.route('/add_to_selected', methods=['POST'])
def add_to_selected():
    anime_data = request.json
    SELECTED_ANIMES.append(anime_data)
    print(SELECTED_ANIMES)
    return jsonify({'success': True})

@app.route('/remove_from_selected', methods=['POST'])
def remove_from_selected():
    anime_data = request.json
    SELECTED_ANIMES.remove(anime_data)
    print(SELECTED_ANIMES)
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

@app.route('/generate_recommendations', methods=['GET'])
def generate_recommendations():
    selected_animes = SELECTED_ANIMES
    # get the anime wikidata ids
    anime_wikidata_ids = []
    for anime in selected_animes:
        anime_wikidata_ids.append(anime['anime']['value'].split('/')[-1])
    # query for genres and studios
    print(">>> Querying for genres and studios...")
    query = """
    SELECT DISTINCT ?anime ?animeLabel ?genre ?genreLabel ?studio ?studioLabel WHERE {
        VALUES ?anime { %s }
        OPTIONAL {
            ?anime wdt:P136 ?genre.
            ?genre rdfs:label ?genreLabel.
            FILTER(LANG(?genreLabel) = "en")
        }
        OPTIONAL {
            ?anime wdt:P272 ?studio.
            ?studio rdfs:label ?studioLabel.
            FILTER(LANG(?studioLabel) = "en")
        }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . }
        } ORDER BY ?animeLabel
    """ % ' '.join(['wd:%s' % id for id in anime_wikidata_ids])
    results = get_query_results(WIKIDATA_URL, query)
    # get genres and studios and count how many times each shows up
    genres = {}
    studios = {}
    for result in results['results']['bindings']:
        if 'genre' in result:
            genre = result['genre']['value'].split('/')[-1]
            if genre not in genres:
                genres[genre] = 0
            genres[genre] += 1
        if 'studio' in result:
            studio = result['studio']['value'].split('/')[-1]
            if studio not in studios:
                studios[studio] = 0
            studios[studio] += 1
    # sort genres and studios by count
    genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
    studios = sorted(studios.items(), key=lambda x: x[1], reverse=True)
    # get the top 3 genres and studios
    genres = genres[:3] if len(genres) > 3 else genres
    studios = studios[:3] if len(studios) > 3 else studios
    # query for anime with those genres
    print(">>> Querying for anime with genres...")
    print(">>> with genres: ", ' '.join(['wd:%s' % genre[0] for genre in genres]))
    query = """
    SELECT DISTINCT ?anime ?animeLabel ?anilist_id WHERE {
        ?anime wdt:P31/wdt:P279* wd:Q1107 .
        ?anime wdt:P8729 ?anilist_id .
        ?anime rdfs:label ?animeLabel.
        FILTER(LANG(?animeLabel) = "en")
        VALUES ?genre { %s }
        ?anime wdt:P136 ?genre.
        ?genre rdfs:label ?genreLabel.
        FILTER(LANG(?genreLabel) = "en")
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } ORDER BY ?animeLabel LIMIT 25
    """ % ' '.join(['wd:%s' % genre[0] for genre in genres])
    genre_results = get_query_results(WIKIDATA_URL, query)
    # query for anime with those studios
    print(">>> Querying for anime with studios...")
    print(">>> with studios: ", ' '.join(['wd:%s' % studio[0] for studio in studios]))
    query = """
    SELECT DISTINCT ?anime ?animeLabel ?anilist_id WHERE {
        ?anime wdt:P31/wdt:P279* wd:Q1107 .
        ?anime wdt:P8729 ?anilist_id .
        ?anime rdfs:label ?animeLabel.
        FILTER(LANG(?animeLabel) = "en")
        VALUES ?studio { %s }
        ?anime wdt:P272 ?studio.
        ?studio rdfs:label ?studioLabel.
        FILTER(LANG(?studioLabel) = "en")
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } ORDER BY ?animeLabel LIMIT 20
    """ % ' '.join(['wd:%s' % studio[0] for studio in studios])
    studio_results = get_query_results(WIKIDATA_URL, query)
    # add anilist info to results
    anilist = Anilist()
    for result in genre_results['results']['bindings']:
        anilist_id = result['anilist_id']['value']
        anime_info = anilist.get_anime_with_id(int(anilist_id))
        result['cover_image'] = anime_info.get('cover_image', '')
        result['average_score'] = anime_info.get('average_score', '')
    for result in studio_results['results']['bindings']:
        anilist_id = result['anilist_id']['value']
        anime_info = anilist.get_anime_with_id(int(anilist_id))
        result['cover_image'] = anime_info.get('cover_image', '')
        result['average_score'] = anime_info.get('average_score', '')
    # combine results
    recommendations = {
        'via_genres': genre_results['results']['bindings'],
        'via_studios': studio_results['results']['bindings'],
    }
    print(">>> Sending recommendations to frontend...")
    return jsonify({'recommendations': recommendations})

@app.route('/forbidden')
def forbidden():
    return make_response('Forbidden', 403)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=81)
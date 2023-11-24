# watos-2023-2
Web de Datos 2023-2 - Final Project

## Members

- Álvaro Morales Torres
- Paula Calderón
- Vicente Coronado

## What is this?

Basically, a small experiment to see if we can generate anime recomendations based on the user's "prevoiusly watched" list, via Wikidata.

## How to run

This is a web app, but we are not hosting it anywhere at the moments, so if you want to try it out, clone this repo and run the following commands:

```bash
pip install flask SPARQLWrapper AnilistPython
python src/app.py
```

Then, open your browser and go to `[localhost:81](http://localhost:81)`.

## Special thanks

- [Flask](https://flask.palletsprojects.com/en/2.0.x/) for the web framework
- [SPARQLWrapper](https://sparqlwrapper.readthedocs.io/en/latest/) for the SPARQL wrapper
- [AnilistPython](https://github.com/ReZeroE/AnilistPython) for the Anilist API wrapper
- The country of Japan for creating anime

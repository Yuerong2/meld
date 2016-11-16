from flask import render_template, request, redirect, url_for, current_app, abort, make_response
from config import basedir
from pprint import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
from pyld import jsonld
import json 
from rdflib import Graph, plugin, URIRef, Literal
from rdflib.parser import Parser
from rdflib.serializer import Serializer
import os
import re
from shortuuid import uuid

from . import main

def best_mimetype():
    best = request.accept_mimetypes.best_match( \
        ["application/rdf+xml", "text/n3", "text/turtle", "application/n-triples", \
        "application/json", "text/html"])
    if not best: 
        abort(406) # unacceptable
    # browser might accept on */*, in which case we should probably deliver html
    if request.accept_mimetypes[best] == request.accept_mimetypes["text/html"]:
        best = "text/html"
    return best


@main.route("/annotations/<uid>", methods=["GET"])
def index(uid):
    rdf_file = "{0}/rdf/{1}.ttl".format(basedir, uid)
    if not os.path.isfile(rdf_file):
        abort(404) # file not found
    g = Graph().parse(rdf_file, format="turtle")
    raw_json = json.loads(g.serialize(format="json-ld", indent=2))
    framed = jsonld.frame(raw_json, {
        "@context": { 
                "rdfs":        "http://www.w3.org/2000/01/rdf-schema#",
                "rdf":        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "cnt":         "http://www.w3.org/2011/content#",
                "oa":          "http://www.w3.org/ns/oa#",
#                "meld":    "http://meld.linkedmusic.org/annotations/",
                "meldterm":    "http://meld.linkedmusic.org/terms/",
                "manifest":        "http://meld.linkedmusic.org/manifestations/",
                "leitmotif":   "http://meld.linkedmusic.org/leitmotif/",
                "frbr":        "http://purl.org/vocab/frbr/core#",
                "fabio":        "http://purl.org/spar/fabio/",
                "dct":         "http://purl.org/dc/terms/"
        },
            "@type": "meldterm:topLevel", 
            "oa:hasBody": {
                "@type": "oa:Annotation",
                "oa:hasTarget": { 
                    "fabio:isManifestationOf": {
                        "@type": "frbr:Work",
                        "@embed": "@always"
                    },
                    "@embed":"@always"
                },
                "@embed":"@always"
            },
            "@embed":"@always"
        }, options={"compactArrays":False})

    best = best_mimetype()
    if best == "text/html":
        return render_template("meld.html", annotations=json.dumps(framed, indent=2))
    elif best == "application/json":
        return json.dumps(framed, indent=2)
    else:
        return g.serialize(format=best)

    
@main.route("/jams/<uid>", methods=["GET"])
@main.route("/jams/<uid>/<voice>", methods=["GET"])
def jams(uid, voice=''):
    #n.b. voice not actually used here; used clientside
    rdf_file = "{0}/rdf/{1}.ttl".format(basedir, uid)
    if not os.path.isfile(rdf_file):
        abort(404) # file not found
    g = Graph().parse(rdf_file, format="turtle")
    raw_json = json.loads(g.serialize(format="json-ld", indent=2))
    framed = jsonld.frame(raw_json, {
        "@context": { 
                "rdfs":        "http://www.w3.org/2000/01/rdf-schema#",
                "rdf":        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "cnt":         "http://www.w3.org/2011/content#",
                "oa":          "http://www.w3.org/ns/oa#",
                "meldterm":    "http://meld.linkedmusic.org/terms/",
                "manifest":        "http://meld.linkedmusic.org/manifestations/",
                "leitmotif":   "http://meld.linkedmusic.org/leitmotif/",
                "frbr":        "http://purl.org/vocab/frbr/core#",
                "fabio":        "http://purl.org/spar/fabio/",
                "dct":         "http://purl.org/dc/terms/"
        },
        "@type": "meldterm:topLevel"
        }, options={"compactArrays":False})

    best = best_mimetype()
    if best == "text/html":
        return render_template("dynameld.html", annotations=json.dumps(framed, indent=2))
    elif best == "application/json":
        return json.dumps(framed, indent=2)
    else:
        return g.serialize(format=best)
    
@main.route("/jams/<uid>/jump", methods=["POST"])
def jumpTo(uid):
    jumpFrom = request.form["trigger"]
    jumpTo = request.form["jumpTarget"]
    # load the current RDF file
    rdf_file = "{0}/rdf/{1}.ttl".format(basedir, uid)
    if not os.path.isfile(rdf_file):
        abort(404) # file not found
    newActionId = uuid()
    with open(rdf_file, "a") as jamfile:
        jamfile.write("""
        <http://meld.linkedmusic.org/jams/{0}> oa:hasBody meld:{1} .
        meld:{1} a oa:Annotation ;
            oa:hasBody [
                a meldterm:Jump ;
                meldterm:jumpTo <{2}>
            ];
            oa:hasTarget <{3}> .
            """.format(uid, newActionId, jumpTo, jumpFrom))

    return("", 200);

@main.route("/rooms", methods=["POST"])
def createRoom():
	topLevelTargets = ["<" + t + ">" for t in request.form["topLevelTargets"].split("|")]
	topLevelId = uuid()
	roomFile = "{0}/room/{1}".format(basedir, topLevelId)
	with open(roomFile, "a") as room:
		room.write("""
PREFIX rdfs:        <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:        <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl:        <http://www.w3.org/2002/07/owl#>
PREFIX cnt:         <http://www.w3.org/2011/content#>
PREFIX oa:          <http://www.w3.org/ns/oa#>
PREFIX meld:        <http://meld.linkedmusic.org/annotations/>
PREFIX meldterm:    <http://meld.linkedmusic.org/terms/>
PREFIX manifest:        <http://meld.linkedmusic.org/manifestations/>
PREFIX leitmotif:   <http://meld.linkedmusic.org/leitmotifs/>
PREFIX meldresource:   <http://meld.linkedmusic.org/resources/>
PREFIX frbr:        <http://purl.org/vocab/frbr/core#>
PREFIX fabio:        <http://purl.org/spar/fabio/>
PREFIX dbp:         <http://dbpedia.org/resource/>
PREFIX dct:         <http://purl.org/dc/terms/>

<http://meld.linkedmusic.org/room/{0}> a oa:Annotation, meldterm:topLevel ; 
		oa:hasTarget {1} . 
""".format(topLevelId, " , ".join(topLevelTargets)))
	
	response = make_response("", 201)
	response.headers["Location"] = "/room/{0}".format(topLevelId)
	return response




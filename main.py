#TODO: clean up variable names
#TODO DAH 1ft vs 1.0 miles issue
#TODO finish data entry of service times
#TODO allow users to filter by day of week
#TODO improve interface :)
#TODO eventually add page for users to add/update a church (drop down from database???)

import datetime
from flask import Flask, request, render_template
import os
from dotenv import load_dotenv
from google.cloud import datastore
import requests
import googlemaps
import re
import sys
from church import Church
from service import Service
from userloc import UserLoc

load_dotenv()
API_KEY = os.getenv('MAPS_TOKEN')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

gmaps = googlemaps.Client(key=API_KEY)

project_id = 'diomo-servicetimes'
app = Flask(__name__)

def add_church(client: datastore.Client):
    kind = "church"
    # The name/ID for the new entity
    name = "St. Paul's"
    # The Cloud Datastore key for the new entity
    task_key = client.key(kind, name)

    # Prepares the new entity
    task = datastore.Entity(key=task_key)
    task["address"] = "6518 Michigan Ave, St. Louis, MO 63111"

    # Saves the entity
    client.put(task)

def list_churches(client: datastore.Client):
    query = client.query(kind="church")
    query2 = client.query(kind = "church")
    query2.keys_only()
    church_list = []
    for church, key in zip (list(query.fetch()), list(query2.fetch())):
        keystring = str(key)
        match =re.findall(r"\(.+\)", keystring)
        keystring = match[0]
        keystring= keystring.replace('(','').replace(')','')  
        keystring= keystring.replace('"','') 
        trash, keystring =keystring.split() 
        newchurch = Church(church.get("name"), church.get("address"), keystring)
        church_list.append(newchurch)
    return church_list


def get_geocode(user_input):
    #convert address from user to geopoint
    georesponse = gmaps.geocode(user_input.input)
    #print(georesponse, file=sys.stderr)
    try:
        geocode = georesponse[0]['geometry']['location']
        user_input.set_geocode(geocode)
    except IndexError:
        user_input.valid = False
    return user_input


def calculate_distances(user_loc, churches):
    for church in churches:
        #print (church.address)
        dist =(gmaps.directions(user_loc.geocode, church.address)[0]['legs'][0]['distance']['text'])
        #print(dist, file=sys.stderr)
        intdist = float(re.findall("\d*\.\d+|\d*", dist)[0]) # match either round # of miles or decimal
        church.set_dist(intdist)

def get_services(user_input):
    ds_client = datastore.Client()
    churches = list_churches(ds_client)
    church_list = sort_church_list(user_input, churches)
    church_dict ={}
    for church in church_list:
        keyforquery = ds_client.key(church.key)
        key_edited = church.key.strip("''")
        ancestor1 = ds_client.key("church", key_edited)
        query = ds_client.query(kind="service", ancestor=ancestor1)
        servicequery = query.fetch()
        servicelist = []
        for service in servicequery:
            servicelist.append(Service(service.get("Day"), service.get("Time"), service.get("Service Type"), service.get("Notes")))
        church_dict[church]=servicelist   
    return church_dict


def sort_church_list (user_input, churches):
    ds_client = datastore.Client()
    calculate_distances(user_input, churches) #get distance between user-input location and churches in database #sort churches by distance from user
    newlist = sorted(churches, key=lambda x: x.distance)
    newlist =newlist[:10]
    return newlist


@app.route('/')
def root():    
    return render_template('home.html')

@app.route('/', methods=['POST'])
def my_form_post():
    #from database get list of churches
    #determine distance between churches in db and user address
    user_input = UserLoc(request.form['location'])
    user_input = get_geocode(user_input)
    if (user_input.valid): #if the geocode is valid
        church_dict = get_services(user_input)
        return render_template('index.html', churches=church_dict, response = "Episcopal Churches")
    else:
        return render_template('index.html', response = "invalid location given")
    

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
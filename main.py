#TODO: clean up variable names
#TODO DAH 1ft vs 1.0 miles issue
#TODO add service times to database, display
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

load_dotenv()
API_KEY = os.getenv('MAPS_TOKEN')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

gmaps = googlemaps.Client(key=API_KEY)

project_id = 'diomo-servicetimes'
app = Flask(__name__)

class Church:
    def __init__(self, name, address, key):
        self.name = name
        self.address = address
        self.key = key
        self.dist_to_user = None
    def tostring(self):
        return self.name + " " + self.address
    def set_dist(self, distance):
        self.distance = distance

class Service:
    def __init__(self, day, time, servicetype, notes):
        self.day = day
        self.time = time
        self.type = servicetype
        self.notes = notes

class UserLoc: #location based on user input
    def __init__ (self, user_input):
        self.input = user_input
        self.geocode = None
        self.valid = True
    def set_geocode(self, geocode):
        self.geocode = geocode

    def get_geocode(self):
        return self.geocode

    def set_valid(self):
        self.valid = True

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
    #query.keys_only()
    church_list = []
    for church in list(query.fetch()):
        #print ("key =" + church.Key, file = sys.stderr)
        newchurch = Church(church.get("name"), church.get("address"), client.key('church', 'Advent'))
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

def sort_churches (churches):
    newlist = sorted(churches, key=lambda x: x.distance)
    return newlist


@app.route('/')
def root():    
    return render_template('home.html')

@app.route('/', methods=['POST'])
def my_form_post():
    #from database get list of churches
    #determine distance between churches in db and user address
    #print in order
    ds_client = datastore.Client()
    churches = list_churches(ds_client)
    user_input = UserLoc(request.form['location'])
    user_input = get_geocode(user_input)
    if (user_input.valid): #if the geocode is valid
        calculate_distances(user_input, churches) #get distance between user-input location and churches in database
        church_list = sort_churches(churches) #sort churches by distance from user
        church_list =church_list[:10]
        church_dict ={}
        for church in church_list:
            query = ds_client.query(kind="service", ancestor = church.key)
            #print("key = " + church.key, file = sys.stderr)
            servicequery = query.fetch()
            servicelist = []
            for service in servicequery:
                #print(service)
                servicelist.append(Service(service.get("Day"), service.get("Time"), service.get("Service Type"), service.get("Notes")))
            servicelist.append(Service("Sunday", "6:13 PM", "Rite II Test", "example only"))
            church_dict[church]=servicelist    
            #print(church_dict, file=sys.stderr)
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
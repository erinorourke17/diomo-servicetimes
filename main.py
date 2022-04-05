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
import time

load_dotenv()
API_KEY = os.getenv('MAPS_TOKEN')
ds_client = datastore.Client()
query = ds_client.query(kind="settings")
settings = list(query.fetch())[0]
API_KEY = settings.get("APIKey")
gmaps = googlemaps.Client(key=API_KEY)

project_id = 'diomo-servicetimes'
app = Flask(__name__)

# def add_church(client: datastore.Client):
#     kind = "church"
#     # The name/ID for the new entity
#     name = "St. Paul's"
#     # The Cloud Datastore key for the new entity
#     task_key = client.key(kind, name)

#     # Prepares the new entity
#     task = datastore.Entity(key=task_key)
#     task["address"] = "6518 Michigan Ave, St. Louis, MO 63111"

#     # Saves the entity
#     client.put(task)

def list_churches(client: datastore.Client):
    query = client.query(kind="church")
    query2 = client.query(kind = "church")
    query2.keys_only()
    church_list = []
    for church, key in zip (list(query.fetch()), list(query2.fetch())):
        keystring = str(key) 
        match =re.findall(r"\(.+\)", keystring) #extract the properly formatted key to pass as an argument
        keystring = match[0]
        keystring= keystring.replace('(','').replace(')','')  
        keystring= keystring.replace('"','') 
        trash, keystring =keystring.split() 
        newchurch = Church(church.get("name"), church.get("address"), church.get("website"), keystring)
        church_list.append(newchurch)
    return church_list


def get_geocode(user_input):
    #convert address from user to geopoint
    georesponse = gmaps.geocode(user_input.input)
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
        dist = dist.split(" ")
        if (dist[1] == "ft"): # convert to miles to enable consistent sorting
            dist[0]= round(float(dist[0])/5280, 2)
            dist[1]="mi"
        church.set_dist(float(dist[0]))

def get_services(user_input):
    churches = list_churches(ds_client)
    church_list = sort_church_list(user_input, churches)
    church_dict ={}
    for church in church_list[:10]:
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
    calculate_distances(user_input, churches) #get distance between user-input location and churches in database #sort churches by distance from user
    newlist = sorted(churches, key=lambda x: x.distance)
    #newlist =newlist[:10]
    return newlist


@app.route('/')
def root():    
    return render_template('home.html')

@app.route('/', methods=['POST'])
def my_form_post():
    #from database get list of churches
    #determine distance between churches in db and user address
    start = time.time()
    user_input = request.form['location']
    if (user_input):
        user_input = UserLoc(request.form['location'])
        user_input = get_geocode(user_input)
        if (user_input.valid): #if the geocode is valid
            church_dict = get_services(user_input)
            end = time.time()
            print("The time of execution of above program is : " + str(end-start), file=sys.stderr)
            return render_template('index.html', churches=church_dict, response = "Episcopal Churches")
        else:
            return render_template('index.html', churches = {}, response = "Location not found, please try again")
    else:
        return render_template('home.html', churches = {}, response = "Please enter a location")
    

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
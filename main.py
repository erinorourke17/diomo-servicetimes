import datetime
from flask import Flask, render_template
import os
from dotenv import load_dotenv
load_dotenv()
from google.cloud import datastore
import requests


API_KEY = os.getenv('MAPS_TOKEN')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

project_id = 'diomo-servicetimes'
app = Flask(__name__)

def create_client():
    from google.cloud import storage

    # If you don't specify credentials when constructing the client, the
    # client library will look for credentials in the environment.
    storage_client = storage.Client.from_service_account_json(
        GOOGLE_APPLICATION_CREDENTIALS)
    return storage_client

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
    return(list(query.fetch()))

@app.route('/')
def root():

    x = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key='+API_KEY)
    #from database get list of churches and print as list
    client = create_client()
    ds_client = datastore.Client()
    add_church(ds_client)
    churches = list_churches(ds_client)
    return render_template(
        'index.html', churches=churches, response=x.content)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
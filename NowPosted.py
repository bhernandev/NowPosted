#Importing flask variables for a server side application
from flask import Flask, request, redirect, session

#Importing the Twilio REST API, and twiml for building Twilio responses
from twilio.rest import TwilioRestClient
import twilio.twiml

#Importing the indeed Python module for indeed requrests
from indeed import IndeedClient

#Importing the credentials for the various APIs and libs used
import credentials

#For json parsing and creation if we need it
import json

app = Flask(__name__)

twilio_api = TwilioRestClient(credentials.my_twilio_account_sid, credentials.my_twilio_auth_token)
indeed_api = IndeedClient(publisher = credentials.my_indeed_publisher_id)

@app.route("/", methods=['GET', 'POST'])
def FindJobs():
    #some loop that creates time synced queueing ()
    #for every phone number in clientele array
    params = {
        'v' = ""
        'userip' = "" #this might be a little tough to circumvent, maybe pull data from the form when signing up for NowPosted?
        'useragent' = ""
        'q' = ""
    }
    #make the request with the parameters from the "database"
    #for every existing job for this phone number, eliminate from the search to have only 10 show up
    return ""

if __name__ == "__main__":
    app.run(debug=True)

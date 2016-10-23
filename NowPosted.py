#Importing flask variables for a server side application
from flask import Flask, request, redirect, session

#Importing the Twilio REST API, and twiml for building Twilio responses
from twilio.rest import TwilioRestClient
import twilio.twiml

#Importing the indeed Python module for indeed requrests
from indeed import IndeedClient

#Importing the credentials for the various APIs and libs used
import credentials

#import userInfo

#For json parsing and creation if we need it
import json

app = Flask(__name__)

twilio_api = TwilioRestClient(credentials.my_twilio_account_sid, credentials.my_twilio_auth_token)
indeed_api = IndeedClient(publisher = credentials.my_indeed_publisher_id)

def FindJobs(user_number):
    # query_param = userInfo['users'][user_number]['query']
    params = {
        'v' = "2"
        'userip' = "" #this might be a little tough to circumvent, maybe pull data from the form when signing up for NowPosted?
        'useragent' = "" #use my own computers credentials?
        'q' = "" #query_param
    }
    indeed_response = IndeedClient.search(**params)
    #old_jobs = userInfo['users'][user_number]['old_jobs']
    #loop that checks if any of the 50 new results for indeed exist in the old jobs array. if they do, remove from the json response
    #new_results = newest results from indeed search
    #return new_results 

@app.route("/", methods=['GET', 'POST'])
def DeliverJobs():
    #some loop that creates time synced queueing ()
    #for every phone number in clientele array
    #FindJobs(user_number)
    #make the request with the parameters from the "database"
    #for every existing job for this phone number, eliminate from the search to have only 10 show up
    return ""

if __name__ == "__main__":
    app.run(debug=True)

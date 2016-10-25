#Importing flask variables for a server side application
from flask import Flask, request, redirect, session

#Importing APIs/Libs
from twilio.rest import TwilioRestClient #Twilio
import twilio.twiml #Twilio
from indeed import IndeedClient #Indeed

#Importing the credentials for the various APIs and libs used
import credentials

#For json parsing and creation if we need it
import json

#Imports for time based scheduling
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__, static_url_path='/static/')
app.config.from_object(__name__)

#Creating the clients to interact with the APIs
twilio_api = TwilioRestClient(credentials.my_twilio_account_sid, credentials.my_twilio_auth_token)
indeed_api = IndeedClient(publisher = credentials.my_indeed_publisher_id)

name = ""
query = ""
location = ""

def FindAndDeliverJobs():
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    for user in user_list:
        params = {
            'q': user['search_query'], #query_param
            'l': user['query_location'],
            'userip': credentials.my_ip_address, #this might be a little tough to circumvent, maybe pull data from the form when signing up for NowPosted?
            'useragent': credentials.my_user_agent, #use my own computers credentials?
            'fromage': 1
        }
        indeed_response = indeed_api.search(**params)
        for job in indeed_response['results']:
            job_delivery = job['jobtitle'] + " at " + job['company']
            twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body=job_delivery)
            print("(" + job_delivery + ") sent to: " + user['phone_number'])

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=FindAndDeliverJobs, trigger=IntervalTrigger(seconds=30), id='printing_job', name='Print date and time every five seconds', replace_existing=True)
atexit.register(lambda: scheduler.shutdown())

@app.route("/", methods=['GET', 'POST'])
def DefaultRequestHandler():
    global name
    global query
    global location

    if request.method == 'GET':
        return app.send_static_file('home.html')
    elif request.method == 'POST':
        name = request.form['phone_number']
        query = request.form['search_query']
        location = request.form['query_location']

        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        user_list.append({'phone_number': name, 'search_query': query, 'query_location': location})

        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

        return app.send_static_file('thankyou.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

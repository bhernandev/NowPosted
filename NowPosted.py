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

def FindAndDeliverJobs():
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    for user in user_list:
        params = {
            'q': user['search_query'], #query_param
            'l': "",
            'userip': credentials.my_ip_address, #this might be a little tough to circumvent, maybe pull data from the form when signing up for NowPosted?
            'useragent': credentials.my_user_agent, #use my own computers credentials?
        }
        indeed_response = indeed_api.search(**params)
        job_delivery = indeed_response['results'][0]['jobtitle'] + " at " + indeed_response['results'][0]['company']
        twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body=job_delivery)
        print("(" + job_delivery + ") sent to: " user['phone_number'])
    #old_jobs = userInfo['users'][user_number]['old_jobs']
    #loop that checks if any of the 50 new results for indeed exist in the old jobs array. if they do, remove from the json response
    #new_results = newest results from indeed search
    #return new_results

#some loop that creates time synced queueing ()
#for every phone number in clientele array
#FindJobs(user_number)
#make the request with the parameters from the "database"
#for every existing job for this phone number, eliminate from the search to have only 10 show up

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=FindAndDeliverJobs, trigger=IntervalTrigger(seconds=30), id='printing_job', name='Print date and time every five seconds', replace_existing=True)
atexit.register(lambda: scheduler.shutdown())

@app.route("/", methods=['GET', 'POST'])
def DefaultRequestHandler():
    global name
    global query
    if request.method == 'GET':
        #return the website with the signup form
        return app.send_static_file('home.html')
    elif request.method == 'POST':
        name = request.form['phone_number']
        query = request.form['search_query']

        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        user_list.append({'phone_number': name, 'search_query': query})

        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

        #with open('user_info.json', "w") as json_file:
            #json_file.write(json.dumps(user_info))

        #get form data from request object and place into a dict
        #attach to the json file http://stackoverflow.com/questions/23111625/how-to-add-a-key-value-to-json-data-retrieved-from-a-file-with-python
        return app.send_static_file('thankyou.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

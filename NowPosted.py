#Importing flask variables for a server side application
from flask import Flask, request, session, render_template

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

app = Flask(__name__, template_folder='templates', static_url_path='/static/')
app.config.from_object(__name__)

#Creating the clients to interact with the APIs
twilio_api = TwilioRestClient(credentials.my_twilio_account_sid, credentials.my_twilio_auth_token)
indeed_api = IndeedClient(publisher = credentials.my_indeed_publisher_id)

def FindAndDeliverJobs():
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    for user in user_list:
        params = {
            'q': user['search_query'], #query_param
            'l': user['query_location'],
            'userip': user['user_ip'], #this might be a little tough to circumvent, maybe pull data from the form when signing up for NowPosted?
            'useragent': user['user_agent'], #use my own computers credentials?
            'fromage': 1,
            'limit': 25
        }
        indeed_response = indeed_api.search(**params)
        for job in indeed_response['results']:
            job_delivery = job['jobtitle'] + " at " + job['company']
            twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body=job_delivery)
            print("(" + job_delivery + ") sent to: " + user['phone_number'])

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=FindAndDeliverJobs, trigger=IntervalTrigger(seconds=30), id='printing_job', name='Print date and time every five seconds', replace_existing=True)
#86400
atexit.register(lambda: scheduler.shutdown())

@app.route("/", methods=['GET', 'POST'])
def DefaultRequestHandler(name=None):

    if request.method == 'GET':
        # return app.send_static_file('home.html')
        return render_template('home.html', name=name)
    elif request.method == 'POST':
        user_ip = request.environ['REMOTE_ADDR']
        user_agent = request.headers['User-Agent']
        name = request.form['phone_number']
        query = request.form['search_query']
        location = request.form['query_location']

        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        user_list.append({'user_ip': user_ip, 'user_agent': user_agent, 'phone_number': name, 'search_query': query, 'query_location': location})

        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

        return render_template('thankyou.html',name=name)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

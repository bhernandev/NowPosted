#Importing flask variables for a server side application
from flask import Flask, request, session, render_template
from flask_mail import Mail, Message

#Importing APIs/Libs
from twilio.rest import TwilioRestClient #Twilio
import twilio.twiml #Twilio
from indeed import IndeedClient #Indeed
from pyshorteners import Shortener #TinyURL shortening

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
app.config.update(
	DEBUG=True,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = credentials.my_email_username,
	MAIL_PASSWORD = credentials.my_email_password
	)
mail=Mail(app)

#Creating the clients to interact with the APIs
twilio_api = TwilioRestClient(credentials.my_twilio_account_sid, credentials.my_twilio_auth_token)
indeed_api = IndeedClient(publisher = credentials.my_indeed_publisher_id)
shortener = Shortener('Tinyurl', timeout=86400)

def FindAndDeliverJobs():
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    for user in user_list:
        #add to for loop, if user['confirmed']==1
        if user['confirmed'] == 1:
            params = {
                'q': user['search_query'], #query_param
                'l': user['query_location'],
                'userip': user['user_ip'], #this might be a little tough to circumvent, maybe pull data from the form when signing up for NowPosted?
                'useragent': user['user_agent'], #use my own computers credentials?
                'fromage': 1,
                'limit': 25
            }
            indeed_response = indeed_api.search(**params)
            job_delivery = "Here are today's postings for " + user['search_query'] +  ":\n\n"
            full_job_delivery = ""
            for job in indeed_response['results']:
                if(len(job_delivery) + len(job['jobtitle'] + " at " + job['company'] + ": \n" + shortener.short(job['url']) + "\n\n") < 1600):
                    job_delivery += job['jobtitle'] + " at " + job['company'] + ": \n" + shortener.short(job['url']) + "\n\n"
                else:
                    twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body=job_delivery)
                    full_job_delivery += job_delivery
                    job_delivery = job['jobtitle'] + " at " + job['company'] + ": \n" + shortener.short(job['url']) + "\n\n"
            if len(job_delivery + "To remove yourself from this service, text back the word 'remove'.") < 1600:
                job_delivery += "To remove yourself from this service, text back the word 'remove'."
                twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body=job_delivery)
            else:
                twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body=job_delivery)
                twilio_api.messages.create(to=user['phone_number'], from_=credentials.my_twilio_number, body="To remove yourself from this service, text back the word 'remove'.")
            full_job_delivery += job_delivery + "To remove yourself from this service, text back the word 'remove'."
            print("{\n" + full_job_delivery + "\n} " + " sent to: " + user['phone_number'])

        else:
            user_list = [kept_user for kept_user in user_list if kept_user != user]
            with open('user_info.json', "w") as write_file:
                json.dump(user_list, write_file)
            print(user['phone_number'] + " has been removed from the userbase")


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=FindAndDeliverJobs, trigger=IntervalTrigger(seconds=86400), id='printing_job', name='Finds and delivers jobs to all users', replace_existing=True)
atexit.register(lambda: scheduler.shutdown())

@app.route("/", methods=['GET', 'POST'])
def DefaultRequestHandler(name=None):

    if request.method == 'GET':
        return render_template('home.html', name=name)
    elif request.method == 'POST':
        user_ip = request.environ['REMOTE_ADDR']
        user_agent = request.headers['User-Agent']
        phone_number = request.form['phone_number']
        query = request.form['search_query']
        location = request.form['query_location']

        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        user_list.append({'user_ip': user_ip, 'user_agent': user_agent, 'phone_number': phone_number, 'search_query': query, 'query_location': location, 'confirmed': 0})

        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

        twilio_api.messages.create(to=phone_number, from_=credentials.my_twilio_number, body="You've registered for NowPosted! To confirm your number, text back the word 'confirm'.")

        return render_template('thankyou.html',name=name)

@app.route("/message", methods=['GET', 'POST'])
def MessageRequestHandler(name=None):
    now_confirmed = False
    message_number = request.values.get('From')

    if "remove" in request.values.get('Body').lower():
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        user_list = [user for user in user_list if user['phone_number'] not in message_number]

        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

        twilio_api.messages.create(to=message_number, from_=credentials.my_twilio_number, body="You have successfully unsubscribed from NowPosted. You will not receive any more postings.")

    elif "confirm" in request.values.get('Body').lower():
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        for user in user_list:
            if user['phone_number'] in message_number:
                user['confirmed'] = 1
                now_confirmed = True

        if now_confirmed:
            with open('user_info.json', "w") as write_file:
                json.dump(user_list, write_file)
            twilio_api.messages.create(to=message_number, from_=credentials.my_twilio_number, body="You have successfully been comfirmed. You will now receive postings every morning!")

        else:
            twilio_api.messages.create(to=message_number, from_=credentials.my_twilio_number, body="It seems you haven't registered with NowPosted, please visit https://nowpostedfor.me to register.")

    elif "info" in request.values.get('Body').lower() and credentials.my_phone_number in message_number:
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

        userbase_message = "Here are the current users of NowPosted: \n\n"

        for user in user_list:
            userbase_message += user['phone_number'] + ": " + user['search_query'] + "\n"

        message_gmail = Message(
            'Current Users',
            sender= credentials.my_email_username,
            recipients=[credentials.my_email_username])
    	message_gmail.body = userbase_message
    	mail.send(message_gmail)

    else:
        twilio_api.messages.create(to=message_number, from_=credentials.my_twilio_number, body="To confirm yourself with this service, text back the word 'confirm'. To remove yourself from this service, text back the word 'remove'.")

    return ""


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

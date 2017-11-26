#Importing flask variables for a server side application
from flask import Flask, request, session, render_template, flash, url_for, redirect
from flask_mail import Mail, Message

#Importing APIs/Libs
from twilio.rest import TwilioRestClient #Twilio
import twilio.twiml #Twilio
from indeed import IndeedClient #Indeed
from pyshorteners import Shortener #TinyURL shortening

#Importing the credentials for the various APIs and libs used
from credentials import (my_email_username, my_email_password,
                         my_twilio_account_sid, my_twilio_auth_token,
                         my_indeed_publisher_id, secret_key)
from email_token import generate_confirmation_token, confirm_token

#For json parsing and creation if we need it
import json

#Imports for time based scheduling
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

#Application setup.
app = Flask(__name__, template_folder='templates', static_url_path='/static/')
app.config.from_object(__name__)

#This is for the mail client, by which we will be able to get user base updates
app.config.update(
	DEBUG=True,
	#Email settings
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = my_email_username,
	MAIL_PASSWORD = my_email_password
	)
mail=Mail(app)

#Creating the clients to interact with the APIs
twilio_api = TwilioRestClient(my_twilio_account_sid, my_twilio_auth_token) #Twilio
indeed_api = IndeedClient(publisher = my_indeed_publisher_id) #Indeed

#Client to shorten links with TinyURL
shortener = Shortener('Tinyurl', timeout=86400)

def FindAndDeliverJobs():
    FindAndDeliverPhoneJobs()
    FindAndDeliverEmailJobs()

# Phone
def FindAndDeliverPhoneJobs():
    #Opening up the json file with all the users for reading
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    #Loop to iterate through every user inside the json file
    for user in user_list:
	#Only look up jobs for the user if they have confirmed their number
        if user['confirmed'] == 1:
	    #Initializing the parameters for the Indeed search using the users preferences
            params = {
                'q': user['search_query'],
                'l': user['query_location'],
                'userip': user['user_ip'],
                'useragent': user['user_agent'],
                'fromage': 1,
                'limit': 25
            } #All of the previous parameters are derived from the initial registration form the user fills out when they sign up
            indeed_response = indeed_api.search(**params) #Using the Indeed client to search for matching jobs

	    #Declaration and initialization of the eventual text message with jobs to send to user
            job_delivery = ("Here are today's postings for ",
                            user['search_query'], ":\n\n")
            full_job_delivery = ""

	    #Loop to iterate through every job in the results for the specific user
            for job in indeed_response['results']:
		#TinyURL shortening
                short_link = shortener.short(job['url'])

		#Continue to concatenate to message if satisfies the <1600 char limit
                if(len(job_delivery) + len(job['jobtitle'] + " at " + job['company'] + ": \n" + short_link + "\n\n") < 1600):
                    job_delivery += job['jobtitle'] + " at " + job['company'] + ": \n" + short_link + "\n\n"

	        #Otherwise send message currently have
                else:
                    twilio_api.messages.create(to=user['phone_number'], from_=my_twilio_number, body=job_delivery)
                    full_job_delivery += job_delivery
                    job_delivery = job['jobtitle'] + " at " + job['company'] + ": \n" + short_link + "\n\n"

            #Final message handling, to send final message
            if len(job_delivery + "To remove yourself from this service, text back the word 'remove'.") < 1600:
                job_delivery += "To remove yourself from this service, text back the word 'remove'."
                twilio_api.messages.create(to=user['phone_number'], from_=my_twilio_number, body=job_delivery)
            else:
                twilio_api.messages.create(to=user['phone_number'], from_=my_twilio_number, body=job_delivery)
                twilio_api.messages.create(to=user['phone_number'], from_=my_twilio_number, body="To remove yourself from this service, text back the word 'remove'.")
	    #Disclaimer to send
            full_job_delivery += job_delivery + "To remove yourself from this service, text back the word 'remove'."
            print("{\n" + full_job_delivery + "\n} " + " sent to: " + user['phone_number'])

        #If user has not confirmed their number, their number is removed from the json file
        else:
            user_list = [kept_user for kept_user in user_list if kept_user != user]
            with open('user_info.json', "w") as write_file:
                json.dump(user_list, write_file)
            print(user['phone_number'] + " has been removed from the userbase")

# Email
def FindAndDeliverEmailsJobs():
    #Opening up the json file with all the users for reading
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    #Loop to iterate through every user inside the json file
    for user in user_list:
	#Only look up jobs for the user if they have confirmed their number
        if user['confirmed'] == 1:
	    #Initializing the parameters for the Indeed search using the users preferences
            params = {
                'q': user['search_query'],
                'l': user['query_location'],
                'userip': user['user_ip'],
                'useragent': user['user_agent'],
                'fromage': 1,
                'limit': 25
            } #All of the previous parameters are derived from the initial registration form the user fills out when they sign up
            indeed_response = indeed_api.search(**params) #Using the Indeed client to search for matching jobs

	    #Declaration and initialization of the eventual text message with jobs to send to user
            email_delivery = job_delivery = ("Here are today's postings for ",
                                             user['search_query'], ":\n\n")
            print email_delivery, job_delivery
            full_job_delivery = ""

	    #Loop to iterate through every job in the results for the specific user
            for job in indeed_response['results']:
		#TinyURL shortening
                short_link = shortener.short(job['url'])

                email_delivery += job['jobtitle'] + " at " + job['company'] + ": \n" + short_link + "\n\n"

            # Send email to users
            message_gmail = Message("NowPosted: today's postings!",
                                    sender= my_email_username,
                                    recipients=[user['email']])
            message_gmail.body = email_delivery
            mail.send(message_gmail)
            print("{\n" + email_delivery + "\n} " + " sent to: " + user['email'])

        #If user has not confirmed their number, their number is removed from the json file
        else:
            user_list = [kept_user for kept_user in user_list if kept_user != user]
            with open('user_info.json', "w") as write_file:
                json.dump(user_list, write_file)
            print(user['email'] + " has been removed from the userbase")


#These lines of code allow for the daily triggering of the job search/delivery function
scheduler = BackgroundScheduler()
scheduler.start()
#The seconds for the IntervalTrigger is 86400 because that is the amount of seconds in a day
scheduler.add_job(func=FindAndDeliverJobs, trigger=IntervalTrigger(seconds=86400),
                  id='find_and_deliver_jobs', name='Finds and delivers jobs to all users', replace_existing=True)
atexit.register(lambda: scheduler.shutdown())


#Flask route for both GET and POST request for our standard endpoint
@app.route("/", methods=['GET', 'POST'])
#Handler for both GET and POST
def DefaultRequestHandler(name=None):
    #On a standard GET request, render out the website to the browser
    if request.method == 'GET':
        return render_template('home.html', name=name)

    #On a POST request (from the form on the website) render out the 'Thank You!' page and register the user into the user json file using the form elements
    elif request.method == 'POST':

	#Saving the form values into variables for saving later
        user_ip = request.environ['REMOTE_ADDR']
        user_agent = request.headers['User-Agent']
        email = request.form['email']
        phone_number = request.form['phone_number']
        query = request.form['search_query']
        location = request.form['query_location']

	#Opening up the user json file for reading and saving the current users into a dictionary
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

	#Adding the new user into the dictionary
        new = not user_list
        confirmed = 0
        for user in user_list:
            if user['phone_number'] == phone_number and user['email'] == email:
                confirmed = user['confirmed']
                if user['search_query'] == query and user['query_location'] == location:
                    new = False
                else:
                    new = True

        print new
        if new:
            user_list.append({'user_ip': user_ip, 'user_agent': user_agent,
                              'email': email, 'phone_number': phone_number,
                              'search_query': query, 'query_location': location,
                              'confirmed': confirmed})
            #Opening up the user json file for writing and then writing the dictionary with the new user into it as json
            with open('user_info.json', "w") as write_file:
                json.dump(user_list, write_file)

            if confirmed == 0:
                email_confirmation(email)
                text_confirmation(phone_number)

	#'Thank You' page rendered for browser
        return render_template('thankyou.html',name=name)

def text_confirmation(number):
    #Send a text message to the new user asking for confirmation
    twilio_api.messages.create(to=number, from_=my_twilio_number,
                               body="You've registered for NowPosted! To confirm your number, text back the word 'confirm'.")

def email_confirmation(email):
    print email
    token = generate_confirmation_token(email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('email.html', confirm_url=confirm_url)
    # Send email to new user
    message_gmail = Message("You've registered for NowPosted!",
                            sender= my_email_username,
                            recipients=[email])
    message_gmail.html = html
    mail.send(message_gmail)


#Flask route for both GET and POST request for inbound text messages to our Twilio number (The one put into our Twilio account)
@app.route("/message", methods=['GET', 'POST'])
#Handler for incoming SMS GET and POST and Admin actions
def MessageRequestHandler(name=None):
    now_confirmed = False #Variable used to confirm users
    message_number = request.values.get('From') #Number of incoming SMS

    #User seeking to remove self from list of users
    if "remove" in request.values.get('Body').lower():

	#Opening up the user json file for reading and saving the current users into a dictionary
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

	#Saves the array WITHOUT users that match the given phone number
        user_list = [user for user in user_list if user['phone_number'] not in message_number]

	#Opening up the user json file for writing and then writing the dictionary with the new user into it as json
        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

	#Confirmation message of successful unsubscription
        twilio_api.messages.create(to=message_number, from_=my_twilio_number,
                                   body="You have successfully unsubscribed from NowPosted. You will not receive any more postings.")

    #User seeking to confirm self into list of users
    elif "confirm" in request.values.get('Body').lower():

	#Opening up the user json file for reading and saving the current users into a dictionary
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

	#For every user, set the confirm attribute to 1
        for user in user_list:
            if user['phone_number'] in message_number:
                user['confirmed'] = 1
                now_confirmed = True

	#If user was successfully confirmed
        if now_confirmed:
	    #Opening up the user json file for writing and then writing the dictionary with the new user into it as json
            with open('user_info.json', "w") as write_file:
                json.dump(user_list, write_file)
            twilio_api.messages.create(to=message_number, from_=my_twilio_number,
                                       body="You have successfully been confirmed. You will now receive postings every morning!")

	#Case where user has not registered yet, inform them of that and give a link
        else:
            twilio_api.messages.create(to=message_number, from_=my_twilio_number,
                                       body="It seems you haven't registered with NowPosted, please visit https://nowpostedfor.me to register.")

    #Admin action to get user list
    elif "users" in request.values.get('Body').lower() and my_phone_number in message_number:

	#Opening up the user json file for reading and saving the current users into a dictionary
        with open('user_info.json', "r") as load_file:
            user_list = json.load(load_file)

	#Email message initialization
        userbase_message = "Here are the current users of NowPosted: \n\n"

	#Storing all users into the message, separated by new lines
        for user in user_list:
            userbase_message += user['phone_number'] + ": " + user['search_query'] + "\n"

	#Generating the email using flask_mail
        message_gmail = Message('Current Users', sender= my_email_username,
                                recipients=[my_email_username]) #Creating the email with the correct credentials
        message_gmail.body = userbase_message #Storing the message into the body of the email
        mail.send(message_gmail) #Sending the email
        twilio_api.messages.create(to=message_number, from_=my_twilio_number,
                                   body="User info was sent to the email in credentials.py") #Confirmation via twilio

    #Admin action to send out messages regardless of state of server
    elif "override" in request.values.get('Body').lower() and my_phone_number in message_number:
        FindAndDeliverJobs()
        twilio_api.messages.create(to=message_number, from_=my_twilio_number,
                                   body="Daily function has been called and users have had their new jobs sent.")

    else:
        twilio_api.messages.create(to=message_number, from_=my_twilio_number,
                                   body="To confirm yourself with this service, text back the word 'confirm'. To remove yourself from this service, text back the word 'remove'.")
    return ""

@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    #Opening up the user json file for reading and saving the current users into a dictionary
    with open('user_info.json', "r") as load_file:
        user_list = json.load(load_file)

    #For every user, set the confirm attribute to 1
    for user in user_list:
        if user['email'] in email:
            if user['confirmed'] == 1:
                flash('Email already confirmed!', 'success')
                now_confirmed = False
            else:
                user['confirmed'] = 1
                now_confirmed = True

    #If user was successfully confirmed
    if now_confirmed:
        #Opening up the user json file for writing and then writing the dictionary with the new user into it as json
        with open('user_info.json', "w") as write_file:
            json.dump(user_list, write_file)

        # Send email to confirmed user
        message_gmail = Message("Your email has been confirmed!",
                                sender= my_email_username,
                                recipients=[email])
        message_gmail.body = ("Thank you for confirming your email. You will now receive job postings every morning!")
        mail.send(message_gmail)
        flash('Email confirmed! You will now receive daily job postings!', 'success')
    return redirect(url_for('DefaultRequestHandler'))

#use_reloader property set to false so that the Flask server does not execute the scheduled code twice!
if __name__ == "__main__":
    app.secret_key = secret_key
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, use_reloader=False)

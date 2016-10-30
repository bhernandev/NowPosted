# NowPosted
A Twilio and Indeed based service that regularly sends SMS messages when a given desired position on Indeed opens. Implemented in Python.

![NowPosted_Demo_1](http://i.imgur.com/dgaL2c2l.jpg) 
![NowPosted_Demo_2](http://i.imgur.com/pml4Vjml.png)

## Setup
#####\*NowPosted was implemented and tested in Python 3.5 only. Other versions of Python may not work.\*
<br />
Clone this repository with the following command in terminal.
```Shell
git clone https://github.com/bhernandez-cs/NowPosted.git
```
Within terminal and inside the project folder, install the necessary libraries and APIs that are required by NowPosted. A virtual environment is a good idea!
```Shell
pip install -r requirements.txt
```
Create a new file titled 'credentials.py' that will host your personal credentials for the Twilio API and the Clarifai API. Inside of your 'credentials.py' file should be the following:
```Python
#You can find/get Twilio credntials at https://www.twilio.com/console
account_sid = "YOUR TWILIO ACCOUNT SID"
auth_token = "YOUR TWILIO AUTH TOKEN"
my_twilio_number = "YOUR TWILIO PHONE NUMBER"

my_indeed_publisher_id = "Your INDEED PUBLISHER ID"
```

## Usage
Start the Flask NowPosted server with the following command inside of the project folder in terminal.
```Shell
python WantON.py
```
The server will serve up all of the static HTML and CSS files by default. However, you'll need to let Twilio find your server to send and respond to messages appropriately. You can use any of the following services, I recommend ngrok!
<ul>
<li><a href="https://ngrok.com/">ngrok</a></li>
<li><a href="http://devcenter.heroku.com/articles/python">Heroku</a></li>
<li><a href="http://flask.pocoo.org/snippets/65/">Webfaction</a></li>
<li><a href="http://flask.pocoo.org/docs/deploying/">Apache,FastCGI, or uWSGI</a></li>
<li><a href="http://flask.pocoo.org/snippets/48/">Dotcloud</a></li>
</ul>

Once you have an <b>online</b> server endpoint, visit the settings for your Twilio phone number at https://www.twilio.com/console and enter your endpoint: 

![Setup_1](http://i.imgur.com/zxZOIzY.png)

Save these settings, visit the endpoint for your server on any browser to sign up, and get you and your friends NowPosted daily!

## Drawbacks
 <ul>
 <li>Links are rather long which is not inherently a problem until you have to pay Twilio for eachc message of up to 1600 characters :(</li>
</ul>

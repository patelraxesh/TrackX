from flask import Flask, request, render_template
from flask_ask import Ask, statement, question, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pprint import pprint
from firebase import firebase
from time import gmtime, strftime
import requests
import json
import time
import random
import datetime
import calendar
import re

firebase = firebase.FirebaseApplication("https://trackx-94915.firebaseio.com/")

ACCOUNT_SID = "AC2bfb2dfdd42e75f169ca972319bec121"
AUTH_TOKEN = "e511f9c1afaa564be32425e900a3265b"
TWILIO_NUMBER = "+16178906207"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

app = Flask(__name__)
ask = Ask(app, "/")

expense_report = {}

def check_budget():
	ph_number_in = session.attributes['number']
	new_data = firebase.get("/user", ph_number_in)
	if ((float(new_data['set_budget']) - float(new_data['Balance'])) < 100) and (float(new_data['set_budget']) > float(new_data['Balance'])):
		add_text = 'Also note that, you are about to reach your budget limit of this month of '+str(new_data['set_budget'])+' Dollars.'
		return str(add_text)
	elif (float(new_data['set_budget']) < float(new_data['Balance'])):
		difference = float(new_data['Balance']) - float(new_data['set_budget'])
		client.messages.create(to='+18577536691', from_=TWILIO_NUMBER, body="Courtesy notification. Your expenses have exceeded the set budget limit. Visit http://mytrackx.herokuapp.com for detailed report.")
		add_text = 'Also note that, you have exceeded your budget limit of this month by '+str(difference)+' Dollars. Check SMS for details.'
		return str(add_text)
	else:
		return " "

def path_join(*parts):
	return ''.join('/' + str(part).strip('/') for part in parts if part)

@app.route("/")
def doc_profile():
	return render_template("mdp.html")

@app.route("/sms", methods=['POST'])
def hello():
	in_text = request.form["Body"]
	ph_number = request.form["From"]
	in_text = in_text.lower()
	out_text = get_response(in_text, ph_number)
	response = MessagingResponse()
	response.message(out_text)
	return str(response)

def get_response(input_str_old, ph_number):
	'''
    Get the response output from input
    '''
	input_str = input_str_old.lower()
	input_words = input_str.split()
	ph_number_in = ph_number[1:]
	print ph_number_in
	# Greetings
	welcome = ["hi", "hello", "hey", "whatsup"]
	reset = ["reset"]
	# Food inputs
	food_input = ['groceries', 'grocceries', 'grocery', 'milk', 'bread', 'coffee', 'egg', 'chicken', 'sugar', 'protien bar', 'coke', 'vegetables', 'salad', 'restaurants', 'food']

	if any(x in input_str for x in food_input):
		changed_items = []
		for item in food_input:
			if item in input_str:
				changed_items.append(item)
		if changed_items:
			values = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
			if values:
				users = firebase.get("/user", None)
				if ph_number_in in users.keys():
					new_balance = firebase.get("/user", ph_number_in)
				else:
					new_value = firebase.put("/user", ph_number_in, {"Balance": 0, "set_budget": 500})
					new_balance = firebase.get("/user", ph_number_in)
				for i in range(len(values)):
					new_balance['Balance'] += float(values[i])
					values[i] = "$"+str(values[i])
					out_text = "Expense added for "+  ', '.join(str(p) for p in changed_items) + " : + " + ' + '.join(str(p) for p in values)
				new_value = firebase.put("/user", ph_number_in, new_balance)
			out_text += "\nTotal Expenses : " + str(new_balance['Balance'])
			return out_text
	elif any(x in input_str for x in reset):
		new_value = firebase.put("/user", ph_number_in, {"Balance": 0, "set_budget": 500})
		out_text = "Total Expense reset to 0"
		return out_text
	elif any(x in input_str for x in welcome):
		out_text = "Hello, Welcome to TrackX, Your Expense tracker. How could i help you today?"
		return out_text
	else:
		None
	return "I did not understand you."

@ask.launch
def start_skill():
	session.attributes['question'] = "start"
	output_txt = 'Hello, Welcome to Track X, Your Personal Expense tracker. Please enter 4 digit Pin number to access your account'
	return question(output_txt)


@ask.intent("phone_number")
def phone_number(mynumber):
	session.attributes['number'] = "18577536691"
	session.attributes['question'] = "phone_number"
	output_txt = 'Hi Anubhav, How can i help you today? You can ask me to "Record Expense", "Budget Status" or "Financial suggestion".'
	return question(output_txt)


@ask.intent("Record_Expense")
def Record_Expense_food():
	session.attributes['question'] = "record_expense"
	output_txt = 'Sure. You can tell me something like "add 6 dollar for Apple" or "12 dollar for cake."'
	return question(output_txt)


@ask.intent("Record_Expense_food")
def Record_Expense_food(number, food):
	session.attributes['number'] = "18577536691"
	ph_number_in = session.attributes['number']
	session.attributes['question'] = "expense_added"
	new_balance = firebase.get("/user", ph_number_in)
	if food == None:
		food = "Other Expenses"
	if number == None:
		return question("Expense not Recorded." + " Please tell me your expense again.")
	if number:
		new_balance['Balance'] += float(number)
		new_value = firebase.put("/user", ph_number_in, new_balance)
		output_txt = 'Expense added of '+ str(number) + " Dollars for " + food + ". Total expense of the month is " + str(new_balance['Balance']) + " Dollars. "
		add_text = check_budget()
		return question(output_txt + add_text + " Do you have any other questions for me?")
	else:
		return question("Expense not Recorded." + " Please tell me your expense again.")


@ask.intent("Budget_Status")
def Budget_Status():
	session.attributes['number'] = "18577536691"
	ph_number_in = session.attributes['number']
	session.attributes['question'] = "Budget_status"
	new_balance = firebase.get("/user", ph_number_in)
	difference = float(new_balance['set_budget']) - float(new_balance['Balance'])
	if difference > 0:
		output_txt = "Your expense for this month uptill now are " + str(new_balance['Balance']) + " Dollars. You have only " + str(difference) + " Dollars left to spend in your budget."
	else:
		output_txt = "Your total expenses for this month are" + str(new_balance['Balance']) + " Dollars. You have already exceeded your budget for this month by " + str((0-difference))+ " Dollars."
		client.messages.create(to='+18577536691', from_=TWILIO_NUMBER, body="Courtesy notification. Your expenses have exceeded the set budget limit. Visit http://mytrackx.herokuapp.com for detailed report. ")
		return question(output_txt+ ". Do you want me to connect with your financial advisor?")
	return question(output_txt+ ". Do you have any other questions for me?")


@ask.intent("Financial_Suggestions")
def Financial_Suggestions():
	session.attributes['number'] = "18577536691"
	ph_number_in = session.attributes['number']
	session.attributes['question'] = "other"
	new_balance = firebase.get("/user", ph_number_in)
	last_month = 440
	difference = float(new_balance['Balance']) - last_month
	if difference > 0:
		current_diff = float(new_balance['Balance']) - float(new_balance['set_budget'])
		if current_diff > 0:
			session.attributes['question'] = "Budget_status"
			output_txt = "Last month you managed your finances with a budget of " + str(last_month) + " dollars. However, this month you are running overbudget by " + str(current_diff) + " Dollars. Check SMS for details. Would you like me to connect your financial advisor?"
			client.messages.create(to='+18577536691', from_=TWILIO_NUMBER, body="Courtesy notification. Your expenses have exceeded the set budget limit. Visit http://mytrackx.herokuapp.com for detailed report. ")
			return question(output_txt)
		else:
			output_txt = "Last month you managed your finances with a budget of " + str(last_month) + " dollars.  Moreover, this month you are wonderfully manging your budget with Total expenses of "+str(new_balance['Balance'])+" Dollars."
			return question(output_txt+ ". Is there anything else i can help you with?")
	else:
		output_txt = "Last month you managed your finances with a budget of " + str(last_month) + " dollars.  Moreover, this month you are wonderfully manging your budget with Total expenses of "+str(new_balance['Balance'])+" Dollars."
		return question(output_txt+ ". Is there anything else i can help you with?")

@ask.intent("Set_Budget")
def Set_Budget(budget):
	session.attributes['number'] = "18577536691"
	ph_number_in = session.attributes['number']
	session.attributes['question'] = "other"
	new_balance = firebase.get("/user", ph_number_in)
	if budget == None:
		output_txt = "Sorry I did not get that. Say something like 'set my budget to 500 dollars'."
		return question(output_txt)
	else:
		new_balance['set_budget'] = budget
		print new_balance
		new_value = firebase.put("/user", ph_number_in, new_balance)
		output_txt = "Your budget for the month is set to " +str(budget)+ " Dollars."
		return question(output_txt+ ". Is there anything else i can help you with?")


@ask.intent("No_intent")
def No_intent():
	if "question" in session.get('attributes', {}):
		if session.attributes['question'] == "Budget_status":
			output_txt = "You can ask me to Record Expense, Budget Status, Financial suggestion."
			return question(output_txt)
		else:
			output_txt = "Thanks for using Track X powered by J P Morgan. Have a Good day!"
			return statement(output_txt)
	output_txt = "Thanks for using Track X powered by J P Morgan. Have a Good day!"
	return statement(output_txt)

@ask.intent("Yes_intent")
def Yes_intent():
	if "question" in session.get('attributes', {}):
		if session.attributes['question'] == "Budget_status":
			call = client.calls.create(to='+18574520056', from_=TWILIO_NUMBER,
                               url="http://demo.twilio.com/docs/voice.xml")
			output_txt = "Calling Mr. Andrew, your financial advisor at J P Morgan."
			return statement(output_txt)
		else:
			output_txt = "You can ask me to Record Expense, Budget Status, Financial suggestion."
	else:
		output_txt = "You can ask me to Record Expense, Budget Status, Financial suggestion."
	return question(output_txt)


if __name__ == '__main__':
    app.run(debug=True)

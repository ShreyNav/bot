import json
import logging
import boto3
import requests
import os
from time import sleep
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set these config values in the serverless.yml file
authToken = os.environ.get('AUTHTOKEN')
ec2quota = os.environ.get('EC2QUOTA')
ami = os.environ.get('AMI')
ec2type = os.environ.get('EC2TYPE')
snsARN = os.environ.get('SNSARN')
SG = os.environ.get('SG')
KEYPAIR = os.environ.get('KEYPAIR')
ACCID = os.environ.get('ACCID')
BUDGETNAME = os.environ.get('BUDGETNAME')


# Process incoming SNS message
def dispatch(event, context):
	data = json.loads(event['Records'][0]['Sns']['Message'])
	logger.info('dispatch - SNS got message: ' + str(data))
	
	req = str(data['Req'])
	target = str(data['Target'])
	chan = str(data['Chan'])
	user = str(data['User'])

	body = {
		"message": "SNS function executed successfully!", "input": event
	}

	response = {
 		"statusCode": 200, "body": json.dumps(body)
	}
	#slackpost("SNS Dispatcher test - Incoming Request type: " + req + ", (optional) target=" + target + " for user: " + user + " in " + chan, chan)
	
	# Process request
	if 'newec2' in req:
		createEC2(user, chan)
		return
	elif 'getBudget' in req:
		getBudget(user, chan)
		return
	elif 'termec2' in req:
		terminateEC2(target, user, chan)
		return
	else:
		logger.error('Request not identified correctly')
		return
	return response


# Create a new EC2 instance    
def createEC2(username, chan):
    logger.info('CreateE2 - started for ' + username + ' in ' + chan)

    # Check if user is over their quota first
    ec2 = boto3.client('ec2')  
    filters = [
        {'Name': 'tag:CreatedBy', 'Values': ['robots', 'script']},
        {'Name': 'tag:Username', 'Values': [username]},
        {'Name': 'instance-state-name', 'Values': ['pending', 'stopped', 'running']}
        ]
    vms = ec2.describe_instances(Filters=filters)  
    count = str(len(vms['Reservations'])); countInt = int(count)

    if (countInt >= int(ec2quota)):
        slackpost(slackUserName(username).split()[0] + ", you reached your EC2 instance limit! You currently have *" + count + "* EC2 instances. Your quota is " + ec2quota + ".", chan)
        return
 
    # Create new EC2 instance
    ec2 = boto3.resource('ec2')
    genInstance = ec2.create_instances(
        ImageId=ami, 
        MinCount=1, 
        MaxCount=1, 
        InstanceType=ec2type,
        KeyName=KEYPAIR,
        SecurityGroups=[SG])
    instance = genInstance[0]

    slackpost("Creating your new EC2 instance, " + slackUserName(username).split()[0] + ". I will let you know when it's online!", chan)

    # Assign tag to instance
    ec2.create_tags(Resources=[instance.id], Tags=[{'Key':'Username', 'Value':username}, {'Key':'CreatedBy', 'Value':'robots'}])

    # Wait for the instance to enter the running state
    instance.wait_until_running()

    # Reload the instance attributes and send instance details to user
    instance.load()
    sleep(2) # Gives the VM a couple of seconds to boot
    slackpost(slackUserName(username).split()[0] + ", your new EC2 instance is now *online*! You can connect with:\n ssh -i " + KEYPAIR + ".pem ec2-user@" + instance.public_dns_name, chan)
    return('OK')


# Terminate EC2 instance
def terminateEC2(id, username, chan):
	logger.info('terminateEC2 - started for instance ID ' + id + ' in ' + chan)

	ec2 = boto3.client('ec2')
	# Check if instance ID is owned by user first!
	filters = [
		{'Name': 'tag:CreatedBy', 'Values': ['robots', 'script']},
		{'Name': 'tag:Username', 'Values': [username]},
		{'Name': 'instance-state-name', 'Values': ['pending', 'stopped', 'running']}
		]
	vms = ec2.describe_instances(Filters=filters)  

	for r in vms['Reservations']:
		for i in r['Instances']:
			if i['InstanceId'] in id:
				ec2 = boto3.resource('ec2')
				ec2.instances.filter(InstanceIds=[id]).terminate()
				slackpost(slackUserName(username).split()[0] + ", " + "I terminated EC2 instance " + id, chan)
				return
	return


# Post current budget info to slack
def getBudget(user, chan):
    logger.info('getBudget for account: ' + ACCID + ' on budget named ' + BUDGETNAME)
    client = boto3.client('budgets')
    res = client.describe_budget(AccountId=ACCID, BudgetName=BUDGETNAME)
    
    #Get budget details
    limit = str(res['Budget']['BudgetLimit']['Amount'])[:7]
    act = str(res['Budget']['CalculatedSpend']['ActualSpend']['Amount'])[:7]
    forecast = str(res['Budget']['CalculatedSpend']['ForecastedSpend']['Amount'])[:7]
    
    #Post billing info to Slack
    slackpost("Billing report! Monthly AWS budget of $" + limit + '.\n\nActual spend so far this month: $' + act + '. Forecast spend for this month: $' + forecast + '.', chan)


# Function for posting a message to slack channel
def slackpost(msg, chan):
    method = "https://slack.com/api/chat.postMessage"   #https://api.slack.com/methods/chat.postMessage
    slack_data = {'channel': chan, 'text': msg}
    response = requests.post(
        method, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken}
    )
    return response 


## Small/helper functions 
# Function for getting a real name from Slack user ID
def slackUserName(id):
    #logger.info('Running get user info')
    method = "https://slack.com/api/users.info?user=" + id
    response = requests.get(
        method,
        headers={'Content-Type': 'Content-type: application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + authToken}
    )
    json_data = json.loads(response.text)
    name = json_data['user']['real_name']
    logger.info('slackUserName - ' + str(name))
    return str(name)

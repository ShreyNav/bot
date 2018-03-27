import json
import logging
import boto3
import requests
import os
import random
from threading import Thread
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set these config values in the serverless.yml file
authToken = os.environ.get('AUTHTOKEN')
ec2quota = os.environ.get('EC2QUOTA')
ami = os.environ.get('AMI')
ec2type = os.environ.get('EC2TYPE')
snsARN = os.environ.get('SNSARN')


# Entry point for processing Slacks events 
def slackEvent(event, context):
    data = json.loads(event['body'])
    response = {"statusCode": 200,}

    # Slack Event Subscriptions API Challenge/Response
    if 'challenge' in data:
        response = {"statusCode": 200, "body": data['challenge']}; return response

    chan = str(data['event']['channel'])
    user = str(data['event']['user'])
    eventID = str(data['event_id'])
    eventText = str(data['event']['text']) 
    logger.info('slackEvent - ' + eventID + ', event text: ' + eventText)
    eventProc(eventText, user, chan)
    return(response)
    

# Main event processor
# Dispatch long running tasks via SNS which triggers other lambdas
# Any functions not dispatched via SNS should return within 3 seconds to stop the Slack API retrying
def eventProc(eventText, user, chan):
    logger.info('eventProc - Processing event: ' + eventText)

    if 'test1' in eventText:
        slackpost("Test 1", chan)
        return
    elif 'test2' in eventText:
        slackpost("Test 2", chan)
        return
    elif 'toss coin' in eventText:
        slackpost(coinToss(), chan)
        return
    elif eventText.endswith('get budget'):
        sns("getBudget", user, chan)
        return
    elif eventText.endswith('whoami'):
        whoami(user, chan)
        return
    elif eventText.endswith('ec2 list'):
        listEC2(user, chan)
        return    
    elif eventText.endswith('ec2 create'):
        sns("newec2", user, chan)
        return
    elif 'ec2 terminate ' in eventText:
        target=eventText.split("terminate ",1)[1]
        sns("termec2", user, chan, target.replace(" ", ""))
        return
    elif eventText.endswith('ec2 terminate'):
        slackpost("You need to provide an instance ID!", chan)          
    else:
        helpText(user, chan)
        return


# Send request asynchronously via SNS Topic 
def sns(req, user, chan, target="none"):
    message = {"Req": req, "Target": target, "User": user, "Chan": chan}
    client = boto3.client('sns')
    logger.info('sns - posting to topic: ' + snsARN)
    response = client.publish(
        TargetArn=snsARN,
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json'
        )
    return


# List users current EC2 instance
def listEC2(username, chan):
    logger.info('Listing EC2 instances')
    ec2 = boto3.client('ec2')  
    filters = [
        {'Name': 'tag:CreatedBy', 'Values': ['robots', 'script']},
        {'Name': 'tag:Username', 'Values': [username]},
        {'Name': 'instance-state-name', 'Values': ['pending', 'stopped', 'running']}
        ]

    vms = ec2.describe_instances(Filters=filters)  
    count = str(len(vms['Reservations'])); countInt = int(count)

    if (countInt < 1):
        slackpost(slackUserName(username).split()[0] + ", you have *" + count + "* EC2 instances. Your quota is " + ec2quota + ".", chan)
        return

    slackpost(slackUserName(username).split()[0] + ", you have *" + count + "* EC2 instances. Your quota is " + ec2quota + ".", chan)

    for r in vms['Reservations']:
      for i in r['Instances']:
        info = str(i['PublicDnsName'] + " (" + i['State']['Name'] + "), Instance ID: " + i['InstanceId'] + ".")
        slackpost(info, chan)


# Just for fun
def coinToss():
    flip = random.randint(0, 1)
    if (flip == 0):
        return("Heads!")
    else:
        return("Tails!")


## Small/helper functions
# Function for printing help text
def helpText(user, chan):
    helpMessage = "*Unrecognized command!* Available commands: \n\n*ec2 list*\n\n*ec2 create*\n\n*ec2 terminate <instance-id>*\n\n*get budget* \n\n*toss coin*"
    slackpost(helpMessage, chan)
    return

# Function for testing getting a real name from Slack user ID
def whoami(id, chan):
    slackpost("You are " + slackUserName(id).split()[0], chan)

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
    
# Function for posting a message to slack channel
def slackpost(msg, chan):
    method = "https://slack.com/api/chat.postMessage"   #https://api.slack.com/methods/chat.postMessage
    slack_data = {'channel': chan, 'text': msg}
    response = requests.post(
        method, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken}
    )
    return response 

# Function for testing posting to slack
def pingSlack(event, context):
    body = {
        "message": "Test function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    slackpost("Pinging slack", "#aws")
    return response


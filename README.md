# Serverless-AWS-Slack-Bot

## Overview
This project came from my wanting to learn the [serverless](https://www.serverless.com) toolkit and AWS Lambda & CloudFormation technologies.

Integrating with Slack, this is an easily-extensible python framework for controlling with AWS resources via Slack. Currently it allows slack users to provision EC2 instances. 

The entire stack is serverless and stateless. Use of SNS + lambda functions to dispatch long-running tasks means it should scale very well.

&nbsp;

![Diagram](https://raw.githubusercontent.com/richstokes/Serverless-AWS-Slack-Bot/master/diagram.jpg)

&nbsp;


## Screenshot
![Screenshot](https://raw.githubusercontent.com/richstokes/Serverless-AWS-Slack-Bot/master/screenshot.png)

## Bot Commands
Bot commands currently available:

* **@BotName ec2 create**
* **@BotName ec2 list**
* **@BotName ec2 terminate <instance-id>**
* **@BotName get budget**
* **@BotName toss coin**

You can easily add extra commands to the eventProc function inside handler.py


## Installing

### Deployment via serverless

git clone the repo, edit serverless.yml to your specification && sls deploy

### Slack API

After deploying via serverless you will need to give your Slack Apps' Event Subscriptions settings page the slackEvent URL. It will look something like this:

`https://4dbi5xxxx2.execute-api.us-east-1.amazonaws.com/dev/slackEvent`


### Configuration

Everything is controlled via environment variables in the serverless.yml file.

Most of the options will be self-explanatory and are commented, however you will want to pay attention to the following:

**AUTHTOKEN** - must be set to your Slack Bot/App OAuth Access Token

**KEYPAIR** - name of the AWS keypair to use for your EC2 instances

**SG** - name of the AWS security group to use for your EC2 instances



## Notes / TODO list
This was built assuming a trusted Slack environment. Minimal input validation is performed and the IAM policies should be tightend up for a production environment.

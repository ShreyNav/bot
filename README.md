# Serverless-AWS-Slack-Bot

## Overview
This project came from my wanting to learn the [serverless](https://www.serverless.com) toolkit and AWS Lambda & CloudFormation technologies.

Integrating with Slack, this is an easily-extensible python framework for controlling with AWS resources via Slack.

The entire stack is serverless and stateless. Use of SNS + lambda functions to dispatch long-running tasks means it should scale very well!

&nbsp;

![Diagram](https://raw.githubusercontent.com/richstokes/Serverless-AWS-Slack-Bot/master/diagram.jpg)

&nbsp;


## Screenshot
![Screenshot](https://raw.githubusercontent.com/richstokes/Serverless-AWS-Slack-Bot/master/screenshot.png)


## Installing

### Configuration

Everything is controlled via environment variables in the serverless.yml file.


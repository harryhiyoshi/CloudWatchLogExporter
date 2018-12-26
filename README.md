# CloudWatch Log Exporter For New Relic Insights

This is a Lambda function receives log entries from CloudWatch Logs
and pushes them to New Relic Insights as your Custom Event.

Once you export logs to New Relic Insights, you can analyze the statistics of the logs in detail (for example, number of errors in a log file) and also **ALERT IT** with excellent features of New Relic Alerts.

<br>Like this<br>
![Examle of Dashboad](https://github.com/harryhiyoshi/CloudWatchLogExporterForNewRelicInsights/blob/master/NewRelicDashboard.png "Examle of Dashboad")

## Collected metrics
It sends the followings in each log stream based on [log event](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/ValidateLogEventFlow.html).
* owner
* logGroup
* Id
* timestamp
* message

## About Sending Custom Events
The command to send a custom event to New Relic Insights
```
gzip -c example_events.json | curl -X POST -H "Content-Type: application/json" -H "X-Insert-Key: YOUR_KEY_HERE"
-H "Content-Encoding: gzip" https://insights-collector.newrelic.com/v1/accounts/YOUR_ACCOUNT_ID/events --data-binary @-
```
For more detailed documentation, <br>
please see https://docs.newrelic.com/docs/insights/insights-data-sources/custom-data/send-custom-events-event-api

<br>You can see all data in New Relic Insights like this<br>
![all data in Insights](https://github.com/harryhiyoshi/CloudWatchLogExporterForNewRelicInsights/blob/master/NewRelicInsights.png "CustomEventCloudWatchLog")

**NOTE: The default Event Type is defined 'CustomEventCloudWatchLog'.**<br>
It creates CustomEventCloudWatchLog as a custom event on your account in New Relic Insights, and then push logs into the event type. You can change the name to re-define EVENT_TYPE in the source.

## !! IMPORTANT !! PLEASE NOTE
**PLEASE DON'T FORGET THE COSTS** for running Lambda functions. Everything related to this tool must be done by your responsibility.

When you set a log stream to Lambda, you may see this warning.
![Warning](https://github.com/harryhiyoshi/CloudWatchLogExporterForNewRelicInsights/blob/master/Warning.png "Warning on AWS")

## Pre-requisites

- Your account ID in New Relic

- INSERT_KEY on your account in New Relic
Please see the detail. https://docs.newrelic.com/docs/insights/insights-data-sources/custom-data/send-custom-events-event-api#register

- A KMS key to encrypt INSERT_KEY

## Installation

### 1. Create a new Lambda function based on this tool
  1. Login to your AWS console

  2. Create a new lambda function with python 3.6 and a role including 'AWSLambdaBasicExecutionRole.'

  3. Delete the function code of the new Lambda function, and then copy and paste function.py into it

  4. Add **INSERT_KEY** and **ACCOUNT_ID** in environment variables and then set each value

  5. Check 'Enable helpers for encryption in transit.'

  6. Choose the same KMS key in 'AWS KMS key to encrypt in transit' as the one in 'AWS KMS key to encrypt at rest.'

  7. You must encrypt only INSERT_KEY with the KMS key. Please click 'Encrypt' button next to "INSERT_KEY."


### 2. Stream CloudWatch logs to the Lambda

  1. Open CloudWatch - Logs

  2. Choose a Log Group and choose Stream to AWS Lambda in Actions

  3. Choose the Lambda Function which you created above in Lambda Function, and then click Next

  4. Choose any Log Format what you prefer

  5. set Subscription Filter Pattern if you want

  6. Click Next and then click Start Straming

  7. Once any logs generated, the Lambda functions start to send them to New Relic Insights

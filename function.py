'''
Copyright 2018 Harry Hiyoshi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import os
import gzip
import json
import time
import boto3
from datetime import datetime


from urllib import request
from io import StringIO
from base64 import b64decode

#Default name of the event type. Change it if you want
EVENT_TYPE='CustomEventCloudWatchLog'

# Retrying configuration.
# Increasing these numbers will make the function longer in case of
# communication failures and that will increase the cost.
# Decreasing these number could increase the probility of data loss.

# Maximum number of retries
MAX_RETRIES = 3
# Initial backoff (in seconds) between retries
INITIAL_BACKOFF = 1
# Multiplier factor for the backoff between retries
BACKOFF_MULTIPLIER = 2


class MaxRetriesException(Exception):
    pass


class BadRequestException(Exception):
    pass


class ThrottlingException(Exception):
    pass


def http_retryable(func):
    '''
    Decorator that retries HTTP calls.

    The decorated function should perform an HTTP request and return its
    response.

    That function will be called until it returns a 200 OK response or 
    MAX_RETRIES is reached. In that case a MaxRetriesException will be raised.

    If the function returns a 4XX Bad Request, it will raise a BadRequestException
    without any retry unless it returns a 429 Too many requests. In that case, it
    will raise a ThrottlingException.
    '''
    def _format_error(e, text):
        return '{}. {}'.format(e, text)

    def wrapper_func():
        backoff = INITIAL_BACKOFF
        retries = 0

        while retries < MAX_RETRIES:
            if retries > 0:
                print('Retrying in {} seconds'.format(backoff))
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER

            retries += 1

            try:
                response = func()

            # This exception is raised when receiving a non-200 response
            except request.HTTPError as e:
                if e.getcode() == 400:
                    raise BadRequestException(
                        _format_error(e, 'Unexpected payload'))
                elif e.getcode() == 403:
                    raise BadRequestException(
                        _format_error(e, 'Review your license key'))
                elif e.getcode() == 404:
                    raise BadRequestException(_format_error(
                        e, 'Review the region endpoint'))
                elif e.getcode() == 429:
                    raise ThrottlingException(
                        _format_error(e, 'Too many requests'))
                elif 400 <= e.getcode() < 500:
                    raise BadRequestException(e)

            # This exception is raised when the service is not responding
            except request.URLError as e:
                print('There was an error. Reason: {}'.format(e.reason))
            else:
                return response

        raise MaxRetriesException()

    return wrapper_func


def _send_log_entry(log_entry, context):

    logs = json.loads(log_entry)

    for log in logs['logEvents']:
        data = {
            'eventType':EVENT_TYPE,
            'owner':logs['owner'],
            'logGroup': logs['logGroup'],
            'logId':log['id'],
            'logCreatedTimestamp': (datetime.fromtimestamp(int(str(log['timestamp'])[:10]))).strftime('%Y%m%d%H%M%S'),
            'message': log['message']        
        }
        print(data)
        
        @http_retryable
        def do_request():
            req = request.Request('https://insights-collector.newrelic.com/v1/accounts/'+ os.environ['ACCOUNT_ID'] + '/events', _get_payload(data))
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-Insert-Key', _get_insert_key())
            req.add_header('Content-Encoding', 'gzip')
            return request.urlopen(req)
    
        try:
            response = do_request()
        except MaxRetriesException as e:
            print('Retry limit reached. Failed to send log entry.')
            raise e
        except BadRequestException as e:
            print(e)
        else:
            print('Log entry sent. Response code: {}'.format(response.getcode()))


def _get_payload(data):
    return gzip.compress(json.dumps(data).encode())

def _get_insert_key():
    kms_client = boto3.client('kms')
    encrypted = os.environ['INSERT_KEY']

    return kms_client.decrypt(CiphertextBlob=b64decode(encrypted)).get('Plaintext')


def lambda_handler(event, context):
    if 'awslogs' in event:        # CloudWatch Log entries are compressed and encoded in Base64
        payload = b64decode(event['awslogs']['data'])
        log_entry = gzip.decompress(payload).decode('utf-8')
        _send_log_entry(log_entry, context)

    else:
        print('Not supported')
        print(event)

# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

from __future__ import print_function
from socket import timeout
import urllib3

import json
import time
from urllib.parse import urlparse, parse_qs
import logging
import os
#Custom Resource helper (https://github.com/aws-cloudformation/custom-resource-helper)
from crhelper import CfnResource

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

helper = CfnResource(json_logging=False, log_level=os.getenv('LOG_LEVEL', 'INFO').upper())
http = urllib3.PoolManager()
current_region = os.environ['AWS_REGION']


#Exception handling classes
class IPAddressNotFound(Exception):
    pass
class InvalidStatusCode(Exception):
    pass


@helper.create
@helper.update
def get_datasync_agent_activation_code(event, context):
    try:
        logger.info("Create/Update event from CloudFormation.")
        logger.info("Received event: " + json.dumps(event, indent=2))
        logger.info("Waiting for 180 seconds to allow EC2 Instance to initialize...")
        time.sleep(180)
        logger.info("Getting DataSync Agent Activation key...")
        
        # Checking if IP Address is passed in event
        if not event['ResourceProperties']['AgentInstanceIPAddress']:
            raise IPAddressNotFound
        
        # Call Agent URL to get activation code
        logger.info("Calling Agent URL to get activation code...")
        agent_ip = event['ResourceProperties']['AgentInstanceIPAddress']
        activationCodeURL = 'http://' + agent_ip
        requestParams={"gatewayType": "SYNC", "activationRegion": current_region, "endpointType" : "PUBLIC"}
        logger.info(f"Activation Code URL: {activationCodeURL}")
        logger.info(f"Requests Parameters Dict: {requestParams}")
        resp = http.request('GET',activationCodeURL,requestParams,redirect=False, timeout=15.00, retries=2)
        
        #Debugging response
        logger.debug(f"Status Code: {resp.status}")
        logger.debug(f"Response headers: {resp.headers}")
        if resp.data:
            logger.debug(f"Full response: {resp.data}")
        
        # Getting Activation Code from response
        if resp.status != 302:
            raise InvalidStatusCode
        logger.info("Getting Activation Code from response...")
        redirectionURL = resp.headers['Location']
        parsed_url = urlparse(redirectionURL)
        activationCode = parse_qs(parsed_url.query)['activationKey'][0]
        logger.info(f"Agent Activation Code: {activationCode}")

        #Setting helper response field for activation code
        helper.Data["AgentActivationCode"] = activationCode
        return activationCode
        
    except IPAddressNotFound:
        logger.error("Agent IP Address not found.")
        helper.Data["AgentActivationCode"] = "IPAddressNotFound"
        return "IPAddressNotFound"
    except InvalidStatusCode:
        logger.error(f"Error in getting response from the AWS DataSync Agent Instance. Invalid Status Code: {str(resp.status)}.")
        helper.Data["AgentActivationCode"] = "InvalidStatus"+str(resp.status)
        return "InvalidStatus"+str(resp.status)
    except Exception:
        logger.error("Unexpected error", exc_info=True)
        helper.Data["AgentActivationCode"] = "NotFound"
        return "NotFound"


@helper.delete
def delete(event, context):
    logger.info("Delete event from CloudFormation.")
    logger.info("Received event: " + json.dumps(event, indent=2))
    pass

def lambda_handler(event, context):
    helper(event, context)
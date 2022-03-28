# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# Based on https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/
# This is used because of a circular dependency limitation in CloudFormmation/CDK: https://github.com/aws-cloudformation/cloudformation-coverage-roadmap/issues/79
from __future__ import print_function
import os
import urllib3
from urllib.parse import urlparse, parse_qs
import logging
#Custom Resource helper (https://github.com/aws-cloudformation/custom-resource-helper)
from crhelper import CfnResource
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

helper = CfnResource(json_logging=False, log_level=os.getenv('LOG_LEVEL', 'INFO').upper())
http = urllib3.PoolManager()
s3 = boto3.resource('s3')

def add_bucket_notification(LambdaArn, Bucket):
    bucket_notification = s3.BucketNotification(Bucket)
    response = bucket_notification.put(
        NotificationConfiguration={
        'LambdaFunctionConfigurations': [
            {
                'LambdaFunctionArn': LambdaArn,
                'Events': [
                    's3:ObjectCreated:*'
                ],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {
                                'Name': 'prefix',
                                'Value': 'adhoc'
                            },
                        ]
                    }
                }
            }
        ]
        }
    )
    logger.info("Add request completed.")
    
def delete_bucket_notification(Bucket):
    bucket_notification = s3.BucketNotification(Bucket)
    response = bucket_notification.put(
        NotificationConfiguration={}
    )
    logger.info("Delete request completed.")

@helper.create
@helper.update
def create_update(event, context):
    try:
        logger.info("Create/Update event from CloudFormation.")
        LambdaArn=event['ResourceProperties']['LambdaArn']
        Bucket=event['ResourceProperties']['Bucket']
        logger.info(f"Adding bucket notification for created objects to lambda {LambdaArn} on bucket {Bucket} ...")
        add_bucket_notification(LambdaArn, Bucket)
        helper.Data['NotificationAdded'] = "Yes"
        helper.Data['Bucket'] = Bucket
        helper.Data['LambdaArn'] = LambdaArn
        return "NotificationAdded"
    except Exception as e:
        logger.error(f"An error ocurred while trying to add the S3 notification.", exc_info=True)
        helper.Data['NotificationAdded'] = "No"
        return "NotificationNotAdded"

@helper.delete
def delete(event, context):
    try:
        logger.info("Delete event from CloudFormation.")
        Bucket=event['ResourceProperties']['Bucket']
        logger.info(f"Deleting bucket notification for created objects on bucket {Bucket} ...")
        delete_bucket_notification(Bucket)
        helper.Data['NotificationDeleted'] = "Yes"
        return "NotificationDeleted"
    except Exception as e:
        logger.error(f"An error ocurred while trying to delete the S3 notification.", exc_info=True)
        helper.Data['NotificationDeleted'] = "No"
        return "NotificationNotDeleted"

def lambda_handler(event, context):
    helper(event, context)
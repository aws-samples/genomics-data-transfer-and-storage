# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import json
import boto3
import os
import logging
import traceback
import sys

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

ds = boto3.client('datasync')
ds_task_arn = os.environ['DATA_SYNC_TASK_ARN']

s3 = boto3.resource('s3')
 
def lambda_handler(event, context):
  
  logger.info('Received event: %s', json.dumps(event, indent=2))
  
   # There should only ever be one record, but just incase, we loop through. 
  for record in event['Records']:
    # Use this to indicate when the process began. only used for maintanability. 
    # We don't actually use it anywhere in the code. 
    # processing_began_at = datetime.now().isoformat()
    
      # if the record isn't in the even then return. This should never be the case. 
    if 'Records' not in event:
      logger.info('No records in event')
      return
    else:
      logger.info('Received {} of records'.format(len(event['Records'])))
      
    
    # Pull the bucket and key from the record input  
    s3_bucket = record['s3']['bucket']['name']
    s3_key = record['s3']['object']['key']

    logger.info('Reading content from adhoc file...')
    adhoc_file_obj = s3.Object(s3_bucket, s3_key)
    folders_to_upload = ''
    for line in adhoc_file_obj.get()['Body'].read().splitlines():
      decoded_line = line.decode('utf-8')
      logger.debug('line content: ' + decoded_line)
      folders_to_upload += decoded_line + '|'
    
    folders_to_upload = folders_to_upload.strip('|')
    logger.debug('folders_to_upload is: ' + folders_to_upload)
    
    
    # See https://docs.aws.amazon.com/datasync/latest/userguide/filtering.html#include-filters
    # include_filter = f"{folder1}|{folder2}"
    include_filter = [
      {
        'FilterType': 'SIMPLE_PATTERN',
        'Value': folders_to_upload
      }
    ]
    
    try:
      rv = ds.start_task_execution(
          TaskArn=ds_task_arn,
          Includes=include_filter
      )
      logger.info(f"Started DataSync task: {ds_task_arn}")
      
    except:
      logger.error(f"An error ocurred while trying to start DataSync task {ds_task_arn}")
      print(sys.exc_info()[0])
      traceback.print_exc()
      return {
        'statusCode': 500,
        'body': json.dumps('Failure')
      }
      
  return {
    'statusCode': 200,
    'body': 'Made it here!'
  }
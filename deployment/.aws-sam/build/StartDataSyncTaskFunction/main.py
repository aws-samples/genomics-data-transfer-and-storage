# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import json
import boto3
import os
import datetime
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

SEQUENCER_OUTPUT_PATHS = os.environ['SEQUENCER_OUTPUT_PATHS'].split(',')

# Number of days to consider to for data transfers
TRANSFER_DAYS = 3

ds = boto3.client('datasync')
ds_task_arn = os.environ['DATA_SYNC_TASK_ARN']
 
def lambda_handler(event, context):

    # Grab Data Sync Task ARN
    logger.info(f"Data Sync Task ARN is {ds_task_arn}")

    # Build the include filter to pass to the DataSync start_task_execution function
    # See https://docs.aws.amazon.com/datasync/latest/userguide/filtering.html#include-filters
    include_filters = []
    for path in SEQUENCER_OUTPUT_PATHS:
        for day in range(TRANSFER_DAYS):
            # Build a date/time string.
            curr_date = datetime.datetime.now() - datetime.timedelta(days=day)
            
            # Pick date format based on sequencer type.
            # iseq "%Y%m%d" - i.e. 20211115, all others "%y%m%d" - i.e 211115
            date_format = "%y%m%d"
            if "/iseq" in path:
                date_format = "%Y%m%d"
            
            date_prefix = curr_date.strftime(date_format)
            
            # Build the include filter to pass to the DataSync start_task_execution function
            curr_filter = "{}/{}*".format(path, date_prefix)
            # Append filter to list
            include_filters.append(curr_filter)

    
    #Add adhoc folder to filter list
    include_filters.append('/adhoc')
    #Convert filter list to string format required by the DataSync API
    include_string = "|".join(include_filters)
    logger.debug(f"include_string: {include_string}")
  
    try:
        rv = ds.start_task_execution(
            TaskArn=ds_task_arn,
            OverrideOptions={
                'VerifyMode': 'ONLY_FILES_TRANSFERRED',
                'TransferMode': 'CHANGED',
                'Atime': 'BEST_EFFORT',
                'LogLevel': 'TRANSFER',
                'Mtime': 'PRESERVE',
            },
            Includes=[{
                'FilterType': 'SIMPLE_PATTERN',
                'Value': include_string
            }]
        )
        logger.info(f"Started DataSync task: {ds_task_arn}")
    except:
        logger.error(f"An error ocurred while trying to start DataSync task {ds_task_arn}")
        print(sys.exc_info()[0])
        sys.exc_info()[3].print_stack()
        return {
            'statusCode': 500,
            'body': json.dumps('Failure')
        }


    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
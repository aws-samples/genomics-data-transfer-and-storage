import os
# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

from datetime import datetime
import uuid
import logging
import boto3
import random

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

BUCKET = os.getenv('MOCK_SEQ_DATA_BUCKET')
SEQUENCER_OUTPUT_PATHS = os.environ['SEQUENCER_OUTPUT_PATHS'].split(',')

NUM_FILES_TO_OUTPUT = 10

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
data_bucket = s3_resource.Bucket(BUCKET)

def lambda_handler(event, context):
  
  select_random_output_path = random.choice(SEQUENCER_OUTPUT_PATHS)
  
  try:
    logger.info('Creating file path...')
    
    # Pick date format based on sequencer type.
    # iseq "%Y%m%d" - i.e. 20211115, all others "%y%m%d" - i.e 211115
    curr_date = datetime.now()  
    date_format = "%y%m%d"
    if "/iseq" in select_random_output_path:
        date_format = "%Y%m%d"
    date_prefix = curr_date.strftime(date_format)

    run_id = str(uuid.uuid4())
    filepath = '/mnt/efs{}/{}/{}/'.format(select_random_output_path, date_prefix, run_id)
    os.makedirs(filepath, exist_ok=True)
  except Exception:
      logger.error("Error while accessing EFS", exc_info=True)
      return {
        "status": 500,
        "comment": "Error while accessing EFS"
      }
  
  try:
    logger.info('Loading files...')
    i = 1
    for object_summary in data_bucket.objects.all():
      if i > NUM_FILES_TO_OUTPUT:
        break
      logger.info('loading object %s into location %s', object_summary.key, filepath)
      converted_key = object_summary.key.replace('/','_')
      s3_client.download_file(BUCKET,  object_summary.key, filepath + converted_key)
      i+=1
  except Exception:
      logger.error("Error while writing files to EFS", exc_info=True)
      return {
        "status": 500,
        "comment": "Error while writing files to EFS"
      }
  
  return {
    "status": 200,
    "comment": "Successfully uploaded sequencer output"
  }

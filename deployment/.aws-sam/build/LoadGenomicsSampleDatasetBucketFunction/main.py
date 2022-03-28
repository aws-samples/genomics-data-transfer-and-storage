# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

from __future__ import print_function
import sys,os
import logging
import urllib3
import boto3
from botocore import UNSIGNED
from botocore.config import Config
#Custom Resource helper (https://github.com/aws-cloudformation/custom-resource-helper)
from crhelper import CfnResource

srcBucketRegion = os.environ['SRC_BUCKET_REGION']
srcBucketName = os.environ['SRC_BUCKET_NAME']
srcBucketPrefix = os.environ['SRC_BUCKET_PREFIX']
destBucketName = os.environ['DEST_BUCKET_NAME']

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

helper = CfnResource(json_logging=False, log_level=os.getenv('LOG_LEVEL', 'INFO').upper())
http = urllib3.PoolManager()
srcS3 = boto3.resource('s3', region_name=srcBucketRegion, config=Config(signature_version=UNSIGNED))
destS3 = boto3.resource('s3')

transferLimitInGB = 2
fileSizeLimitInMB = 20

@helper.create
@helper.update
def load_data_from_open_registry(event, context):
    try:
        logger.info("Create/Update event from CloudFormation.")
        srcBucket = srcS3.Bucket(srcBucketName)
        destBucket = destS3.Bucket(destBucketName)

        num_files = 0
        total_bytes_transferred = 0
        for file in srcBucket.objects.filter(Prefix=srcBucketPrefix):
            #logger.debug(f"File {file.key}, size {file.size}")
            #If file is less than fileSizeLimitInMB (to avoid coying very large files from source dataset)
            if file.size <= (fileSizeLimitInMB*1024*1024):
                #If bytes transferred are > transferLimitInGB, stop the transfer
                if total_bytes_transferred >= (transferLimitInGB*1024*1024*1024):
                    logger.info(f"Transferred {transferLimitInGB} GB of data, stopping copy operations...")
                    break

                #Copying files from source
                logger.debug(f"Copying file {file.key}, of size {((file.size/1024)/1024)} MB to target bucket...")
                copy_source = {
                    'Bucket': srcBucketName,
                    'Key': file.key
                }
                destBucket.copy(copy_source, 'upto'+str(fileSizeLimitInMB)+'MB/'+file.key)
                num_files += 1
                total_bytes_transferred += file.size
                logger.debug(f"Files Transferred: {num_files}. Bytes Transferred: {((total_bytes_transferred/1024)/1024)} MB.")

        helper.Data['DataLoaded'] = "Yes"
        helper.Data['TotalBytesTransferred'] = total_bytes_transferred
        helper.Data['TotalNumberOfFiles'] = num_files
        logger.info(f"Total Files Transferred: {num_files}. Total Bytes Transferred: {((total_bytes_transferred/1024)/1024)} MB.")
        return "DataLoaded"
        
    except Exception:
        logger.error(f"An error ocurred while trying to copy the file with key {file.key}, from bucket {file.bucket_name}", exc_info=True)
        helper.Data['DataLoaded'] = "No"
        helper.Data['ErroDetails'] = sys.exc_info()[0]
        return "DataNotLoaded"

@helper.delete
def delete(event, context):
    logger.info("Delete event from CloudFormation.")
    helper.Data["DataLoaded"] = "None"
    pass

def lambda_handler(event, context):
    helper(event, context)
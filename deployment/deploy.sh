#!/bin/bash -e

# Copyright 2022 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

ARTIFACT_BUCKET=$1
STACK_NAME=$2


echo '
###############################
# Building and deploying Stack
###############################
'

sam build -t cloudformation.yml

sam package \
    --output-template-file packaged.yml \
    --s3-bucket ${ARTIFACT_BUCKET}

aws cloudformation deploy --template-file packaged.yml \
    --stack-name ${STACK_NAME} \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

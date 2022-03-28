# Warning to supress/ignore from cfn_nag scans
| Warning                                                                                                                                                                                                                                                                  | Supress Justification                                                                                                                                                                                                                                                                                                                                                                    |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Resources: ["LoadGenomicsSampleDatasetBucketFunction", "SequencerSimulatorFunction", "GetDataSyncAgentActivationKeyFunction", "StartDataSyncTaskFunction", "S3NotificationLambdaFunction", "AdhocDataSyncTaskFunction"] Lambda functions should be deployed inside a VPC | The only lambda functions that need to be inside a VPC are SequencerSimulatorFunction and GetDataSyncAgentActivationKeyFunction. Both of them are already part of the OnPremisesSimulatorVPC.  Verify in the CloudFormation Template.                                                                                                                                                    |
| Resource: ["OnPremisesSimulatorFlowLogGroup", "EFSToS3DataSyncLogGroup"] CloudWatchLogs LogGroup should specify a KMS Key Id to encrypt the log data                                                                                                                     | All log groups are encrypted by default. CloudWatch Logs service manages the server-side encryption keys. If any customer wants to manage their own keys, they are welcome to do so.                                                                                                                                                                                                     |
| Resource: ["LoggingBucket", "GenomicsSampleDatasetBucket", "DestinationBucket"] S3 bucket should likely have a bucket policy                                                                                                                                             | Access control to these buckets is managed using the Canned ACLs specified in the value of the property AccessControl of each bucket. LogDeliveryWrite or BucketOwnerFullControl depending on the bucket. [More info here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl).                                                                          |
| Resource: ["LoggingBucket"] S3 Bucket should have access logging configured                                                                                                                                                                                              | Logging configuration on all the other buckets is already set, all of them are configured to put access logs push in this bucket. The LoggingBucket itself should not have access logging configured.                                                                                                                                                                                    |
| Resources: ["SequencerSimulatorFunctionIAMRole", "GetDataSyncAgentActivationKeyFunctionIAMRole"] IAM role should not allow * resource on its permissions policy                                                                                                          | The actions defined by the policy 'ENIAccessDescribePermissions' require a wildcard resource. Actions: DescribeNetworkInterfaces, DescribeNetworkInterfacePermissions, DescribeDhcpOptions, DescribeSubnets, DescribeVpcs, DescribeInstances. [More info here](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonec2.html#amazonec2-actions-as-permissions). |
| Resources: ["DataSyncOnPremisesSimulatorAgentInstanceSecurityGroup", "SequencerSimulatorFunctionSecurityGroup", "GetDataSyncAgentActivationKeyFunctionSecurityGroup"] Security Groups found with cidr open to world on egress                                            | Egress access is required for these functions to work properly.  Ingress access to all of them is restricted.                                                                                                                                                                                                                                                                            |
| Resource: ["DataSyncOnPremisesSimulatorAgentInstanceSecurityGroup"] Security Groups found egress with port range instead of just a single port                                                                                                                           | Egress access to a range of ports is required for this function to work properly.  Ingress access to all of it is restricted. Moreover, the port 80 of the instance is automatically closed by AWS DataSync once the agent is activate. [More info here](https://docs.aws.amazon.com/datasync/latest/userguide/activating-agent.html) .                                                 |
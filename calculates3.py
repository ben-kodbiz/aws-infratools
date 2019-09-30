#To calculate all bucket size in account
#Best use with aws-vault

import boto3
import datetime

now = datetime.datetime.now()

cw = boto3.client('cloudwatch')
s3client = boto3.client('s3')

# Get a list of all buckets
allbuckets = s3client.list_buckets()

# Header Line for the output going to standard out
print('Bucket'.ljust(45) + 'Size in Bytes'.rjust(25))

# Iterate through each bucket
for bucket in allbuckets['Buckets']:
    # For each bucket item, look up the cooresponding metrics from CloudWatch
    response = cw.get_metric_statistics(Namespace='AWS/S3',
                                        MetricName='BucketSizeBytes',
                                        Dimensions=[
                                            {'Name': 'BucketName', 'Value': bucket['Name']},
                                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                                        ],
                                        Statistics=['Average'],
                                        Period=3600,
                                        StartTime=(now-datetime.timedelta(days=1)).isoformat(),
                                        EndTime=now.isoformat()
                                        )
    # The cloudwatch metrics will have the single datapoint, so we just report on it. 
    for item in response["Datapoints"]:
        print(bucket["Name"].ljust(45) + str("{:,}".format(int(item["Average"]))).rjust(25))

#run state
#tag “AutoOff” tag “AutoOff” set to “False”
#
import boto3
import logging
 
#setup simple logging for INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)
 
#define the connection
ec2 = boto3.resource('ec2')
# open connection to ec2
#conn = get_ec2_conn()
 
# get a list of all instances
# all_instances = [i for i in ec2.instances.all()]
# get list of all running instances
 
all_instances = [i for i in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])]
def lambda_handler(event, context):
 
    #instances = ec2.instances.filter(Filters=filters)
    # get instances with filter of running + with tag `Name`
    instances = [i for i in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}, {'Name':'tag:AutoOff', 'Values':['False']}])]
 
    # make a list of filtered instances IDs `[i.id for i in instances]`
    # Filter from all instances the instance that are not in the filtered list
    instances_to_stop = [to_stop for to_stop in all_instances if to_stop.id not in [i.id for i in instances]]
 
    # run over your `instances_to_stop` list and stop each one of them
    for instance in instances_to_stop:
        instance.stop()

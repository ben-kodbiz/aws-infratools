import boto3
import collections
import datetime
import time
import sys 
ses = boto3.client('ses')
AWSAccountID=boto3.client('sts').get_caller_identity()['Account']
AWSUser=boto3.client('sts').get_caller_identity()['UserId']
ec = boto3.client('ec2', 'eu-west-1')
ec2 = boto3.resource('ec2', 'eu-west-1')
from datetime import datetime
from dateutil.relativedelta import relativedelta

#create date variables 

date_after_month = datetime.now()+ relativedelta(days=7)
#date_after_month.strftime('%d/%m/%Y')
today=datetime.now().strftime('%d/%m/%Y')

def send_mail(email_from, email_to, subject, body):
    smtp_address = 'smtp.office365.com'
    provider_username = 'sender@company.com'
    provider_password = 'Pass'
    smtpserver = smtplib.SMTP(smtp_address, 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo() # extra characters to permit edit
    smtpserver.login(provider_username, provider_password)
    header = 'To: ' + email_to + '\n' + 'From: ' + email_from + '\n' + 'Subject: ' + subject + '\n'
    msg = header + '\n ' + body + ' \n\n'
    smtpserver.sendmail(provider_username, email_to, msg)
    smtpserver.quit()
def lambda_handler(event, context):
  #Get instances with Owner Taggs and values Unknown/known
    instance_ids = []
    reservations = ec.describe_instances().get('Reservations', []) 

    for reservation in reservations:
     for instance in reservation['Instances']:
        tags = {}
        for tag in instance['Tags']:
            tags[tag['Key']] = tag['Value']
            if tag['Key'] == 'Name':
              name=tag['Value']
        if not 'Owner' in tags or tags['Owner']=='unknown' or tags['Owner']=='Unknown':
              instance_ids.append(instance['InstanceId'])  

                #Check if "TerminateOn" tag exists:

              if 'TerminateOn' in tags:
                  #compare TerminteOn value with current date
                    if tags["TerminateOn"]==today:

                    #Check if termination protection is enabled
                     terminate_protection=ec.describe_instance_attribute(InstanceId =instance['InstanceId'] ,Attribute = 'disableApiTermination')
                     protection_value=(terminate_protection['DisableApiTermination']['Value'])
                     #if enabled disable it
                     if protection_value == True:
                        ec.modify_instance_attribute(InstanceId=instance['InstanceId'],Attribute="disableApiTermination",Value= "False" )
                    #terminate instance
                     ec.terminate_instances(InstanceIds=instance_ids)
                     body="AWS Account:" + AWSUser + "\n\nAWS Account Number:" + AWSAccountID + "\n\nInstance Name:" + name + "\n\nInstance ID:" + instance['InstanceId'] + "\n\nTo be Removed In:Now\n\n\n\rNote:\n\nOwner tag is missing from this instance, hence,instance is removed." 
                     send email that instance is terminated
                     send_mail('sender@example.com', 'johndoe@doe.com', 'US:Notification of terminating instances', body)

                    else:
                      

                      now=datetime.now()
                      future=tags["TerminateOn"]
                      TerminateOn = datetime.strptime(future, "%d/%m/%Y")
                      days= (TerminateOn-now).days
                      body="AWS Account:" + AWSUser + "\n\nAWS Account Number:" + AWSAccountID + "\n\nInstance Name:" + name + "\n\nInstance ID:" + instance['InstanceId'] + "\n\nTo be Removed In:" + str(days) + "days\n\n\n\rNote:\n\nOwner tag is missing from this instance, hence,instance is removed."
                      send_mail('sender@example.com', 'johndoe@doe.com', 'US:Notification of terminating instances', body)
                      ec.stop_instances(InstanceIds=instance_ids)

              else:
                 if not 'TerminateOn' in tags:#, create it
                  ec2.create_tags(Resources=instance_ids,Tags=[{'Key':'TerminateOn','Value':date_after_month.strftime('%d/%m/%Y')}])
                  ec.stop_instances(InstanceIds=instance_ids)
                  body="AWS Account:" + AWSUser + "\n\nAWS Account Number:" + AWSAccountID + "\n\nInstance Name:" + name + "\n\nInstance ID:" + instance['InstanceId'] + "\n\nTo be Removed In:Six Days from now\n\n\n\rNote:\n\nOwner tag is missing from this instance.\nIf you do not wish this instance to be removed, please update the Owner tag." 
                  send_mail('sender@example.com', 'johndoe@doe.com', 'US:Notification of shutting down instances', body)
                  

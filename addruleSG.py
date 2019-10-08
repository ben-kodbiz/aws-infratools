#!/usr/bin/python3
import boto3
import csv
security_group_id = "sg-000000000"
port_range_start = 514
port_range_end = 514
protocol = "udp"
csv_file = "/FULL/PATH/TO/FILE.csv"
ec2 = boto3.resource('ec2')
security_group = ec2.SecurityGroup(security_group_id)
f = open(csv_file)
csv_f = csv.reader(f)
#security_group.revoke_ingress(IpPermissions=security_group.ip_permissions) #use this to remove all rules from the group
for row in csv_f:
    cidr = row[0] + "/32"
    description = row[1]
    security_group.authorize_ingress(
        DryRun=False,
        IpPermissions=[
            {
                'FromPort': port_range_start,
                'ToPort': port_range_end,
                'IpProtocol': protocol,
                'IpRanges': [
                    {
                        'CidrIp': cidr,
                        'Description': description
                    },
                ]
            }
        ]
    )

#! /usr/bin/python
################################################################################
##  - Creates a CSV report for EBS volumes, including some snapshot information
################################################################################
import csv
import os, sys
import datetime
import argparse
from boto import ec2
from boto.exception import EC2ResponseError

# Defaults, can be modified
AWS_ACCESS_KEY = None
AWS_SECRET_KEY = None
AWS_REGIONS = u'us-east-1|us-west-1|us-west-2|eu-west-1|ap-southeast-1|ap-northeast-1|ap-southeast-2|sa-east-1'

def open_file (filepath):
    """
    Opens the output files, promts whether to overwrite
    """
    goaheadandopen = True
    if os.path.exists (filepath):
        if os.path.isfile (filepath):
            valid = {'yes':True, 'y':True,
                     'no':False, 'n':False}
                     
            while True:
                sys.stdout.write ('file %s exists, overwrite it? [y/n] ' % filepath)
                choice = raw_input().lower()
                if choice in valid.keys ():
                    if not valid[choice]:
                        goaheadandopen = False
                    break
                sys.stdout.write ('Please respond with \'yes\' or \'no\' (or \'y\' or \'n\').\n')
        else: # folder
            sys.stdout.write ('%s exists but nt a regular file. Aborting...\n')
            goaheadandopen = False
            
    if not goaheadandopen:
        return None
        
    try:
        f = file(filepath, 'wt')
    except Exception, e:
        f = None
        sys.stderr.write ('Could not open file %s. reason: %s\n' % (filepath, e))
        
    return f
        
def ec2_connect (access_key, secret_key, region):
    """
    Connects to EC2, returns a connection object
    """
    
    try:
        conn = ec2.connect_to_region (region, 
                                      aws_access_key_id=access_key, 
                                      aws_secret_access_key=secret_key)
    except Exception, e:
        sys.stderr.write ('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn = None
        
    return conn
        
def create_ebs_report (regions, access_key, secret_key, filepath):
    """
    Creates the actual report, first into a python data structure
    Then write into a csv file
    """
    # opens file
    f = open_file (filepath)
    if not f:
        return False

    region_list = regions.split('|')
    
    volume_dict = {}
    # go over all regions in list
    for region in region_list:
    
        # connects to ec2
        conn = ec2_connect (access_key, secret_key, region)
        if not conn:
            sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
            continue
        
        # get all volumes and snapshots
        try:
            volumes = conn.get_all_volumes ()
            snapshots = conn.get_all_snapshots (owner='self')
        except EC2ResponseError, e:
            sys.stderr.write ('Could not get volumes or snapshots for region: %s. Skipping (problem: %s)\n' % (region, e.error_message))
            continue
        
        volume_types_map = { u'standard' : u'Standard/Magnetic', u'io1' : u'Provisioned IOPS (SSD)', u'gp2' : u'General Purpose SSD'}
        volume_dict [region] = {}
        # goes over volumes and insert relevant data into a python dictionary
        for vol in volumes:
            try:
                name = vol.tags['Name']
            except:
                name = u''
            try:
                iops = vol.iops
            except:
                iops = 0
            if vol.attachment_state() == u'attached':
                instance_id = vol.attach_data.instance_id
                device = vol.attach_data.device
            else:
                instance_id = u'N/A'
                device = 'N/A'
            if iops == None : iops = 0
            
            if vol.encrypted:
                encrypted = u'yes'
            else:
                encrypted = u'no'
 
            volume_dict [region][vol.id] = { 'name' : name, 
                                             'size' : vol.size,
                                             'zone' : vol.zone,
                                             'type' : volume_types_map[vol.type],
                                             'iops' : iops,
                                             'orig_snap' : vol.snapshot_id,
                                             'encrypted' : encrypted,
                                             'instance' : instance_id,
                                             'device' : device,
                                             'num_snapshots' : 0,
                                             'first_snap_time' : u'',
                                             'first_snap_id' : u'N/A',
                                             'last_snap_time' : u'',
                                             'last_snap_id' : u'N/A'
                                            }
                                            

        #go over snapshots and match to volumes structure
        for snap in snapshots:
            start_time = datetime.datetime.strptime (snap.start_time.split('.')[0],'%Y-%m-%dT%H:%M:%S')
            if volume_dict[region].has_key (snap.volume_id):
                vol=volume_dict[region][snap.volume_id]
                vol['num_snapshots']+=1
                if vol['first_snap_time'] == u'' or start_time < vol['first_snap_time']:
                    vol['first_snap_time'] = start_time
                    vol['first_snap_id'] = snap.id
                if vol['last_snap_time'] == u'' or start_time > vol['last_snap_time']:
                    vol['last_snap_time'] = start_time
                    vol['last_snap_id'] = snap.id
            else:
                sys.stdout.write ('Region %s: Could not find volume %s for snapshot %s. Volume was deleted or snapshot copied from another region \n' % \
                                   (region, snap.volume_id, snap.id))
                
                                                    

    # starts the csv file
    writer = csv.writer (f)
    # header
    writer.writerow (['Region','volume ID','Volume Name','Volume Type','iops','Size (GiB)', \
                      'Created from Snapshot','Attached to','Device','Encrypted','Number of Snapshots', \
                      'Earliest Snapshot Time','Earliest Snapshot','Most Recent Snapshot Time','Most Recent Snapshot'])
         
    # writes actual data
    for region in volume_dict.keys ():
        for volume_id in volume_dict[region].keys ():
            volume = volume_dict[region][volume_id]
            writer.writerow ([region, volume_id, volume['name'],volume['type'],volume['iops'],volume['size'], \
                              volume['orig_snap'],volume['instance'],volume['device'],volume['encrypted'], \
                              volume['num_snapshots'],volume['first_snap_time'],volume['first_snap_id'], \
                              volume['last_snap_time'],volume['last_snap_id']])
                              
                              
    f.close ()
    return True
    
if __name__ == '__main__':

    # Define command line argument parser
    parser = argparse.ArgumentParser(description='Creates a CSV report about EBS volumes and tracks snapshots on them.')
    parser.add_argument('--regions', default = AWS_REGIONS, help='AWS regions to create the report on, can add multiple with | as separator. Default will assume all regions')
    parser.add_argument('--access_key', default = AWS_ACCESS_KEY, help='AWS API access key.  If missing default is used')
    parser.add_argument('--secret_key', default = AWS_SECRET_KEY, help='AWS API secret key.  If missing default is used')
    parser.add_argument('--file', required=True, help='Path for output CSV file')
    
    args = parser.parse_args ()

    # creates the report
    retval = create_ebs_report (args.regions, args.access_key, args.secret_key, args.file)
    if retval:
        sys.exit (0)
    else:
        sys.exit (1)
        
        

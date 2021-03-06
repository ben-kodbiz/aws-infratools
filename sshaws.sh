#!/usr/bin/env bash
#For accessing ec2 ssh based instances by modifying security group ingress  based
#on your dynamic ip.Its better than using those dreaded 0.0.0.0/0
#Things that you need
# 1)working bash shell or wsl
# 2)configured aws creds
#And you good, Please use your sg-id(example: sg-01da4fd4299ec7aaabbcc)
#for example ./sshaws sg-01da4fd4299ec7aaabbcc 22


# Usage: ./sshaws <Security Group Id> <Port>

# Standardised error process. Errors to STDERR.
function error_and_die() {
  echo -e "[ERROR] ${1}" >&2;
  exit 1;
}


declare access_granted="false";
declare allowed_cidrs;
declare group_id="${1}"; 
declare port="${2:-22}"
declare my_cidr;
declare my_ip;

# Get my public IP...
my_ip="$(curl -s curlmyip.org || echo "Failed")";

# ... or this is all pointless.
[ "${my_ip}" == "Failed" ] \
  && error_and_die "Failed to retrieve my IP from v4.ifconfig.co";


allowed_cidrs="$(aws ec2 describe-security-groups \
                   --output text \
                   --query '
                     SecurityGroups[?
                       GroupId==`'${group_id}'`
                     ].
                     [
                       IpPermissions[?
                         ToPort==`'${port}'` && FromPort==`'${port}'` && IpProtocol==`tcp`
                       ].
                       IpRanges[*].
                       CidrIp
                     ]' \
                   || echo "Failed")";


[ "${allowed_cidrs}" == "Failed" ] \
  && error_and_die "Failed to retrieve SSH ingress rules for ${group_id}";


my_cidr="${my_ip}/32";

for cidr in ${allowed_cidrs}; do 
  if [ "${cidr}" == "${my_cidr}" ]; then
    access_granted="true";
  else
    echo -en "Revoking SSH access to ${group_id} from ${cidr}... ";
    aws ec2 revoke-security-group-ingress \
      --group-id ${group_id} \
      --protocol tcp \
      --port ${port} \
      --cidr ${cidr} \
      && echo -e "Done." \
      || echo -e "Failed."; # Non-fatal. Don't die.
  fi;
done;

if [ "${access_granted}" == "true" ]; then
  # If we found our IP in the list, we don't need to re-authorise it.
  echo -e "Access already authorised from ${my_cidr}";
else
  
  echo -en "Authorising SSH access to ${group_id} from ${my_cidr}... ";
  aws ec2 authorize-security-group-ingress \
    --group-id ${group_id} \
    --protocol tcp \
    --port ${port} \
    --cidr ${my_cidr} \
    && echo -e "Done." \
    || error_and_die "Failed."; # Fatal.
fi;

# We're all done, no fatal errors.
exit 0;

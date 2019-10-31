#!/bin/bash
 
aws support describe-trusted-advisor-checks --region us-east-1 --language en | jq -c ".checks[] | [ .category , .name , .id ]" | sort > checks.txt
 
while read line
do
  echo -n `echo "$line" | awk -F'"' '{print $2}' `
  echo -n " "
  echo -n `echo "$line" | awk -F'"' '{print $4}' `
  echo -n " ------ "
  aws support describe-trusted-advisor-check-result --region us-east-1 --language en --check-id `echo "$line" | awk -F'"' '{print $6}' ` | jq -r ".result.status" 
 
done <resultcheck.txt

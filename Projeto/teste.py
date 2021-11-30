import boto3
import os
from botocore.exceptions import ClientError
import time
import requests


client_LB = boto3.client('elbv2', region_name="us-east-1")


LB_existe = client_LB.describe_load_balancers(
    Names=[
        'LBProjeto'
    ]
)

DNS=LB_existe["LoadBalancers"][0]["DNSName"]

print(DNS)

res = requests.get("http://"+DNS+"/admin/")

print(res)
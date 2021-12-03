import boto3
import os
from botocore.exceptions import ClientError
import time







# USERDATA_SCRIPT_POSTGRES = '''#!/bin/bash
# sudo apt update
# sudo apt install postgresql postgresql-contrib -y 
# sudo -u postgres psql -c "create user cloud with encrypted password 'cloud';"
# sudo -u postgres psql -c 'create database tasks with owner cloud;'
# sudo echo "listen_addresses = '*'" >> /etc/postgresql/12/main/postgresql.conf
# sudo echo "host all all 192.168.0.0/20 trust" >> /etc/postgresql/12/main/pg_hba.conf
# sed -i '1i\host  all  all 0.0.0.0/0 md5'  /etc/postgresql/12/main/pg_hba.conf
# sudo ufw allow 5432/tcp
# sudo systemctl restart postgresql'''


# ec2_ohio = boto3.resource('ec2', region_name="us-east-2")

# client_Ohio = boto3.client('ec2', region_name="us-east-2")

# existe_Postgres = client_Ohio.describe_instances(
#     Filters=[
#         {
#             'Name': 'key-name',
#             'Values': [
#                 'KP_Ohio',
#             ],
#         },
#     ],
# )


# for reservation in (existe_Postgres["Reservations"]):
#         for instance in reservation["Instances"]:
#             try:
#                 terminate_instance(instance["InstanceId"], "us-east-2")
#             except:
#                 pass

# time.sleep(60)

# #Apagando par de chaves

# try:
#     client_Ohio.delete_key_pair(
#         KeyName='KP_Ohio'
#     )
# except:
#     pass

# # Gerando par de chaves 
# KP_Ohio = client_Ohio.create_key_pair(KeyName = 'KP_Ohio')
# file = open("KP_Ohio.pem", 'w')
# file.write(KP_Ohio['KeyMaterial'])
# file.close

# # Apagando o Securuty Group

# client_Ohio.delete_security_group(
#     GroupName='SG_Ohio',
# )


# # Criando Security Group
# SG_Ohio = client_Ohio.create_security_group(
#     GroupName = 'SG_Ohio',
#     Description = 'SG_Ohio sg'  
# )

# # ID do grupo de segurança de Ohio
# Gid_Ohio = SG_Ohio['GroupId']

# # Passando as portas
# client_Ohio.authorize_security_group_ingress(
#     GroupId = Gid_Ohio,
#     IpPermissions = [
#         {
#             "FromPort": 22,
#             "IpProtocol": "tcp",
#             'IpRanges': [
#                 {
#                     'CidrIp': '0.0.0.0/0'
#                 },
#             ],
#             "ToPort": 22
#         },
#         {
#             "FromPort": 5432,
#             "IpProtocol": "tcp",
#             'IpRanges': [
#                 {
#                     'CidrIp': '0.0.0.0/0'
#                 },
#             ],
#             "ToPort": 5432
#         },
#     ]
# )





# instance_ohio = ec2_ohio.create_instances(
#     ImageId="ami-0629230e074c580f2",
#     MinCount=1,
#     MaxCount=1,
#     InstanceType="t2.micro",
#     UserData=USERDATA_SCRIPT_POSTGRES,
#     KeyName="KP_Ohio",
#     SecurityGroups = ['SG_Ohio'],
#     TagSpecifications=[
#     {
#         'ResourceType': 'instance',
#         'Tags': [
#             {
#                 'Key': 'Name',
#                 'Value': 'Postgres'
#             },
#         ]
#     },
# ]

# )

# id_instance_ohio = instance_ohio[0].id
# print(id_instance_ohio)
# ip_pub_postgres=get_public_ip(id_instance_ohio, "us-east-2")
# print(ip_pub_postgres)

# USERDATA_SCRIPT_ORM = '''#!/bin/bash
# sudo apt update
# cd /home/ubuntu
# sudo git clone https://github.com/LaisNSilva/tasks.git
# sudo sed -i s/"node1"/"''' + str(ip_pub_postgres) + '''"/g  tasks/portfolio/settings.py
# cd tasks
# sudo ./install.sh
# sudo ufw allow 8080/tcp
# sudo reboot
# '''


# ec2_North_Virginia = boto3.resource('ec2', region_name="us-east-1")
# client_North_Virginia = boto3.client('ec2', region_name="us-east-1")

# try:
#     client_North_Virginia.delete_key_pair(
#         KeyName='KP_North_Virginia'
#     )
# except:
#     pass

# # Gerando par de chaves 
# KP_North_Virginia = client_North_Virginia.create_key_pair(KeyName = 'KP_North_Virginia')
# file = open("KP_North_Virginia.pem", 'w')
# file.write(KP_North_Virginia['KeyMaterial'])
# file.close

# # Apagando o Securuty Group
# try:
#     client_North_Virginia.delete_security_group(
#         GroupName='SG_North_Virginia'
#     )
# except:
#     pass


# # Criando Security Group
# SG_North_Virginia = client_North_Virginia.create_security_group(
#     GroupName = 'SG_North_Virginia',
#     Description = 'SG_North_Virginia sg'  
# )

# # ID do grupo de segurança de Ohio
# Gid_North_Virginia = SG_North_Virginia['GroupId']

# # Passando as portas
# client_North_Virginia.authorize_security_group_ingress(
#     GroupId = Gid_North_Virginia,
#     IpPermissions = [
#         {
#             "FromPort": 22,
#             "IpProtocol": "tcp",
#             'IpRanges': [
#                 {
#                     'CidrIp': '0.0.0.0/0'
#                 },
#             ],
#             "ToPort": 22
#         },
#         {
#             "FromPort": 8080,
#             "IpProtocol": "tcp",
#             'IpRanges': [
#                 {
#                     'CidrIp': '0.0.0.0/0'
#                 },
#             ],
#             "ToPort": 8080
#         },
#     ]
# )

# instance_North_Virginia = ec2_North_Virginia.create_instances(
#     ImageId="ami-083654bd07b5da81d",
#     MinCount=1,
#     MaxCount=1,
#     InstanceType="t2.micro",
#     KeyName="KP_North_Virginia",
#     SecurityGroups = ['SG_North_Virginia'],
#     UserData=USERDATA_SCRIPT_ORM,
#     TagSpecifications=[
#     {
#         'ResourceType': 'instance',
#         'Tags': [
#             {
#                 'Key': 'Name',
#                 'Value': 'ORM'
#             },
#         ]
#     },
# ]
# )

# id_instance_North_Virginia = instance_North_Virginia[0].id
# print("instancia 2: {0}".format(id_instance_North_Virginia))

# ip=get_public_ip(id_instance_North_Virginia, "us-east-1")
# print(ip)

# instance_North_Virginia = ec2_North_Virginia.Instance(id=id_instance_North_Virginia)
# instance_North_Virginia.wait_until_running()

# print('Sleep starting... ({0})'.format(150))
# time.sleep(150)
# print('Sleep ended')
# instance_North_Virginia.reload()

client_LB = boto3.client('elbv2', region_name="us-east-1")
TargetGroup = client_LB.create_target_group(
    Name='TGTESTE2',
    Protocol='HTTP',
    Port=8080,
    VpcId='vpc-7086360a',
    TargetType='instance',
    IpAddressType='ipv4'
)
LoadBlanacer = client_LB.create_load_balancer(
    Name='LBTESTE2',
    Type='application',
    Subnets = ['subnet-14b9da3a', 'subnet-44fe557a'],
    Scheme='internet-facing',
    IpAddressType='ipv4',
)

LB = LoadBlanacer['LoadBalancers'][0]['LoadBalancerArn']
TG = TargetGroup["TargetGroups"][0]["TargetGroupArn"]
lb_name = LB[LB.find("app"):]
tg_name = TG[TG.find("targetgroup"):]

print(lb_name)
print(tg_name)




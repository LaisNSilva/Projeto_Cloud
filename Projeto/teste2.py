import boto3
import os
from botocore.exceptions import ClientError
import time



def terminate_instance(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    response = ec2_client.terminate_instances(InstanceIds=[instance_id])
    print(response)




def create_key_pair():
    ec2_client = boto3.client("ec2", region_name="us-east-2")
    key_pair = ec2_client.create_key_pair(KeyName="ec2-key-pair")

    private_key = key_pair["KeyMaterial"]

    # write private key to file with 400 permissions
    with os.fdopen(os.open("/tmp/aws_ec2_key.pem", os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
        handle.write(private_key)

# Cria par de chaves
#create_key_pair()

def get_public_ip(instance_id):
    ec2_client = boto3.client("ec2", region_name="us-east-2")
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")

    for reservation in reservations:
        for instance in reservation['Instances']:
            return(instance.get("PublicIpAddress"))




USERDATA_SCRIPT_POSTGRES = '''#!/bin/bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y 
sudo -u postgres psql -c "create user cloud with encrypted password 'cloud';"
sudo -u postgres psql -c 'create database tasks with owner cloud;'
sudo echo "listen_addresses = '*'" >> /etc/postgresql/12/main/postgresql.conf
sudo echo "host all all 192.168.0.0/20 trust" >> /etc/postgresql/12/main/pg_hba.conf
sed -i '1i\host  all  all 0.0.0.0/0 md5'  /etc/postgresql/12/main/pg_hba.conf
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql'''


ec2_ohio = boto3.resource('ec2', region_name="us-east-2")
instance_ohio = ec2_ohio.create_instances(
    ImageId="ami-0629230e074c580f2",
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    UserData=USERDATA_SCRIPT_POSTGRES,
    KeyName="Lais_Ohio",
    TagSpecifications=[
    {
        'ResourceType': 'instance',
        'Tags': [
            {
                'Key': 'Name',
                'Value': 'Postgres'
            },
        ]
    },
]

)

id_instance_ohio = instance_ohio[0].id
print(id_instance_ohio)
ip_pub_postgres=get_public_ip(id_instance_ohio)
print(ip_pub_postgres)

USERDATA_SCRIPT_ORM = '''#!/bin/bash
sudo apt update
cd /home/ubuntu
sudo git clone https://github.com/LaisNSilva/tasks.git
sudo sed -i s/"node1"/"''' + str(ip_pub_postgres) + '''"/g  tasks/portfolio/settings.py
cd tasks
sudo ./install.sh
sudo ufw allow 8080/tcp
sudo reboot
'''


ec2_North_Virginia = boto3.resource('ec2', region_name="us-east-1")
client_North_Virginia = boto3.client('ec2', region_name="us-east-1")
instance_North_Virginia = ec2_North_Virginia.create_instances(
    ImageId="ami-083654bd07b5da81d",
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="Lais",
    UserData=USERDATA_SCRIPT_ORM,
    TagSpecifications=[
    {
        'ResourceType': 'instance',
        'Tags': [
            {
                'Key': 'Name',
                'Value': 'ORM'
            },
        ]
    },
]
)

id_instance_North_Virginia = instance_North_Virginia[0].id
print("instancia 2: {0}".format(id_instance_North_Virginia))

instance_North_Virginia = ec2_North_Virginia.Instance(id=id_instance_North_Virginia)
instance_North_Virginia.wait_until_running()

print('Sleep starting... ({0})'.format(150))
time.sleep(150)
print('Sleep ended')
instance_North_Virginia.reload()


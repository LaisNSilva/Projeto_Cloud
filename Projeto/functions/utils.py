import boto3
from datetime import datetime

# Função para terminar a instância
def terminate_instance(instance_id, region):
    ec2_client = boto3.client("ec2", region_name=region)
    response = ec2_client.terminate_instances(InstanceIds=[instance_id])

# Função para pegar o IP publico das instancias
def get_public_ip(instance_id, region):
    ec2_client = boto3.client("ec2", region_name=region)
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")

    for reservation in reservations:
        for instance in reservation['Instances']:
            return(instance.get("PublicIpAddress"))

# Ler os scripts
def get_scripts(arquivo):
    script=''
    arq = open(arquivo,'r')
    for l in arq:
        script+=l
    arq.close()
    return script











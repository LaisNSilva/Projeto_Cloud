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
sudo git clone https://github.com/raulikeda/tasks.git
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

instance_North_Virginia[0].wait_until_running()

print('Sleep starting... ({0})'.format(150))
time.sleep(150)
print('Sleep ended')
instance_North_Virginia[0].reload()

id_instance_North_Virginia = instance_North_Virginia[0].id
print("instancia 2: {0}".format(id_instance_North_Virginia))


instance_North_Virginia = ec2_North_Virginia.Instance(id=id_instance_North_Virginia)
instance_North_Virginia.wait_until_running()


# Criar AMI

print("Listando as imagens")
images = ec2_North_Virginia.images.filter(Owners=['self']) 
print(images)
print("Caso tenha a image AMI_Instace_2 irá deletá-la")
for image in images:
    if image.name=="AMI_Instace_2":
        image_del = ec2_North_Virginia.Image(image.id)
        image_del.deregister()
        print(f'AMI {image.id} successfully deregistered')

print("Vai criar a imagem!")

image = instance_North_Virginia.create_image(
    InstanceId=id_instance_North_Virginia,
    Name='AMI_Instace_2',
    Description='AMI da segunda instancia',
    NoReboot=True
)


print(f'AMI creation started: {image.id}')

image.wait_until_exists(
    Filters=[
        {
            'Name': 'state',
            'Values': ['available']
        }
    ]
)

print(f'AMI {image.id} successfully created')


#Destruindo a segunda instancia
terminate_instance(id_instance_North_Virginia)

client_as = boto3.client('autoscaling', region_name="us-east-1")
try:
    ASGroup_existe = client_as.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            'ASGroup_Projeto',
        ]
    )

    if len(ASGroup_existe["AutoScalingGroups"])>0:
        client_as.delete_auto_scaling_group(
        AutoScalingGroupName='ASGroup_Projeto',
        ForceDelete=True
        )
        print("Deletou o Auto Scaling que existia")
except:
    pass   

try:
    LC_exite = client_as.describe_launch_configurations(
        LaunchConfigurationNames=[
            'LC_Projeto',
        ]
    )

    if len(LC_exite["LaunchConfigurations"])>0:
        client_as.delete_launch_configuration(
        LaunchConfigurationName='LC_Projeto'
        )
        print("Deletou o Launch Configuration que existia")
except:
    pass   

while len(ASGroup_existe["AutoScalingGroups"])>0:
    ASGroup_existe = client_as.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            'ASGroup_Projeto',
        ]
    )

LaunchConfiguration = client_as.create_launch_configuration(
    LaunchConfigurationName='LC_Projeto',
    ImageId=image.id,
    KeyName='Lais',
    SecurityGroups=[
        'default',
    ],
    InstanceType="t2.micro"
)

print("Criou o Launch Configuration")

zones_lista = client_North_Virginia.describe_availability_zones()["AvailabilityZones"]
zones=[]
for z in zones_lista:
    zones.append(z["ZoneName"])

ASGroup=client_as.create_auto_scaling_group(
    AutoScalingGroupName="ASGroup_Projeto",
    LaunchConfigurationName="LC_Projeto",
    MinSize=1,
    MaxSize=3,
    AvailabilityZones= zones 
)

print("Criou o Auto Scaling Groups")

client_LB = boto3.client('elbv2', region_name="us-east-1")

try:
    LB_existe = client_LB.describe_load_balancers(
        Names=[
            'LBProjeto'
        ]
    )
    if len(LB_existe["LoadBalancers"])>0:
        client_LB.delete_load_balancer(
            LoadBalancerArn=LB_existe["LoadBalancers"][0]["LoadBalancerArn"]
        )
        print("Deletou o Load Balancer que existia")
except:
    print("não exclui o load balancer")
    pass        

try:
    TG_existe = client_LB.describe_target_groups(
        Names=[
            'TGProjeto'
        ],
    )
    if len(TG_existe["TargetGroups"])>0:
        client_LB.delete_target_group(
            TargetGroupArn=TG_existe["TargetGroups"][0]["TargetGroupArn"]
        )
        print("Deletou o Target Group que existia")
except:
    pass


TargetGroup = client_LB.create_target_group(
    Name='TGProjeto',
    Protocol='HTTP',
    Port=8080,
    VpcId='vpc-7086360a',
    TargetType='instance',
    IpAddressType='ipv4'
)

print("Criou o Target Group")

subnets_lista=client_North_Virginia.describe_subnets()['Subnets']
subnets=[]
for s in subnets_lista:
        subnets.append(s['SubnetId'])

LoadBlanacer = client_LB.create_load_balancer(
    Name='LBProjeto',
    Type='application',
    Subnets= subnets, 
    Scheme='internet-facing',
    IpAddressType='ipv4',
)

waiter.wait(LoadBalancerArns=LoadBlanacer["LoadBalancers"][0]["LoadBalancerArn"])

print("Criou o Load Balancer")

TG = client_LB.describe_target_groups(
        Names=[
            'TGProjeto'
        ],
)

anexo_LB_TG = client_as.attach_load_balancer_target_groups(
    AutoScalingGroupName='ASGroup_Projeto',
    TargetGroupARNs=[TG["TargetGroups"][0]["TargetGroupArn"]
    ]
)



print("Vou criar o listener")

listener = client_LB.create_listener(
    LoadBalancerArn=LoadBlanacer["LoadBalancers"][0]["LoadBalancerArn"],
    Protocol='HTTP',
    Port=80,
    DefaultActions=[{'Type': 'forward', 'TargetGroupArn': TG["TargetGroups"][0]["TargetGroupArn"]}]
)

print("Criei o listener")







# Criar grupo de segurança

# response = ec2.describe_vpcs()
# vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

# try:
#     response = ec2.create_security_group(GroupName='SECURITY_GROUP_NAME',
#                                          Description='DESCRIPTION',
#                                          VpcId=vpc_id)
#     security_group_id = response['GroupId']
#     print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

#     data = ec2.authorize_security_group_ingress(
#         GroupId=security_group_id,
#         IpPermissions=[
#             {'IpProtocol': 'tcp',
#              'FromPort': 80,
#              'ToPort': 80,
#              'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
#         ])
#     print('Ingress Successfully Set %s' % data)
# except ClientError as e:
#     print(e)









                    


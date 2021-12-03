import boto3
import os
from botocore.exceptions import ClientError
import time
import logging
from functions.utils import *
import requests



# Iniando o arquivo log
try:
    # Se já existe irá apagar
    os.remove("./log.log")
except:
    #Caso ainda não exista apenas continua
    pass
# Configuração do Log
logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')



ec2_ohio = boto3.resource('ec2', region_name="us-east-2")
logging.info("Criou ec2 resource na região us-east-2 (Ohio)")

client_Ohio = boto3.client('ec2', region_name="us-east-2")
logging.info("Criou ec2 client na região us-east-2 (Ohio)")

# # ---------------------------------------------------------------------------
# # Apagar Instância Postgres
# logging.info("Verifica se há instâncias de base de dados região us-east-2 (Ohio)")
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

# logging.info("Encerrando as instâncias de base de dados região us-east-2 (Ohio)")
# for reservation in (existe_Postgres["Reservations"]):
#         for instance in reservation["Instances"]:
#             try:
#                 terminate_instance(instance["InstanceId"], "us-east-2")
#                 logging.info("Uma instância Postgres será encerrada")
#             except:
#                 logging.info("Instância Postgres não existia")
#                 pass

# logging.info("Esperando a desligamento")
# time.sleep(60)
# logging.info("Instância encerrada")


# ---------------------------------------------------------------------------
#Apagando par de chaves
logging.info("Deletando Key Pair região us-east-2 (Ohio)")
try:
    client_Ohio.delete_key_pair(
        KeyName='KP_Ohio'
    )
    logging.info("Key Pair KP_Ohio foi deletada")
except:
    logging.info("Key Pair KP_Ohio não existia")
    pass

# ---------------------------------------------------------------------------
# Gerando par de chaves 
KP_Ohio = client_Ohio.create_key_pair(KeyName = 'KP_Ohio')
file = open("KP_Ohio.pem", 'w')
file.write(KP_Ohio['KeyMaterial'])
file.close
logging.info("Key Pair KP_Ohio foi criada")

# ---------------------------------------------------------------------------
# Apagando o Securuty Group
# logging.info("Deletando Securuty Group do Postgres região us-east-2 (Ohio)")
# try:
#     client_Ohio.delete_security_group(
#         GroupName='SG_Ohio',
#     )
#     logging.info("Securuty Group SG_Ohio foi deletada")
# except:
#     logging.info("Securuty Group SG_Ohio não existia")
#     pass

# ---------------------------------------------------------------------------
# Criando Security Group
faz_SG_Ohio=True
for c in client_Ohio.describe_security_groups()['SecurityGroups']:
    if c['GroupName'] == 'SG_Ohio':
        faz_SG_Ohio=False
        logging.info("O grupo SG_Ohio com autorizações para as portas 22 e 5432 já existe")
        

if faz_SG_Ohio==True:  
    SG_Ohio = client_Ohio.create_security_group(
        GroupName = 'SG_Ohio',
        Description = 'SG_Ohio sg'  
    )
    logging.info("Securuty Group da Base de Dados está sendo criado")

    # ID do grupo de segurança de Ohio
    Gid_Ohio = SG_Ohio['GroupId']

    # Passando as portas
    client_Ohio.authorize_security_group_ingress(
        GroupId = Gid_Ohio,
        IpPermissions = [
            {
                "FromPort": 22,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 22
            },
            {
                "FromPort": 5432,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 5432
            },
                    {
                "FromPort": 8080,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 8080
            },
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 80
            }
        ]
    )

    logging.info("Securuty Group da Base de Dados foi criado com autorizações para as portas 22 e 5432")




# ---------------------------------------------------------------------------
# Criando Instância
USERDATA_SCRIPT_POSTGRES = '''#!/bin/bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y 
sudo -u postgres psql -c "create user cloud with encrypted password 'cloud';"
sudo -u postgres psql -c 'create database tasks with owner cloud;'
sudo echo "listen_addresses = '*'" >> /etc/postgresql/12/main/postgresql.conf
sudo echo "host all all 192.168.0.0/20 trust" >> /etc/postgresql/12/main/pg_hba.conf
sed -i '1i\host  all  all 0.0.0.0/0 md5'  /etc/postgresql/12/main/pg_hba.conf
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
'''
logging.info("Criando a instânca de banco de dados Postgres em Ohio")
instance_ohio = ec2_ohio.create_instances(
    ImageId="ami-0629230e074c580f2",
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    UserData=USERDATA_SCRIPT_POSTGRES,
    KeyName="KP_Ohio",
    SecurityGroups = ['SG_Ohio'],
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
ip_pub_postgres=get_public_ip(id_instance_ohio, "us-east-2")
print(ip_pub_postgres)

logging.info("A instância de Banco de Dados foi criada - Id = "+id_instance_ohio)

# ------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------
client_as = boto3.client('autoscaling', region_name="us-east-1")
logging.info("Criou autoscaling client na região us-east-1 (North Virginia)")
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Apagando o Auto Scaling
try:
    logging.info("Verificando se existe ASGroup_Projeto Auto Scaling Group em North Virginia")
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
        logging.info("Deletou o ASGroup_Projeto que existia em North Virginia")
        print("Deletou o Auto Scaling que existia")
except:
    logging.info("Não havia ASGroup_Projeto Auto Scaling Group")
    pass   

# ---------------------------------------------------------------------------
# Apagando o Launch Configuration
try:
    logging.info("Verificando de existe LC_Projeto Launch Configuration")
    LC_exite = client_as.describe_launch_configurations(
        LaunchConfigurationNames=[
            'LC_Projeto',
        ]
    )

    if len(LC_exite["LaunchConfigurations"])>0:
        client_as.delete_launch_configuration(
        LaunchConfigurationName='LC_Projeto'
        )
        logging.info("Deletou o LC_Projeto que existia em North Virginia")
        print("Deletou o Launch Configuration que existia")
except:
    logging.info("Não havia LC_Projeto Launch Configuration")
    pass 

# ---------------------------------------------------------------------------
# Criando o client
client_LB = boto3.client('elbv2', region_name="us-east-1")
logging.info("Criou elbv2 client na região us-east-1 (North Virginia)")

# ---------------------------------------------------------------------------
# Apagando o Load Balancer
try:
    logging.info("Verificando se existe LBProjeto Load Balancer em Noth Virginia")
    LB_existe = client_LB.describe_load_balancers(
        Names=[
            'LBProjeto'
        ]
    )
    if len(LB_existe["LoadBalancers"])>0:
        client_LB.delete_load_balancer(
            LoadBalancerArn=LB_existe["LoadBalancers"][0]["LoadBalancerArn"]
        )
        load_balancer_waiter_delete = client_LB.get_waiter('load_balancers_deleted')  
        load_balancer_waiter.wait(LoadBalancerArns=[LB_existe["LoadBalancers"][0]["LoadBalancerArn"]])   
        logging.info("Deletou o LBProjeto que existia em North Virginia")
        print("Deletou o Load Balancer que existia")
except:
    logging.info("Não havia LBProjeto Load Balancer")
    print("não exclui o load balancer")
    pass 

#time.sleep(120)



# ---------------------------------------------------------------------------
# Apagando o Securuty Group
# try:
#     client_North_Virginia.delete_security_group(
#         GroupName='SG_Load_Balancer'
#     )
#     print("apagando SC LB")
#     logging.info("O Securuty Group SG_Load_Balancer foi deletado em North Virginia")
# except:
#     print("não apagou SC LB")
#     logging.info("Não havia SG_Load_Balancer Securuty Group")
#     pass     

# ---------------------------------------------------------------------------


ec2_North_Virginia = boto3.resource('ec2', region_name="us-east-1")
logging.info("Criou ec2 resource na região us-east-1 (North Virginia)")

client_North_Virginia = boto3.client('ec2', region_name="us-east-1")
logging.info("Criou ec2 client na região us-east-1 (North Virginia)")

# ---------------------------------------------------------------------------
#Apagando par de chaves
logging.info("Deletando Key Pair região us-east-1 (North Virginia)")
try:
    client_North_Virginia.delete_key_pair(
        KeyName='KP_North_Virginia'
    )
    logging.info("Key Pair KP_North_Virginia foi deletada")
except:
    logging.info("Key Pair KP_North_Virginia não existia")
    pass

# ---------------------------------------------------------------------------
# Gerando par de chaves 
KP_North_Virginia = client_North_Virginia.create_key_pair(KeyName = 'KP_North_Virginia')
file = open("KP_North_Virginia.pem", 'w')
file.write(KP_North_Virginia['KeyMaterial'])
file.close
logging.info("Key Pair KP_North_Virginia foi criada")

# ---------------------------------------------------------------------------
# Apagando o Securuty Group
# logging.info("Deletando Securuty Group do Django região us-east-1 (North_Virginia)")
# #try:
# client_North_Virginia.delete_security_group(
#     GroupName='SG_North_Virginia'
# )
# logging.info("Securuty Group SG_North_Virginia foi deletada")
# #except:
#     #logging.info("Securuty Group SG_North_Virginia não existia")
#     #pass



# ---------------------------------------------------------------------------
# Criando Security Group
faz_SG_North_Virginia=True
for c in client_North_Virginia.describe_security_groups()['SecurityGroups']:
        if c['GroupName'] == 'SG_North_Virginia':
            logging.info("O grupo SG_North_Virginia com autorizações para as portas 22 e  já 8080 existe")
            faz_SG_North_Virginia=False

if faz_SG_North_Virginia==True:    
    SG_North_Virginia = client_North_Virginia.create_security_group(
        GroupName = 'SG_North_Virginia',
        Description = 'SG_North_Virginia sg'  
    )
    logging.info("Securuty Group do ORM está sendo criado")

    # ID do grupo de segurança de Ohio
    Gid_North_Virginia = SG_North_Virginia['GroupId']

    # Passando as portas
    client_North_Virginia.authorize_security_group_ingress(
        GroupId = Gid_North_Virginia,
        IpPermissions = [
            {
                "FromPort": 22,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 22
            },
            {
                "FromPort": 8080,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 8080
            },
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 80
            }, {
                "FromPort": 5432,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 5432
            },
        ]
    )
    logging.info("Securuty Group da Base de Dados foi criado com autorizações para as portas 22 e 8080")

# ---------------------------------------------------------------------------
# Criando Instância

USERDATA_SCRIPT_ORM ='''#!/bin/bash
sudo apt update
cd /home/ubuntu
sudo git clone https://github.com/LaisNSilva/tasks.git
sudo sed -i s/"node1"/"''' + str(ip_pub_postgres) + '''"/g  tasks/portfolio/settings.py
cd tasks
sudo ./install.sh
sudo ufw allow 8080/tcp
sudo reboot
'''

logging.info("Criando a instânca de ORM Django em North Virginia")
instance_North_Virginia = ec2_North_Virginia.create_instances(
    ImageId="ami-083654bd07b5da81d",
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="KP_North_Virginia",
    SecurityGroups = ['SG_North_Virginia'],
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
ip=get_public_ip(id_instance_North_Virginia, "us-east-1")
print(ip)

logging.info("A instância de ORM foi criada - Id = "+id_instance_North_Virginia)

instance_North_Virginia = ec2_North_Virginia.Instance(id=id_instance_North_Virginia)
instance_North_Virginia.wait_until_running()

print('Sleep starting... ({0})'.format(150))
logging.info("Esperando a instância de North Virginia ser inicializada")
time.sleep(150)
print('Sleep ended')
logging.info("A instância de North Virginia foi inicializada")


instance_North_Virginia.reload()

# ---------------------------------------------------------------------------
# Criar AMI

print("Listando as imagens")
logging.info("Listando as imagens de North Virginia")
images = ec2_North_Virginia.images.filter(Owners=['self']) 
print(images)
print("Caso tenha a image AMI_Instace_2 irá deletá-la")
for image in images:
    if image.name=="AMI_Instace_2":
        image_del = ec2_North_Virginia.Image(image.id)
        image_del.deregister()
        print(f'AMI {image.id} successfully deregistered')
        logging.info(f'AMI {image.id} foi deletada')

print("Vai criar a imagem!")
logging.info("Criando a imagem da instância ORM em North Viginia")
image = instance_North_Virginia.create_image(
    InstanceId=id_instance_North_Virginia,
    Name='AMI_Instace_2',
    Description='AMI da segunda instancia',
    NoReboot=True
)

logging.info(f'AMI id: {image.id}')
print(f'AMI creation started: {image.id}')

logging.info("Esperando a imagem")
image.wait_until_exists(
    Filters=[
        {
            'Name': 'state',
            'Values': ['available']
        }
    ]
)


logging.info("A imagem de ORM em North Viginia está pronta")

print(f'AMI {image.id} successfully created')

# ---------------------------------------------------------------------------
#Destruindo a segunda instancia
terminate_instance(id_instance_North_Virginia, "us-east-1")
logging.info("A instândo de ORM Djando em North Virginia foi encerrada")




# ---------------------------------------------------------------------------
# Descrevendo o Auto Scaling
while len(ASGroup_existe["AutoScalingGroups"])>0:
    ASGroup_existe = client_as.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            'ASGroup_Projeto',
        ]
    )

# ---------------------------------------------------------------------------
# Criando o LaunchConfiguration 
logging.info("Criando o Launch Configuration em North Virginia")
LaunchConfiguration = client_as.create_launch_configuration(
    LaunchConfigurationName='LC_Projeto',
    ImageId=image.id,
    KeyName='Lais',
    SecurityGroups=[
        'SG_North_Virginia',
    ],
    InstanceType="t2.micro"
)

logging.info("O Launch Configuration LC_Projeto foi criado")
print("Criou o Launch Configuration")

# ---------------------------------------------------------------------------
zones_lista = client_North_Virginia.describe_availability_zones()["AvailabilityZones"]
zones=[]
for z in zones_lista:
    zones.append(z["ZoneName"])
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Criando o Auto Scaling Group
logging.info("Criando o Auto Scaling Group em North Virginia")
ASGroup=client_as.create_auto_scaling_group(
    AutoScalingGroupName="ASGroup_Projeto",
    LaunchConfigurationName="LC_Projeto",
    MinSize=1,
    MaxSize=3,
    AvailabilityZones= zones 
)

logging.info("O Auto Scaling Group ASGroup_Projeto foi criado")
print("Criou o Auto Scaling Groups")




# ---------------------------------------------------------------------------
# Criando Security Group
faz_SG_Load_Balancer=True
for c in client_North_Virginia.describe_security_groups()['SecurityGroups']:
        if c['GroupName'] == 'SG_Load_Balancer':
            Gid_Load_Balancer = c['GroupId']
            logging.info("O SG_Load_Balancer já existe")
            faz_SG_Load_Balancer=False

if faz_SG_Load_Balancer==True:
    SG_Load_Balancer = client_North_Virginia.create_security_group(
        GroupName = 'SG_Load_Balancer',
        Description = 'SG_Load_Balancer sg'  
    )

    logging.info("Securuty Group do Load Balancer está sendo criado")

    # ID do grupo de segurança de Ohio
    Gid_Load_Balancer = SG_Load_Balancer['GroupId']

    # Passando as portas
    client_North_Virginia.authorize_security_group_ingress(
        GroupId = Gid_Load_Balancer,
        IpPermissions = [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
                "ToPort": 80
            }
        ]
    ) 
    logging.info("Securuty Group do Load Balancer foi criado com autorizações para a porta 80")   

# ---------------------------------------------------------------------------
# Apagando Target Group
try:
    logging.info("Verificando se existe TGProjeto Target Group em Noth Virginia")
    TG_existe = client_LB.describe_target_groups(
        Names=[
            'TGProjeto'
        ],
    )
    if len(TG_existe["TargetGroups"])>0:
        client_LB.delete_target_group(
            TargetGroupArn=TG_existe["TargetGroups"][0]["TargetGroupArn"]
        )
        logging.info("Deletou o TGProjeto que existia em North Virginia")
        print("Deletou o Target Group que existia")
except:
    logging.info("Não havia TGProjeto Target Group")
    pass

# ---------------------------------------------------------------------------
# Criando o Target Group Group
logging.info("Criando o Target Group em North Virginia")
TargetGroup = client_LB.create_target_group(
    Name='TGProjeto',
    Protocol='HTTP',
    Port=8080,
    VpcId='vpc-7086360a',
    TargetType='instance',
    IpAddressType='ipv4'
)
logging.info("O Target Group TGProjeto foi criado")
print("Criou o Target Group")

# ---------------------------------------------------------------------------
subnets_lista=client_North_Virginia.describe_subnets()['Subnets']
subnets=[]
for s in subnets_lista:
        subnets.append(s['SubnetId'])
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Criando o Load Balancer
logging.info("Criando o Load Balancer em North Virginia")
LoadBlanacer = client_LB.create_load_balancer(
    Name='LBProjeto',
    Type='application',
    Subnets= subnets, 
    Scheme='internet-facing',
    IpAddressType='ipv4',
    SecurityGroups=[Gid_Load_Balancer]
)

logging.info("Esperando o Load Balancer ficar pronto")
load_balancer_waiter = client_LB.get_waiter('load_balancer_available')
load_balancer_waiter.wait(LoadBalancerArns=[LoadBlanacer["LoadBalancers"][0]["LoadBalancerArn"]])

logging.info("O Load Balancer LBProjeto foi criado")
print("Criou o Load Balancer")

# ---------------------------------------------------------------------------
TG = client_LB.describe_target_groups(
        Names=[
            'TGProjeto'
        ],
)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Anexando
anexo_LB_TG = client_as.attach_load_balancer_target_groups(
    AutoScalingGroupName='ASGroup_Projeto',
    TargetGroupARNs=[TG["TargetGroups"][0]["TargetGroupArn"]
    ]
)

logging.info("O Auto Scaling Group foi anexado ao Target Group do Load Balancer")



# ---------------------------------------------------------------------------
# Listener

print("Vou criar o listener")
logging.info("Criando o Listener")
listener = client_LB.create_listener(
    LoadBalancerArn=LoadBlanacer["LoadBalancers"][0]["LoadBalancerArn"],
    Protocol='HTTP',
    Port=80,
    DefaultActions=[{'Type': 'forward', 'TargetGroupArn': TG["TargetGroups"][0]["TargetGroupArn"]}]
)
logging.info("O listener foi criado")
print("Criei o listener")

# ---------------------------------------------------------------------------
# Policy
LB = LoadBlanacer['LoadBalancers'][0]['LoadBalancerArn']
TG = TargetGroup["TargetGroups"][0]["TargetGroupArn"]
lb_name = LB[LB.find("app"):]
tg_name = TG[TG.find("targetgroup"):]

logging.info("Criando a Policy do Auto Scaling Group")
policy = client_as.put_scaling_policy(
    AutoScalingGroupName='ASGroup_Projeto',
    PolicyName='policy_ASGroup',
    PolicyType='TargetTrackingScaling',
    TargetTrackingConfiguration={
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": 'ALBRequestCountPerTarget',
                    "ResourceLabel": f"{lb_name}/{tg_name}"
                },
                "TargetValue": 50
            }
        
)
logging.info("A Policy do Auto Scaling Group foi criada")


#-------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------





















                    


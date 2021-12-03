import boto3
import os
from botocore.exceptions import ClientError
import time
import requests
import logging

logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


client_LB = boto3.client('elbv2', region_name="us-east-1")
LB_existe = client_LB.describe_load_balancers(
    Names=[
        'LBProjeto'
    ]
)

DNS=LB_existe["LoadBalancers"][0]["DNSName"]


sair="N"


token=requests.post("http://"+DNS+"/api-token-auth/" ,  data={"username": "cloud", "password": "cloud"})
cloud_token = token.json()['token']
a='Token '+cloud_token


while sair=="N":

    acao = input("Digite 1 para listar usuários, 2 para listar grupos, 3 para criar usuário, 4 para criar grupo, 5 paradeletar usuario, 6 para deletar grupo: ")
    print(acao)

    
    if acao=='1':
        res = requests.get("http://"+DNS+"/users" , headers={'Authorization': a})
        print(res)
        print(res.json())
        logging.info('GET '+str(res)+str(res.json()))
    elif acao=='2':
        res = requests.get("http://"+DNS+"/groups" , headers={'Authorization': a})
        print(res)
        print(res.json())
        logging.info('GET '+str(res)+str(res.json()))
    elif acao=='3':
        username = input("Digite o username: ")
        email = input("Digite o e-mail: ")
        res = requests.post("http://"+DNS+"/users/", data={"username": username, "email": email}, headers={'Authorization': a})
        print(res)
        print(res.json())
        logging.info('POST '+str(res)+str(res.json()))
    elif acao=='4':
        nome_grupo = input("Digite o nome do grupo: ")
        res = requests.post("http://"+DNS+"/groups/" , data={"name": nome_grupo}, headers={'Authorization': a})
        print(res)
        print(res.json())
        logging.info('POST '+str(res)+str(res.json()))
    elif acao =='5':
        id_user = input("Digite o id: ")
        res = requests.delete("http://"+DNS+"/users/"+id_user+"/", headers={'Authorization': a})
        print(res)
        logging.info('DELETE '+str(res))
    else:
        id_group = input("Digite o id: ")
        res = requests.delete("http://"+DNS+"/users/"+id_group+"/", headers={'Authorization': a})
        print(res)
        logging.info('DELETE '+str(res))
        



    
    

    sair=input("Parar requisições? S/N: ")

print("Saiu das requisições")
logging.info('Saiu das requisições')






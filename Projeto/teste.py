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

sair="N"

while sair=="N":

    acao = input("Digite 1 para listar usuários, 2 para listar grupos, 3 para criar usuário, 4 para criar grupo: ")
    print(acao)

    #res = requests.get("http://"+DNS+"/admin/")
    if acao=='1':
        res = requests.get("http://"+DNS+"/users" , auth=('cloud', 'cloud'))
        print(res.json())
    elif acao=='2':
        res = requests.get("http://"+DNS+"/groups" , auth=('cloud', 'cloud'))
        print(res.json())
    elif acao=='3':
        username = input("Digite o username: ")
        email = input("Digite o e-mail: ")
        res = requests.post("http://"+DNS+"/users/", data={"username": username, "email": email}, auth=('cloud', 'cloud'))
    elif acao=='4':
        nome_grupo = input("Digite o nome do grupo: ")
        res = requests.post("http://"+DNS+"/groups/" , data={"name": nome_grupo}, auth=('cloud', 'cloud'))
    elif acao =='5':
        id_user = input("Digite o id: ")
        res = requests.delete("http://"+DNS+"/users/"+id_user+"/", auth=('cloud', 'cloud'))
    else:
        id_group = input("Digite o id: ")
        res = requests.delete("http://"+DNS+"/users/"+id_group+"/", auth=('cloud', 'cloud'))



    print(res)
    

    sair=input("Parar requisições? S/N: ")

print("Saiu das requisições")






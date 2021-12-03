from functions.utils import *
from datetime import datetime
import os
import logging
USERDATA_SCRIPT_POSTGRES = get_scripts('Script_Postgres.sh')
try:
    os.remove("./log.txt")
except:
    pass

os.remove("./log.log")

logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logging.info("bbbbbbbbbbbb")
# arq = open('log.txt','w')

# log('aaa', arq)
# log('bbb', arq)

print(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
#print(USERDATA_SCRIPT_POSTGRES)

# teste= open('test.txt','w')
# teste.write('a\n')
# teste.write('b\n')
# teste.close()

# teste = open('test.txt','w')
# teste.write('c\n')
# teste.write('\n')
# teste.close()

logging.info('aa')






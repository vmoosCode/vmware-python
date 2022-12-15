import os
import paramiko as pm
from getpass import getpass
import argparse
from  tabulate import tabulate
import json

"""
CLi interaction based script that creates a environments which contains a number of desired VMs, then starts them at once.
script consists of 2 files, the script itself and a file to store created environments.
I made this script cause am lazy :) to open ESXi host GUI and then to start VM one by one as i have many environments that may contains a 3+ VMs
i hope you enjoy using it and i'll be happy to have pull requests for updates.

vmoosCode

i'll make the following features:
- suspend VMs
- Guest shutdown 
- delete/update environments.
"""


def get_args():
    parser = argparse.ArgumentParser(description="Script to auto start environments",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-e", "--esxi")
    parser.add_argument("-u", "--username")
    args = parser.parse_args()

    password = getpass('password: ')
    args = vars(args)
    args['password'] = password
    # args['password'] =  ""
    return args

def ssh_esxi(ip, username,password):
    port= 22
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
    ssh.connect(ip,port,username, password)
    return ssh

def load_vms(session):
    stding, stdout, stderr = session.exec_command('vim-cmd vmsvc/getallvms')
    lines = stdout.readlines()
    # vms dict keys represebt vm name, and the value represent vm ID 
    vms = {} 
    for line in lines:
        l = line.split()
        vms[l[1]] = l[0]
    # with open('vms.json','w') as f:
    #     f.write(json.dumps(vms))
    return vms

def create_environment(session):
    allvms = load_vms(session)
    print('Discovered VMs \n')
    vms_table=  []
    for vm in allvms:
        if vm != 'Name':
            vms_table.append([vm,allvms[vm]])
    print(tabulate(vms_table, headers=['Name', 'ID']))
    print('---------------------------------------\n')
    print('Enter VM id and seperate with comma: ')
    vms_ids = input()
    print('\n Environment name: ')
    env_name = input()
    vms_ids = vms_ids.replace(" ","")
    vms_ids = vms_ids.split(",")
    current_envs = {}
    if os.path.getsize('environments.json') > 0:
        with open('environments.json', 'r') as file:
            reader= file.read()

            if reader != None:
                current_envs = json.loads(reader)
            file.close()

    current_envs[env_name] = vms_ids
    print(current_envs)
    with open('environments.json', 'w') as file:
        j  = json.dumps(current_envs)
        file.write(j)
        file.close()
        
    print(f'Environment --> {env_name} <-- successfully created! \n')
    print(f'Would you like to start --> {env_name} <-- Environment ?')
    selection = input()
    if selection == 'y' or selection == 'Y' or selection == "yes":
        toggleVm(vms_ids,session)

def toggleVm(vm_ids,session):
    for vm in vm_ids:
        stding, stdout, stderr = session.exec_command(f'vim-cmd vmsvc/power.getstate {vm}')
        vms_clean_list = [el.strip() for el in stdout.readlines()]
        print(vms_clean_list)
        if 'Powered off' in vms_clean_list:
            print(f'Will power on vm id {vm}')
            estding, estdout, estderr = session.exec_command(f'vim-cmd vmsvc/power.on {vm}')
            print(estdout.readlines())
            print(f'VM power on successfully')
    
def start_environment(session):
    with open('environments.json','r') as f:
        reader = f.read()
        environments=  json.loads(reader)
        print('Available Environments: \n')
        for i in environments:
            print('-'+i )
        selection = input('Enter environment name (case sensetive): ')
        if selection in environments.keys():
            # for vm in environments[selection]:
            #     print(vm)
            #     toggleVm(vm,session)
            toggleVm(environments[selection],session)
        else:
            print('THis environment not exist!!!')

def shutdownHost(session):
    print("proceed in host shutdown")
    stding, stdout, stderr = session.exec_command(f'poweroff -f')

if __name__ == "__main__":
    args = get_args()
    session = ssh_esxi(args['esxi'], args['username'], args['password'])
    vms = load_vms(session)
    print('=======================================')
    print()
    print('What would you like to do :')
    print()
    print(
        ' 1- Create Environment (set of vms to starts together) \n',
        '2- Start predefined Environment \n',
        '3- Shutdown ESXi Host \n',
        '4- Exit'
    )
    print()
    print('=======================================')
    selection = input()
    match selection:
        case "1":
            create_environment(session)
        case "2":
            start_environment(session)
        case "3":
            shutdownHost(session)
        case "4":
            session.close()
            exit()
    session.close()

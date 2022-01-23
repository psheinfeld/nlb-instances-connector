import argparse
import json
import oci
import json
import os
import logging

##known "BUG" - documentation declares delete command with : , but actual call is with . (instance port separator)

def run_oci_cli_command(command):
    try:
        result = subprocess.run(command.split(" "), stdout=subprocess.PIPE)
        output = json.loads(result.stdout.decode('utf-8'))
        return True,output
    except Exception as e:
        return False,e

def get_instances_by_compartment(compartment_id):
    command = 'oci compute instance list --all -c {0} --auth instance_principal --query data[?\"lifecycle-state\"!=\'TERMINATED\' && \"lifecycle-state\"!=\'TERMINATING\'].id'.format(compartment_id)
    sucessfull,instances = run_oci_cli_command(command)
    return instances if sucessfull else []


def get_ip_and_subnet_for_instances_list(instances):
    ip_and_subnet_list = []
    for instance_id in instances:
        command = 'oci compute instance list-vnics --instance-id {0} --auth instance_principal --query data[*].[\"private-ip\",\"subnet-id\"]'.format(instance_id)
        sucessfull,ip_and_subnet = run_oci_cli_command(command)
        ip_and_subnet_list.append(ip_and_subnet) if sucessfull else print('error reading ip and subnet for {0}'.format(instance_id))
    return ip_and_subnet_list


def get_ip_ocid_for_instances_list(ip_and_subnet_list):
    ips_list = []
    for [[ip,subnet]] in ip_and_subnet_list:
        command = 'oci network private-ip list --all --ip-address {0} --subnet-id {1} --auth instance_principal --query data[0].id'.format(ip,subnet)
        sucessfull,ip_ocid = run_oci_cli_command(command)
        ips_list.append(ip_ocid) if sucessfull else print('error reading ocid for ip {0} in subnet {1}'.format(ip,subnet))
    return ips_list


def get_ip_ocids_from_nlb_and_backendset(nlb_id,backendset_name):
    command = 'oci nlb backend list --network-load-balancer-id {0} --backend-set-name {1} --all --auth instance_principal --query data.items[].\"target-id\"'.format(nlb_id,backendset_name)
    sucessfull,backend_ip_ocids = run_oci_cli_command(command)
    return backend_ip_ocids if sucessfull else []


def get_instances_by_instance_pool(compartment_id,instance_pool_id):
    command = 'oci compute-management instance-pool list-instances -c {0} --instance-pool-id {1} --all --auth instance_principal --query data[].id'.format(compartment_id,instance_pool_id)
    sucessfull,instances = run_oci_cli_command(command)
    return instances if sucessfull else []


def compartment_groups(args):
    if not args.compartment:
        return
    for argument in args.compartment:
        try:
            compartment_id = argument[0]
            nlb_id = argument[1].split(":")[0]
            backendset_name = argument[1].split(":")[1]
            port = argument[1].split(":")[2]
        except Exception as e:
            print('arguments error...exiting')
            print(e)
            exit()
        
        print('\ncompartment_OCID: {0}\nNLB_OCID: {1}\nbackendset_name: {2}\nport: {3}'.format(compartment_id,nlb_id,backendset_name,port))

        instances = get_instances_by_compartment(compartment_id)
        print('\nFound {0} non-terminated instances in compartment'.format(len(instances)))
        print(instances)
        
        ip_and_subnet_list = get_ip_and_subnet_for_instances_list(instances)
        print('\nFound {0} non-terminated instance ips and subnets in compartment'.format(len(ip_and_subnet_list)))
        print(ip_and_subnet_list)

        ips_list = get_ip_ocid_for_instances_list(ip_and_subnet_list)
        print('\nFound {0} non-terminated instance ips in compartment'.format(len(ips_list)))
        print(ips_list)

        backend_ip_ocids = get_ip_ocids_from_nlb_and_backendset(nlb_id,backendset_name)
        print('\nFound {0} backends ip ocids in nlb'.format(len(backend_ip_ocids)))
        print(backend_ip_ocids)

        #if ip is active and not in backend -> add to backend
        for ip_ocid in ips_list:
            if ip_ocid not in backend_ip_ocids:
                print('\nAttaching {0} to {1}:{2} of {3}'.format(ip_ocid,backendset_name,port,nlb_id))
                command = 'oci nlb backend create --backend-set-name {0} --network-load-balancer-id {1} --port {2} --target-id {3} --wait-for-state SUCCEEDED --auth instance_principal --query data[].status'.format(backendset_name,nlb_id,int(port),ip_ocid)
                sucessfull,responce = run_oci_cli_command(command)
                print(responce)

        #if ip in the backend is not part of the group (could be terminated) -> remove from backend
        for ip_ocid in backend_ip_ocids:
            if ip_ocid not in ips_list:
                print('\nRemoving {0} from {1}:{2} of {3}'.format(ip_ocid,backendset_name,port,nlb_id))
                command = 'oci nlb backend delete --backend-set-name {0} --network-load-balancer-id {1} --backend-name {2}.{3} --wait-for-state SUCCEEDED --auth instance_principal --force'.format(backendset_name,nlb_id,ip_ocid,int(port))
                sucessfull,responce = run_oci_cli_command(command)
                print(responce)


def instance_pool_groups(args):
    if not args.instance_pool:
        return
    for argument in args.instance_pool:
        try:
            compartment_id = argument[0]
            nlb_id = argument[1].split(":")[0]
            backendset_name = argument[1].split(":")[1]
            port = argument[1].split(":")[2]
            instance_pool_id = argument[2]
        except Exception as e:
            print('arguments error...exiting')
            print(e)
            exit()

        print('\ncompartment_OCID: {0}\nNLB_OCID: {1}\nbackendset_name: {2}\nport: {3}\ninstance_pool: {4}'.format(compartment_id,nlb_id,backendset_name,port,instance_pool_id))

        instances = get_instances_by_instance_pool(compartment_id,instance_pool_id)
        print('\nFound {0} instances in the instance pool'.format(len(instances)))
        print(instances)

        ip_and_subnet_list = get_ip_and_subnet_for_instances_list(instances)
        print('\nFound {0} non-terminated instance ips and subnets in compartment'.format(len(ip_and_subnet_list)))
        print(ip_and_subnet_list)

        ips_list = get_ip_ocid_for_instances_list(ip_and_subnet_list)
        print('\nFound {0} non-terminated instance ips in compartment'.format(len(ips_list)))
        print(ips_list)

        backend_ip_ocids = get_ip_ocids_from_nlb_and_backendset(nlb_id,backendset_name)
        print('\nFound {0} backends ip ocids in nlb'.format(len(backend_ip_ocids)))
        print(backend_ip_ocids)

        #if ip is active and not in backend -> add to backend
        for ip_ocid in ips_list:
            if not (ip_ocid in backend_ip_ocids):
                print('\nAttaching {0} to {1}:{2} of {3}'.format(ip_ocid,backendset_name,port,nlb_id))
                command = 'oci nlb backend create --backend-set-name {0} --network-load-balancer-id {1} --port {2} --target-id {3} --wait-for-state SUCCEEDED --auth instance_principal --query data.status'.format(backendset_name,nlb_id,int(port),ip_ocid)
                sucessfull,responce = run_oci_cli_command(command)
                print(responce)

        #if ip in the backend is not part of the group (could be terminated) -> remove from backend
        for ip_ocid in backend_ip_ocids:
            if not (ip_ocid in ips_list):
                print('\nRemoving {0} from {1}:{2} of {3}'.format(ip_ocid,backendset_name,port,nlb_id))
                command = 'oci nlb backend delete --backend-set-name {0} --network-load-balancer-id {1} --backend-name {2}.{3} --wait-for-state SUCCEEDED --auth instance_principal --force --query data.status'.format(backendset_name,nlb_id,ip_ocid,int(port))
                sucessfull,responce = run_oci_cli_command(command)
                print(responce)




if __name__ == "__main__":
    log = init_log()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--compartment',action='append',nargs='+')
    parser.add_argument('-dg','--dynamic-group',action='append',nargs='+')
    parser.add_argument('-ip','--instance-pool',action='append',nargs='+')
    args = parser.parse_args()

    if (not (args.compartment or args.dynamic_group or args.instance_pool)):
        print("execution arguments missing...exiting")
        exit()
    
    instance_pool_groups(args)
    
import argparse
import subprocess
import json

parser = argparse.ArgumentParser()

parser.add_argument('-c','--compartment',action='append',nargs='+')
parser.add_argument('-dg','--dynamic-group',action='append',nargs='+')
parser.add_argument('-ip','--instance-pool',action='append',nargs='+')

args = parser.parse_args()

#instance_id ='ocid1.instance.oc1.eu-frankfurt-1.antheljrenqmchqcpqyodzlezb6ijwoj6kjzbhkpbimnny4dbdj6clqg4glq'

backendset_name = 'backendset_2021-1104-1815'
nlb_id ='ocid1.networkloadbalancer.oc1.eu-frankfurt-1.amaaaaaaenqmchqaio23brpah5dynld73t3bbneah5baugxjg5eihnhrjt6a'
port = 0
#ip_ocid ='ocid1.privateip.oc1.eu-frankfurt-1.abtheljrac6dxqmp2ymhpccg6h2nbizgg6cawu6fsi6kiufynr5f5wmpineq'
#ip_ocid = 'ocid1.privateip.oc1.eu-frankfurt-1.abtheljrlv66dvncjppsqkkjxsfsa6pwkagcini7lpjrs3l5hwwos4un6aza'
ip_ocid = 'ocid1.privateip.oc1.eu-frankfurt-1.abtheljrzf4ux4vqxlsrps3ks3qszvfh2kgemmolmt4h4vouz6wpon6ck3lq'
command = 'oci nlb backend create --backend-set-name {0} --network-load-balancer-id {1} --port {2} --target-id {3} --wait-for-state SUCCEEDED --auth instance_principal'.format(backendset_name,nlb_id,port,ip_ocid)
#command = 'oci nlb backend delete --backend-set-name {0} --network-load-balancer-id {1} --backend-name {2}:{3} --wait-for-state SUCCEEDED --auth instance_principal --force'.format(backendset_name,nlb_id,ip_ocid,int(port))
result = subprocess.run(command.split(" "), stdout=subprocess.PIPE)
output = json.loads(result.stdout.decode('utf-8'))
print(output)


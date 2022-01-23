import oci
import json
import os
import logging
import base64



class OCIInstance(object):
    def __init__(self,id, instance,vnic_attachment):
        self.id = id
        self.instance = instance
        self.vnic_attachment = vnic_attachment

    def add_vnic(self,vnic):
        self.vnic = vnic

    def __str__(self):
        return self.id + " " + self.vnic_attachment.id #instance.display_name + " " + str(self.id)


def get_vnic(vnic_attachment,networking_client):
    try:
        vnic = networking_client.get_vnic(vnic_attachment.vnic_id).data
        return vnic
    except Exception as e:
        log.error("error geting vnic: {}".format(e))
        return {}


def init_log():
    log = logging.getLogger('k8sLabeler')
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log


def read_environment_variable(name,default_value=None,mandatory=True,base64encoded=False):
    value = os.getenv(name)
    default_value_used = False

    if not value and mandatory:
        log.error('mandatory environment variable {} not set - exiting'.format(name))
        exit()
    
    if not value and default_value:
        value = default_value
        default_value_used = True
        #log.info('{} not set, using default value {}'.format(name,default_value))

    if(base64encoded):
        value = base64.b64decode(value)

    if(default_value_used):
        log.info('{} not set, using default value {}'.format(name,value))

    return value



def get_map(compartment_id, compute_client,networking_client,get_vnic_info):
    map = []
    instances_list = []
    vnic_attachments = []
    try:
        list_instances_response = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                compartment_id
            )
        instances_list = list_instances_response.data
    except Exception as e:
        log.error("error geting instances: {}".format(e))

    try:
        list_vnic_attachments_response = oci.pagination.list_call_get_all_results(
                compute_client.list_vnic_attachments,
                compartment_id
            )
        vnic_attachments = list_vnic_attachments_response.data
    except Exception as e:
        log.error("error geting vnic attachments: {}".format(e))

    for instance in instances_list:
        notFound = True
        for vnic_attachment in vnic_attachments:
            if vnic_attachment.instance_id == instance.id:
                notFound = False
                map.append(OCIInstance(instance.id,instance,vnic_attachment))
                #map.append({"id":instance.id,"instance":instance,"vnic_attachment":vnic_attachment})
                #instance["vnic_attachment"] = vnic_attachment
                break
        if notFound:
            log.warning("no vNIC for instance {} ".format(instance.id))

    if get_vnic_info:
        for instance in map:
            instance.add_vnic(get_vnic(instance.vnic_attachment,networking_client))
            #instance["vnic"]=get_vnic(instance["vnic_attachment"],networking_client)

    return map

def get_param_value(obj,param_path):
    try:
        path_parts = param_path.split(".")
        temp = obj
        for part in path_parts:
            if type(temp) is dict:
                temp = temp[part]
            else:
                temp = getattr(temp, part)
            if part == path_parts[-1]:
                return temp
    except Exception as e:
        log.error("error geting attribute {} for object {} : {}".format(param_path, type(obj), e))

if __name__ == '__main__':
    #log
    log = init_log()

    #collect environment variables 
    compartment_id = read_environment_variable('OCI_COMPARTMENT_ID')
    region = read_environment_variable('OCI_REGION')
    refresh_rate = read_environment_variable('OCI_REFRESH_RATE',2,False)
    get_vnic_info = read_environment_variable('OCI_GET_VNIC_INFO',True,False)
    extended_labels = read_environment_variable('OCI_EXTENDED_LABELS',"W10=",False,True)
    extended_specs = read_environment_variable('OCI_EXTENDED_SPECS',"W10=",False,True)

    #export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..aaaaaaaaxbfg6ojv6vpjehoi4iu6ifrfu3wmpry4hb32l44blu4ciyrqnxya"
    #export OCI_REGION="ocid1.compartment.oc1..aaaaaaaaxbfg6ojv6vpjehoi4iu6ifrfu3wmpry4hb32l44blu4ciyrqnxya"

    #configure clients
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    signer.refresh_security_token()
    identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    virtual_network_client = oci.core.VirtualNetworkClient(config={}, signer=signer)

    infra_map = get_map(compartment_id, compute_client,virtual_network_client,get_vnic_info)
    
    default_labels_list =  [("oci.oraclecloud.com/fault-domain", "instance.fault_domain"),\
                            ("creator","instance.defined_tags.Owner.Creator"),\
                            ("failure-domain.beta.kubernetes.io/zone","instance.availability_domain"),\
                            ("topology.kubernetes.io/zone","instance.availability_domain")]

    default_specs_list = [("spec.providerID", "instance.id")]

    #param_path = "instance.availability_domain"
    #param_path = "instance.shape_config.ocpus"
    #param_path = "vnic_attachment.id1"
    for instance in infra_map:
        for label in default_labels_list:
            val = get_param_value(instance,label[1])
            print(label[0] + " : " + val)
        for spec in default_specs_list:
            val = get_param_value(instance,spec[1])
            print(spec[0] + " : " + val)




    




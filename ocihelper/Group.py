import oci
import logging

class Instance(object):
    def __init__(self,id : str = "", instance: oci.core.models.instance.Instance = None):
        self._id = id
        self._instance = instance
    @property
    def id(self) -> str:
        return self._id
    @id.setter
    def id(self, id : str):
        self._id = id
    @property
    def instance(self)-> oci.core.models.instance.Instance:
        return self._instance
    @instance.setter
    def instance(self, instance : oci.core.models.instance.Instance):
        self._instance = instance
    @property
    def vnic_attachment(self) -> oci.core.models.vnic_attachment :
        return self._vnic_attachment
    @vnic_attachment.setter
    def vnic_attachment(self, vnic_attachment : oci.core.models.vnic_attachment):
        self._vnic_attachment = vnic_attachment
    @property
    def vnic(self) -> oci.core.models.vnic.Vnic:
        return self._vnic
    @vnic.setter
    def vnic(self, vnic : oci.core.models.vnic.Vnic):
        self._vnic = vnic


class Group(object):
    map = []
    def __init__(self,compartment_id : str,instance_pool_id : str):
        


    def __get_instances_by_instance_pool(compartment_id : str,instance_pool_id : str):
        return[]       
    

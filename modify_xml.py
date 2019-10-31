import json
import sys
import xml.etree.ElementTree as ET
from shutil import copyfile

ref_vm = sys.argv[1]
json_file = sys.argv[2]
print(json_file)


class xml_creation:
    def __init__(self):
        self = None

    def name(self,domain,new_name):
        n = domain.find('name')
        n.text = new_name

    def remove_uuid(self,domain):
        uuid = domain.find('uuid')
        domain.remove(uuid)

    def copy_(self,new_name):
        copyfile("/var/lib/libvirt/images/"+ref_vm+".img", "/var/lib/libvirt/images/"+new_name+".img")


    def change(self,domain,new_name):
        for child in domain.iter("source"):
            if 'file' in child.attrib:
                child.set('file','/var/lib/libvirt/images/'+new_name+'.qcow2')

    def remove_interface(self,domain):
        dev = domain.find('devices')
        for interfaces in dev.findall('interface'):
            dev.remove(interfaces)

    def set_network(self,domain,network):
        dev = domain.find('devices')
        interf = ET.SubElement(dev,'interface')
        interf.set('type','network')
        source = ET.SubElement(interf,'source')
        source.set('network',network)
        model = ET.SubElement(interf,'model')
        model.set('type','virtio')

    def set_vcpu(self,domain,num):
        vcpu = domain.find('vcpu')
        vcpu.set('vcpu',num)

    def set_ram(self,domain,num):
        ram = domain.find('memory')
        ram.set('memory',num)

    def set_disk(self,domain,num):
        disk = domain.find('currentMemory')
        disk.set('currentMemory',num)

if __name__ == "__main__":
    with open(json_file) as f:
        schema = json.load(f)

    for item in schema["guests"]:
        tree =ET.parse('/etc/libvirt/qemu/'+ref_vm+'.xml')
        domain = tree.getroot()
        xml_file = xml_creation()
        #xml_file.copy_(item["vm_name"])
        xml_file.name(domain,item["vm_name"])
        xml_file.remove_uuid(domain)
        xml_file.change(domain,item["vm_name"])
        xml_file.remove_interface(domain)
        xml_file.set_vcpu(domain,item["vcpu"])
        xml_file.set_ram(domain,item["ram"])
        xml_file.set_disk(domain,item["memory"])
        l = len(item["interface"])

        if l>0:
            for k in item["interface"]:
                xml_file.set_network(domain,k)

        tree.write('/etc/libvirt/qemu/'+item["vm_name"]+'.xml')









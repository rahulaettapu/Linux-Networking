from __future__ import print_function
import sys
import libvirt
import collections
from xml.dom import minidom
import ipaddress

def change_mac(mac, offset):
    return "{:012x}".format((int(mac, 16) + offset)%0x1000000000000)

def change_ip(ip, pre, offset):
    if(offset%(2**(32-pre)) == 0 or offset%(2**(32-pre)) == (2**(32-pre)-1)):
        return ipaddress.ip_interface(ip).ip;
    else:
        return ipaddress.ip_interface(ip).network[offset%(2**(32-pre))];

conn = libvirt.open('qemu:///system')

if conn == None:
    print('Failed to open connection to qemu:///system', file=sys.stderr)
    exit(1)
                
domain_id = conn.listDomainsID()
nets = conn.listAllNetworks();

if domain_id == None:
    print('Failed to get the domain IDs list object', file=sys.stderr)

if nets == None:
    print('Failed to get the virNetwork list object', file=sys.stderr)
                        
addrMACSet = list([]);
addrIPSet = list([]);

for vm in domain_id:
    dom = conn.lookupByID(vm);
    print("Trying domain %s" %dom.name());
    ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)
    for (name, val) in ifaces.iteritems():
        if name != "lo":
            addrMACSet.append(val['hwaddr']);
            print("Domain %s has interface %s with MAC address %s" %(dom.name(), name, val['hwaddr']));
            if val['addrs']:
                for ipaddr in val ['addrs']:
                    if ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                        print("Domain %s has interface %s with IPv4 address %s/%d" %(dom.name(), name, ipaddr['addr'],ipaddr['prefix']));
                        addrIPSet.append(ipaddr['addr']);

for netW in nets:
    raw_xml = netW.XMLDesc(0);
    netsXML = minidom.parseString(raw_xml);
    macTags = netsXML.getElementsByTagName('mac');
    ipTags = netsXML.getElementsByTagName('ip');
    if(macTags != None and len(macTags) >= 1):
        addrMACSet.append(str(macTags[0].getAttribute('address')));
    if(ipTags != None and len(ipTags) >= 1):
        addrIPSet.append(str(ipTags[0].getAttribute('address')));

addrMACCounts = collections.Counter(addrMACSet);
addrIPCounts = collections.Counter(addrIPSet);

for vm in domain_id:
    dom = conn.lookupByID(vm);
    ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)
    raw_xml = dom.XMLDesc(0);
    ifxml = minidom.parseString(raw_xml);
    devices = ifxml.getElementsByTagName('mac');
    confChange = False;
    netConfChange = False;
    for (name, val) in ifaces.iteritems():
        if name != "lo":
            oldAddr = str(val['hwaddr']);
            if(addrMACCounts[val['hwaddr']] > 1):
                for dev in devices:
                    if(str(val['hwaddr']) == str(dev.getAttribute('address'))):
                        newAddr = val['hwaddr'];
                        i = 1;
                        while(newAddr in addrMACCounts or (newAddr == "00:00:00:00:00:00")):
                            newStr =  change_mac(dev.getAttribute('address').replace(':',''),i);
                            newAddr = newStr[0:2] + ':' + newStr[2:4] + ':' + newStr[4:6] + ':' +  newStr[6:8] + ':' + newStr[8:10] + ':' + newStr[10:];
                            i+=1;
                        addrMACCounts[val['hwaddr']] += -1;
                        print("Domain %s Interface %s MAC address changed to %s" %(dom.name(), name, newAddr));
                        dev.setAttribute('address',newAddr);
                        val['hwaddr'] = newAddr;
                        addrMACCounts.update({newAddr:1});
                        confChange = True;
            if val['addrs']:
                for ipaddr in val ['addrs']:
                    if ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                        if(addrIPCounts[ipaddr['addr']] > 1):
                            for dev in devices:
                                if(str(val['hwaddr']) == str(dev.getAttribute('address'))):
                                    netToMod = str(dev.parentNode.getElementsByTagName('source')[0].getAttribute('network'));
                                    for netW in nets:
                                        if(str(netToMod) == str(netW.name())):
                                            raw_xml = netW.XMLDesc(0);
                                            netsXML = minidom.parseString(raw_xml);
                                            dhcHosts = netsXML.getElementsByTagName('dhcp')[0].getElementsByTagName('host');
                                            newAddr = ipaddr['addr'];
                                            i=1;
                                            while(newAddr in addrIPCounts):
                                                newAddr =  str(change_ip(u"" + ipaddr['addr'] + '/' +str(ipaddr['prefix']),int(ipaddr['prefix']),i));
                                                i+=1;
                                            addrIPCounts[ipaddr['addr']] += -1;
                                            print("Domain %s Interface %s IP address changed to %s" %(dom.name(), name, newAddr));
                                            ipaddr['addr'] = newAddr;
                                            addrIPCounts.update({newAddr:1});
                                            netConfChange = False;
                                            for d in dhcHosts:
                                                if(((str(d.getAttribute('mac')) == oldAddr) and (str(d.getAttribute('name')) == dom.name()))):
                                                    d.setAttribute('ip',newAddr);
                                                    confChange = True;
                                                    netConfChange = True;
                                                    netW.destroy();
                                                    while(True):
                                                        if(netW.isActive() == 0):
                                                            break;
                                                    conn.networkDefineXML(netsXML.toxml());
                                                    conn.networkCreateXML(netsXML.toxml());
                                                    while(True):
                                                        if(netW.isActive() == 1):
                                                            break;
                                            if(netConfChange == False):
                                                dhcHosts = netsXML.getElementsByTagName('dhcp')[0];
                                                d = netsXML.createElement('host');
                                                d.setAttributeNode(netsXML.createAttribute('mac'));
                                                d.setAttributeNode(netsXML.createAttribute('ip'));
                                                d.setAttributeNode(netsXML.createAttribute('name'))
                                                d.setAttribute('ip',newAddr);
                                                d.setAttribute('mac',val['hwaddr']);
                                                d.setAttribute('name',dom.name());
                                                dhcHosts.appendChild(d);
                                                confChange = True;
                                                netW.destroy();
                                                while(True):
                                                    if(netW.isActive() == 0):
                                                        break;
                                                conn.networkDefineXML(netsXML.toxml());
                                                conn.networkCreateXML(netsXML.toxml());
                                                while(True):
                                                    if(netW.isActive() == 1):
                                                        break;
                                                                                                                                                                      
    if(confChange):
        dom.shutdown();
        while(True):
            if(dom.isActive() == 0):
                break;
        conn.defineXMLFlags(ifxml.toxml(),libvirt.VIR_DOMAIN_DEFINE_VALIDATE);
        conn.createXML(ifxml.toxml(),0);
        while(True):
            if(dom.isActive() == 1):
                break;

print(addrMACCounts);
print(addrIPCounts);
conn.close();
exit(0)

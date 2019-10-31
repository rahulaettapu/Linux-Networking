#!/bin/bash

interface_name=$1
ip_adress=$2

req_ip=$(echo "$ip_adress" | cut -d '.' -f 1-3)

echo interface = $interface_name >> /etc/dnsmasq.conf
echo dhcp-range = $interface_name, $req_ip.2, $req_ip.254 >> /etc/dnsmasq.conf
#dhcprange=$(echo "$interface_name, $req_ip.2, $req_ip.254")
#echo $req_ip
#echo $dhcprange
#sudo dnsmasq --interface= $interface_name  --except-interface=lo --bind-interfaces --dhcp-range= $dhcprange
sudo systemctl restart dnsmasq

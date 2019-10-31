#!/bin/bash
ip_addr=$1
br_name=$2


addr=$(echo "$ip_addr" | cut -d '.' -f 1-3)
net_addr=$addr.0/24

#runt iptables -S
iptables -A INPUT -i $br_name -p udp -m udp --dport 53 -j ACCEPT
iptables -A INPUT -i $br_name -p tcp -m tcp --dport 53 -j ACCEPT
iptables -A INPUT -i $br_name -p udp -m udp --dport 67 -j ACCEPT
iptables -A INPUT -i $br_name -p tcp -m tcp --dport 67 -j ACCEPT
iptables -A FORWARD -d $net_addr -o $br_name -j ACCEPT
iptables -A FORWARD -s $net_addr -i $br_name -j ACCEPT
iptables -A FORWARD -i $br_name -o $br_name -j ACCEPT
iptables -A FORWARD -o $br_name -j REJECT --reject-with icmp-port-unreachable
iptables -A FORWARD -i $br_name -j REJECT --reject-with icmp-port-unreachable
iptables -A OUTPUT -o $br_name -p udp -m udp --dport 68 -j ACCEPT


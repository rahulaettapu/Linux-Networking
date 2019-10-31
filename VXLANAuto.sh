#!/bin/bash

if [ $# -ne 7 ];
then
	echo "Illegal number of params"
	exit
fi

ip netns exec $1 ip link add name $5 type vxlan id $7 dev ${1}Tr remote $4 dstport 4789
ip netns exec $1 ip link set dev $5 up
ip netns exec $1 brctl addif ${1}Br $5
ip netns exec $2 ip link add name $6 type vxlan id $7 dev ${2}Tr remote $3 dstport 4789
ip netns exec $2 ip link set dev $6 up
ip netns exec $2 brctl addif ${2}Br $6

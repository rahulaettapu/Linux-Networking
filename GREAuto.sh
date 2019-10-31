#!/bin/bash

if [ $# -ne 8 ];
then
	echo "Illegal number of params"
	exit
fi

ip netns exec $1 ip tunnel add $7 mode gre local $3 remote $4
ip netns exec $1 ip link set dev $7 up
ip netns exec $1 ip route add $5 dev $7
ip netns exec $2 ip tunnel add $8 mode gre local $4 remote $3
ip netns exec $2 ip link set dev $8 up
ip netns exec $2 ip route add $6 dev $8

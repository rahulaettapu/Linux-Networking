#!/bin/bash

if [ $# -ne 4 ];
then
	echo "Illegal number of params"
	exit
fi

ip netns exec $1 ip link set dev $3 down
ip netns exec $2 ip link set dev $4 down
ip netns exec $1 ip tunnel delete $3
ip netns exec $2 ip tunnel delete $4

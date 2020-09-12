#!/bin/bash

# files to delete
List=(
    "/etc/wpa_supplicant.conf" 
    "/etc/init.d/S35oneshot"
    )

for Item in ${List[*]} 
    do
        echo "deleting $Item"
        ssh buildroot "rm $Item"
    done
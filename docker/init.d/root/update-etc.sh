#!/bin/bash

# 사용자 계정 추가
for fname in $(\ls /mnt/etc/*) ; do
    fname=$(basename ${fname})
    if [ -f /mnt/etc/${fname} ] ; then
         cat /mnt/etc/${fname} >> /etc/${fname}
    fi
done

# sudoer 추가
if [ -f /mnt/etc/passwd ] ; then
    for user_name in $(cat /mnt/etc/passwd | grep -v ^# | cut -f1 -d':') ; do
        adduser ${user_name} sudo
    done

    echo "sudoer 사용자 권한 추가"
    echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
fi

# skel 복사
if [ -d /mnt/etc/skel ] ; then
    for fname in $(\ls /mnt/etc/skel/*) ; do
        fname=$(basename ${fname})
        if [ -f /mnt/etc/skel/${fname} ] ; then
            rsync -av /mnt/etc/skel/ /root/
        fi
    done
fi

#!/bin/bash

# extra 추가
for extra in hosts group gshadow passwd shadow ; do
    if [ -f /etc/${extra}.extra ] ; then
        echo "${extra}.extra 추가"

        echo >> /etc/${extra}
        echo "# extra" >> /etc/${extra}
        cat /etc/${extra}.extra >> /etc/${extra}
    fi
done

# 사용자 계정 추가
if [ -d /mnt/etc ] ; then
    for fname in $(\ls /mnt/etc/*) ; do
        fname=$(basename ${fname})
        if [ -f /mnt/etc/${fname} ] ; then
             cat /mnt/etc/${fname} >> /etc/${fname}
        fi
    done
fi

# sudoer 추가
for passwd in /mnt/etc/passwd /etc/passwd.extra ; do
    if [ -f ${passwd} ]; then
        for user_name in $(cat ${passwd} | grep -v ^# | cut -f1 -d':') ; do
            adduser ${user_name} sudo
        done
    fi
done

echo "sudoer 사용자 권한 추가"
echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# skel 복사
if [ -d /mnt/etc/skel ] ; then
    for fname in $(\ls /mnt/etc/skel/*) ; do
        fname=$(basename ${fname})
        if [ -f /mnt/etc/skel/${fname} ] ; then
            rsync -av /mnt/etc/skel/ /root/
        fi
    done
fi


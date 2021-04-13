#!/bin/bash
#############################################################


rename 's/\s+/ /g' */*

rename 's/zip/zip/i' */*
rename 's/rar/rar/i' */*

find . -name "*.rar" -print | perl -nle '($d1,$d2,$f)=split(/\//, $_); print "echo \"$_\"; cd $d2; unrar x -y *.rar;cd .."' | sh -


export UNZIP="-O CP949"
export ZIPINFO="-O CP949"

find . -name "*.zip" -print | perl -nle '($d1,$d2,$f)=split(/\//, $_); print "echo \"$_\"; cd $d2; unzip -o *.zip;cd .."' | sh -

rename 's/\s+/ /g' */*
rename 's/smi/smi/i' */*


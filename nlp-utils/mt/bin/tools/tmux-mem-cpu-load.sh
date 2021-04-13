#!/bin/bash

tmux-mem-cpu-load $1 | perl -ple 's/ //g; s/(MB|\%)/$1\t/g;' | cut -f1,2 | tr '\t' ' '

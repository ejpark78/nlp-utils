#!/bin/bash

# -i 1 -m 0 -g 0
# 3482/16050MB  0.0% 0.23 0.28 0.36

if [[ "$(tmux-mem-cpu-load)" != "" ]] ; then 
    cpu=$(tmux-mem-cpu-load $1 | perl -ple 's/(.+?MB)\s*(.+?) .+$/$2 $1/; s/\//MB\//; s/\d{3,3}MB/GB/g; s/^\s+|\s+$//g;' | cut -f1)
    cpu="CPU($cpu)"
fi

if [[ "$(which nvidia-smi)" != "" ]] && [[ "$(nvidia-smi | grep Error)" == "" ]] ; then 
    gpu=$(nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader \
      | perl -ple 's/, / /g; s/ \%/\%/g; s/\% /\//; s/ MiB/MB/g; s/MB /MB\//; s/\d{3,3}MB/GB/g;')

    gpu="GPU($gpu)"
fi

if [[ "$cpu" != "" ]] || [[ "$gpu" != "" ]] ; then
    echo $cpu $gpu
fi


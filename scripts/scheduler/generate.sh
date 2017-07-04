#!/bin/bash

echo '' > result.json
for year in {1998..2004} ; do
    cat template.json | perl -ple 's/2017/'${year}'/g;' | tee -a result.json
done

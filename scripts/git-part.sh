#!/usr/bin/env bash

git clone https://gollum/LP/crawler.git ./

git config core.sparseCheckout true

echo "dictionary" >> .git/info/sparse-checkout
echo "model/ner.josa.model" >> .git/info/sparse-checkout
echo "rsc" >> .git/info/sparse-checkout
echo "*.so" >> .git/info/sparse-checkout
echo "sp_config.ini" >> .git/info/sparse-checkout
echo "NCKmat.py" >> .git/info/sparse-checkout
echo "NCNamedEntity.py" >> .git/info/sparse-checkout
echo "NCNlpUtil.py" >> .git/info/sparse-checkout
echo "NCSPProject.py" >> .git/info/sparse-checkout

git read-tree -mu HEAD

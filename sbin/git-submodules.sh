#!/usr/bin/env bash


git ls-files --stage

git rm --cached language_lab_utils

git submodule add http://galadriel.korea.ncsoft.corp/ejpark/language_lab_utils.git

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import gzip
import glob

import nltk
from nltk.tag import pos_tag_sents 
from nltk.tokenize import word_tokenize 

reload(sys)
sys.setdefaultencoding("utf-8")

def split(arr, count):
	return [arr[i::count] for i in range(count)]

if __name__ == '__main__':
	# nltk.download()

	i = 0
	for line in sys.stdin:
		line = line.strip()
		line = line.replace('|', ' ')
		line = re.sub(u'\s+', ' ', line)

		if i%100. == 0.:
			sys.stderr.write("\rReview %d" % (i))
			sys.stderr.flush()
		i += 1

		try:
			tagged_sent = []
			for tag in pos_tag_sents([word_tokenize(line.strip())])[0] :
				tagged_sent.append("%s/%s" % (tag[0], tag[1]))

			print " ".join(tagged_sent)
		except:
			print "ERROR: %s" % line



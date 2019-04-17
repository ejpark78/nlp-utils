
.ONESHELL:
release-g7:
	rsync -avz --delete --exclude=*.tar.gz ./ g7:crawler/build/
#	rsync -avz --delete ../config/ g7:crawler/config/

.ONESHELL:
release-g5:
	rsync -avz --delete --exclude=*.tar.gz ./ g5:crawler/build/
#	rsync -avz --delete ../config/ g5:crawler/config/

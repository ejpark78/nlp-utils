
release-g7:
	rsync -avz --delete --exclude=*.tar.gz ./ g7:crawler/build/
	rsync -avz --delete ../config/jobs/ g7:crawler/config/jobs/
	rsync -avz --delete ../config/parsing/ g7:crawler/config/parsing/

release-g5:
	rsync -avz --delete --exclude=*.tar.gz ./ g5:crawler/build/
	rsync -avz --delete ../config/jobs/ g5:crawler/config/jobs/
	rsync -avz --delete ../config/parsing/ g5:crawler/config/parsing/

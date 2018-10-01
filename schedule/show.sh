list=`cat aws_crawler.list`
for l in $list ; do
	echo "- $l"
	docker logs $l -t  2>&1 |tail -5; 
done

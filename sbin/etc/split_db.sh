#!/usr/bin/env bash

time {

echo -e "PRAGMA foreign_keys=OFF;\nBEGIN TRANSACTION;" > 2005.sql
sqlite3 2005-03.db .schema >> 2005.sql
echo -e ".mode insert text $t\nSELECT * FROM text WHERE url LIKE '%view/2005%';" | sqlite3 2005-03.db >> 2005.sql
echo -e "COMMIT;" >> 2005.sql
sync && sqlite3 2005.db < 2005.sql

}



echo -e "PRAGMA foreign_keys=OFF;\nBEGIN TRANSACTION;" > 2006.sql
sqlite3 2005-03.db .schema >> 2006.sql
echo -e ".mode insert text $t\nSELECT * FROM text WHERE url LIKE '%view/2006%';" | sqlite3 2005-03.db >> 2006.sql
echo -e "COMMIT;" >> 2006.sql
sync && sqlite3 2006.db < 2006.sql

# split by month


time {
    y=2006
    for i in {1..10} ; do
        month=$(printf "%02d" $i)
        echo $month; 

        sql="$y-$month.sql"

        echo -e "PRAGMA foreign_keys=OFF;\nBEGIN TRANSACTION;" > $sql
        sync && sqlite3 2005-03-01~2005-11.db .schema >> $sql
        sync && echo -e ".mode insert text\nSELECT * FROM text WHERE url LIKE '%view/$y"$month"%';" | sqlite3 2005-03-01~2005-11.db >> $sql
        sync && echo -e "COMMIT;" >> $sql
        sync && cat $sql | sqlite3 $y-$month.db
        sync && rm $sql
    done
}






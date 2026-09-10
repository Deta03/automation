#!/bin/bash

SOURCE=$1
DESTINATION=${2:-/backup}

if [ -z "$SOURCE"]; then
	echo "error: sourse does not  specifed"
	exit 1
fi
if [! -d "$SOURCE"]; then
	echo " error: sourse does not exist" 
	exit 1
fi
if if [! -d "$DESTINATION"]; then 
	echo " error: backup does not exist"
	exit 1
fi

DATE=$(date +%Y-%m-%d)

tar-czf  "$DESTINATION/backup_$DATE.tar.gz" "$SOURSE"

if [$? -ne 0]; then
	echo "error: backup failed"
	exit 1
fi

echo "backup completed successfully"

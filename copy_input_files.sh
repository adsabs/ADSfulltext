set -e

INPUT_BASE=/proj/ads/abstracts/config/
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_BASE=./logs/input/input.$TIMESTAMP/



# path and min sizes for files, size is set to ~90% of current size
FILES_INFO=(
    links/fulltext/all.links:5500000
)

# Delete old input files
if [ -d ./logs/input ]; then
    find ./logs/input/ -name "input.20*-*-*_*-*-*" -type d -mtime +20 -exec rm -rf '{}' \;
fi

# create local copies of files
echo hey $FILES_INFO
for FILE_INFO in ${FILES_INFO[@]} ; do
    FILE=${FILE_INFO%%:*}
    mkdir -p $(dirname "$OUTPUT_BASE$FILE")
    echo INFO: `date` copying $INPUT_BASE$FILE to $OUTPUT_BASE$FILE
    cp -v $INPUT_BASE$FILE $OUTPUT_BASE$FILE
done

# validate local files
for FILE_INFO in ${FILES_INFO[@]} ; do
    FILE=${FILE_INFO%%:*}
    MIN_LINES=${FILE_INFO##*:}
    echo INFO: `date` validating $OUTPUT_BASE$FILE is at least $MIN_LINES lines long
    if [ $(wc -l < $OUTPUT_BASE$FILE) -lt ${MIN_LINES} ]; then
	echo "ERROR: file $OUTPUT_BASE$FILE has less than ${MIN_LINES} lines, processing aborted"
	exit 1
    fi
done

# ingest code expects latest files in directory named current
echo INFO: `date` linking $PWD/logs/input/current to $PWD/$OUTPUT_BASE
rm -fv ./logs/input/current
ln -fsv $PWD/$OUTPUT_BASE $PWD/logs/input/current

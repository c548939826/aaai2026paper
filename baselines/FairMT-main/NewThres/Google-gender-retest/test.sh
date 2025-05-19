flag=$1
thresh=$2

python3 read2diff.py $flag
python3 read_diff.py $flag
python3 getscore.py  $flag
python3 ./readscore.py $thresh $flag

# !/bin/bash
flag=$1
thres=$2

input_file="../../experiments/$flag/en_tk.txt"
output_file="../../experiments/$flag/gender/f_en_mu.txt"
index_file="../../experiments/$flag/gender/en_mu.index"
final_output="../../experiments/$flag/gender/en_mu.txt"

python3 refine.py $thres $flag
python3 bertMuN.py "$input_file" "$output_file" "$index_file" $flag

# 拷贝输出文件
cp "$output_file" "$final_output"

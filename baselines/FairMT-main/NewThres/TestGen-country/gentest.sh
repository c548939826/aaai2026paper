#!/bin/bash

flag=$1

input_file="../../experiments/$flag/en_tk.txt"
output_file="../../experiments/$flag/country/f_en_mu.txt"
index_file="../../experiments/$flag/country/en_mu.index"
final_output="../../experiments/$flag/country/en_mu.txt"

python3 bertMuN.py "$input_file" "$output_file" "$index_file"

# 拷贝输出文件
cp "$output_file" "$final_output"

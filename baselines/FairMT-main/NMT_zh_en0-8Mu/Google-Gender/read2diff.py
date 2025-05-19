import sys
import os

# 获取命令行参数
flag = sys.argv[1]
base_dir = f"../../experiments/{flag}/gender"

# 打开文件
with open(os.path.join(base_dir, "f_en_mu.zh.beam"), "r") as f:
    zhlines = f.readlines()

with open(os.path.join(base_dir, "en_mu.txt"), "r") as f:
    enlines = f.readlines()

# 创建输出文件
f_Mut_en = open(os.path.join(base_dir, "Com_Original.en"), "w")
f_Ori_zh = open(os.path.join(base_dir, "Com_Mutated.zh"), "w")
f_Mut_zh = open(os.path.join(base_dir, "Com_Original.zh"), "w")
f_Ori_en = open(os.path.join(base_dir, "Com_Mutated.en"), "w")
f_Ori_O = open(os.path.join(base_dir, "Com_oracle.zh"), "w")

# 写入文件
for i in range(len(enlines)):
    en = enlines[i].strip() + "\n"
    zh = zhlines[i].strip() + "\n"  # " ".join(zhlines[i].strip().split("\t")[0].split()) + "\n"
    if i % 2 == 0:
        f_Ori_en.write(en)
        f_Ori_zh.write(zh)
    elif i % 2 == 1:
        f_Mut_en.write(en)
        f_Mut_zh.write(zh)
        f_Ori_O.write(zh)

# 关闭文件
f_Mut_en.close()
f_Mut_zh.close()
f_Ori_zh.close()
f_Ori_en.close()
f_Ori_O.close()

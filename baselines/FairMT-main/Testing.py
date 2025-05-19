import os
import shutil
import sys
flag = sys.argv[1]
thres = float(sys.argv[2])
Genderdirs = ['./NMT_zh_en0-8Mu/Google-Gender']
Countrydirs = ['./NMT_zh_en0-8Mu/Google-Country']

backup_dir = "./experiments/example"
base_dir = f"./experiments/{flag}"

if not os.path.exists(base_dir):
    shutil.copytree(backup_dir, base_dir)

os.system(f"python3 ./MutantGen-Test.py {flag}")

for gen, cou in zip(Genderdirs, Countrydirs):

    os.system(f"cp NewThres/TestGen-gender/*.txt NewThres/TestGen-gender/*.index {gen}")
    os.system(f"cd {gen} && sh desp.sh {flag}")
    os.system(f"cd {gen} && python3 lookupTrans.py {flag}")
    os.system(f"cd {gen} && sh test.sh {flag}")


    os.system(f"cp NewThres/TestGen-country/*.txt NewThres/TestGen-country/*.index {cou}")
    os.system(f"cd {cou} && sh desp.sh")
    os.system(f"cd {cou} && python3 lookupTrans.py {flag}")
    os.system(f"cd {cou} && sh test.sh {flag}")


final_dir = f"./experiments/{flag}_{thres:.2f}"
if not os.path.exists(final_dir):
    shutil.copytree(base_dir, final_dir)
os.system(f"python3 ./ReTesting.py {flag} {thres}")

temp_dir = f"./experiments/tmp_swap_dir"
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.rename(base_dir, temp_dir)
os.rename(final_dir, base_dir)
os.rename(temp_dir, final_dir)

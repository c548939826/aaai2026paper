import os
import sys
flag = sys.argv[1]
thres = float(sys.argv[2])
GenderRedirs = ['./NewThres/Google-gender-retest']
CountryRedirs = ['./NewThres/Google-country-retest']
for regen, recou in zip(GenderRedirs, CountryRedirs):
    os.system(f"cd {regen} && sh gentest.sh {flag} {thres}")
    os.system(f"cd {regen} && python3 lookupTrans.py {flag} {thres}")
    os.system(f"cd {regen} && sh test.sh {flag} {thres}")
    
    os.system(f"cd {recou} && sh gentest.sh {flag} {thres}")
    os.system(f"cd {recou} && python3 lookupTrans.py {flag} {thres}")
    os.system(f"cd {recou} && sh test.sh {flag} {thres}")

import os
import sys

flag = sys.argv[1] 

os.system(f"cd ./NewThres/TestGen-gender && sh gentest.sh {flag}")
os.system(f"cd ./NewThres/TestGen-country && sh gentest.sh {flag}")

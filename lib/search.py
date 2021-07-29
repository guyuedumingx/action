import sys
import subprocess

avgs = sys.argv
if avgs[1].strip().endswith("="):
    link = avgs[2]
else:
    link = avgs[1]
order = "start msedge " + link
subprocess.call(order.split(" "),shell=True)
    

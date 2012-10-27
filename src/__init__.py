import sys
import os
p = os.path
basedir = os.path.dirname(os.path.abspath(__file__)) + "/.."
ref_dirs = []
map((lambda d: sys.path.append(basedir + "/" + d)), ref_dirs)

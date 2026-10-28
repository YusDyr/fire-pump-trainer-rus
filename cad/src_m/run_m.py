import os, traceback
D=os.environ['NCPK_DIR']
try:
    exec(open(os.path.join(D,'build_m.py'),encoding='utf-8').read(), {'__file__':os.path.join(D,'build_m.py'),'__name__':'__main__'})
except SystemExit: pass
except Exception:
    open(os.path.join(D,'err.txt'),'w',encoding='utf-8').write(traceback.format_exc())
os._exit(0)

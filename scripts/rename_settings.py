import os
p=os.path.join('web','pages')
files=os.listdir(p)
for f in files:
    if 'Settings' in f and any(ord(c)>127 for c in f):
        src=os.path.join(p,f)
        dst=os.path.join(p,'04__Settings.py')
        print('Renaming',repr(src),'->',repr(dst))
        os.rename(src,dst)
        break
else:
    print('No non-ASCII Settings file found')

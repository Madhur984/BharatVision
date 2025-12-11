import os
from collections import defaultdict
p=os.path.join('web','pages')
if not os.path.exists(p):
    print('web/pages not found')
    raise SystemExit(1)
files=sorted(os.listdir(p))
print('Files in web/pages:')
for f in files:
    print('-',f)

non_ascii=[f for f in files if any(ord(c)>127 for c in f)]
if non_ascii:
    print('\nFiles with non-ASCII characters:')
    for f in non_ascii:
        print('-',f)
else:
    print('\nNo non-ASCII filenames found')

prefixes=defaultdict(list)
for f in files:
    parts=f.split('_',1)
    if parts and parts[0].isdigit():
        prefixes[parts[0]].append(f)

dups={k:v for k,v in prefixes.items() if len(v)>1}
if dups:
    print('\nDuplicate numeric prefixes found:')
    for k,v in dups.items():
        print(k,':')
        for fn in v:
            print('  -',fn)
else:
    print('\nNo duplicate numeric prefixes')

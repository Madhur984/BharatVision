import os
p=os.path.join('web','pages')
files=sorted(os.listdir(p))
for f in files:
    codepoints=[ord(c) for c in f]
    print(repr(f), len(f), codepoints)

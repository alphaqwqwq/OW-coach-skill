import os
path = r'd:\workspace\alphaqwq-home\src\App.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
old = "url: '/',"
new = "url: 'https://coach.alphaqwq.xyz',"
content = content.replace(old, new)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done: replaced', old, '->', new)

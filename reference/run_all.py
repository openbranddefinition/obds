from pathlib import Path
import re, subprocess, sys
root=Path(__file__).resolve().parent
total=0
for name in ["foundation","context-delivery","context-assembly","design-space","integration","golden","adversarial"]:
    p=subprocess.run([sys.executable,"-m","pytest","-q"],cwd=root/name,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(f"## {name}\n{p.stdout.strip()}")
    if p.returncode:
        raise SystemExit(p.returncode)
    m=re.search(r"(\d+) passed",p.stdout)
    total += int(m.group(1)) if m else 0
print(f"TOTAL: {total} passed")

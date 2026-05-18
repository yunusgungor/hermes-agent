#!/usr/bin/env python3
"""Python cache temizleyici"""
import os
import shutil

for root, dirs, files in os.walk('.'):
    for d in dirs:
        if d == '__pycache__':
            path = os.path.join(root, d)
            print(f"Siliniyor: {path}")
            shutil.rmtree(path, ignore_errors=True)
    for f in files:
        if f.endswith('.pyc'):
            path = os.path.join(root, f)
            os.remove(path)

print("Cache temizlendi")

#!/usr/bin/env python3
"""
Extrai partições lógicas de super.img.
Uso: python extract_super.py <super.img> <pasta_destino>
"""
import sys
import os
from utils import tool_path, run_tool, finish, log, progress

def is_sparse(image_path):
    with open(image_path, 'rb') as f:
        magic = f.read(4)
        return magic == b'\x3a\xff\x26\xed'  # sparse magic

def main():
    if len(sys.argv) != 3:
        print("Uso: extract_super.py <super.img> <out_dir>")
        sys.exit(1)
    
    super_img = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    
    # Converte de sparse para raw, se necessário
    if is_sparse(super_img):
        log("Detectada imagem esparsa. Convertendo para raw...")
        raw_img = os.path.join(out_dir, 'super_raw.img')
        code, _, stderr = run_tool('simg2img', super_img, raw_img)
        if code != 0:
            finish({"error": f"Falha na conversão sparse: {stderr}"})
        super_img = raw_img
        progress(30)
    
    log("Extraindo partições com lpunpack...")
    code, stdout, stderr = run_tool('lpunpack', super_img, out_dir)
    progress(80)
    
    if code != 0:
        finish({"error": f"Falha ao extrair super: {stderr}"})
    
    # Lista as partições geradas
    partitions = []
    for fname in os.listdir(out_dir):
        if fname.endswith('.img'):
            fpath = os.path.join(out_dir, fname)
            sz = os.path.getsize(fpath)
            partitions.append({"name": fname, "size": sz})
    
    progress(100)
    finish({"partitions": partitions, "out_dir": out_dir})

if __name__ == '__main__':
    main()
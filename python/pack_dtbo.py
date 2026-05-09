#!/usr/bin/env python3
"""
Reempacota um dtbo.img a partir de uma pasta com arquivos .dtb.
Uso: python pack_dtbo.py <pasta_dtbs> <saida.img>
"""
import sys
import os
import glob
from utils import tool_path, run_tool, finish, log, progress

def main():
    if len(sys.argv) != 3:
        print("Uso: pack_dtbo.py <dtbs_dir> <output.img>")
        sys.exit(1)
    
    dtbs_dir = sys.argv[1]
    output_img = sys.argv[2]
    
    dtbs = glob.glob(os.path.join(dtbs_dir, '*.dtb'))
    if not dtbs:
        finish({"error": "Nenhum arquivo .dtb encontrado"})
    
    cmd = ['mkdtimg', 'create', output_img] + dtbs
    log(f"Criando dtbo com {len(dtbs)} dtbs...")
    code, stdout, stderr = run_tool(*cmd)  # run_tool aceita lista ou expansão
    progress(100)
    
    if code != 0:
        finish({"error": f"Falha ao criar dtbo: {stderr}"})
    
    finish({"output": output_img})

if __name__ == '__main__':
    main()
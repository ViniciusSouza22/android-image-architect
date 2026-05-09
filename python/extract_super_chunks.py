#!/usr/bin/env python3
"""
Une chunks do super.img e extrai partições lógicas usando Python puro.
Uso: python extract_super_chunks.py <pasta_com_chunks_ou_arquivo> <pasta_destino>
"""
import sys
import os
import glob
import re
from pathlib import Path
from utils import finish, log, progress
from lp_unpack import LpUnpack

def main():
    if len(sys.argv) != 3:
        print("Uso: extract_super_chunks.py <pasta_com_chunks_ou_super.img> <out_dir>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    
    # Se for uma pasta, une os chunks
    if os.path.isdir(input_path):
        log(f"Procurando chunks em: {input_path}")
        all_files = glob.glob(os.path.join(input_path, '*_sparsechunk*'))
        if not all_files:
            finish({"error": "Nenhum arquivo de chunk encontrado."})
            return
        
        pattern = re.compile(r'_sparsechunk\.?(\d+)')
        chunk_files = []
        for f in all_files:
            m = pattern.search(f)
            if m:
                chunk_files.append((int(m.group(1)), f))
                log(f"Chunk: {os.path.basename(f)}")
        
        if not chunk_files:
            finish({"error": "Nenhum chunk válido."})
            return
        
        chunk_files.sort(key=lambda x: x[0])
        merged_sparse = os.path.join(out_dir, 'super_merged.img')
        with open(merged_sparse, 'wb') as out:
            for _, chunk_path in chunk_files:
                log(f"Juntando {os.path.basename(chunk_path)}")
                with open(chunk_path, 'rb') as f:
                    out.write(f.read())
        log("Chunks unidos.")
        super_img = merged_sparse
    else:
        # É um arquivo único (super.img ou chunk inicial)
        # Se for um chunk (ex: super.img_sparsechunk.0), une todos no mesmo diretório
        if '_sparsechunk' in os.path.basename(input_path):
            base_dir = os.path.dirname(input_path)
            pattern = re.compile(r'_sparsechunk\.?(\d+)')
            prefix = os.path.basename(input_path).split('_sparsechunk')[0]
            all_files = glob.glob(os.path.join(base_dir, f'{prefix}_sparsechunk*'))
            chunk_files = []
            for f in all_files:
                m = pattern.search(f)
                if m:
                    chunk_files.append((int(m.group(1)), f))
            chunk_files.sort(key=lambda x: x[0])
            merged_sparse = os.path.join(out_dir, 'super_merged.img')
            with open(merged_sparse, 'wb') as out:
                for _, chunk_path in chunk_files:
                    log(f"Juntando {os.path.basename(chunk_path)}")
                    with open(chunk_path, 'rb') as f:
                        out.write(f.read())
            super_img = merged_sparse
        else:
            super_img = input_path
    
    log("Processando super com Python puro...")
    progress(50)
    
    # Usa o LpUnpack para extrair - certifique-se de que OUTPUT_DIR é um Path
    try:
        unpacker = LpUnpack(
            SUPER_IMAGE=super_img,
            OUTPUT_DIR=Path(out_dir),   # ← CORREÇÃO AQUI
            SHOW_INFO=False
        )
        unpacker.unpack()
    except Exception as e:
        finish({"error": f"Falha ao extrair partições: {str(e)}"})
        return
    
    # Lista as partições geradas
    partitions = []
    for fname in os.listdir(out_dir):
        fpath = os.path.join(out_dir, fname)
        if os.path.isfile(fpath) and fname.endswith('.img') and fname != 'super_merged.img':
            sz = os.path.getsize(fpath)
            partitions.append({"name": fname, "size": sz})
    
    if not partitions:
        finish({"error": "Nenhuma partição foi extraída."})
        return
    
    progress(100)
    finish({"partitions": partitions, "out_dir": out_dir})

if __name__ == '__main__':
    main()
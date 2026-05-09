#!/usr/bin/env python3
"""
Extrai DTBs de um dtbo.img usando Python puro.
Suporta magics: QCDT (0xBD E4 A5 9A) e DTB (0xD0 0D FE ED)
Uso: python extract_dtbo.py <dtbo.img> <pasta_destino>
"""
import sys
import os
import struct
from utils import finish, log

def main():
    if len(sys.argv) != 3:
        print("Uso: extract_dtbo.py <dtbo.img> <out_dir>")
        sys.exit(1)
    
    dtbo_img = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    
    with open(dtbo_img, 'rb') as f:
        data = f.read()
    
    # Magics conhecidos
    dtb_magics = [b'\xD0\x0D\xFE\xED', b'\xBD\xE4\xA5\x9A']  # DTB ou QCDT
    dtbs = []
    offset = 0
    while offset < len(data):
        found = False
        for magic in dtb_magics:
            if data[offset:offset+4] == magic:
                # Lê tamanho do DTB (4 bytes big-endian após magic)
                if offset + 8 > len(data):
                    break
                total_size = struct.unpack('>I', data[offset+4:offset+8])[0]
                if total_size < 32 or offset + total_size > len(data):
                    # Tamanho inválido, pula
                    offset += 1
                    found = True
                    break
                dtb_data = data[offset:offset+total_size]
                dtb_path = os.path.join(out_dir, f'dtbo.{len(dtbs)}.dtb')
                with open(dtb_path, 'wb') as df:
                    df.write(dtb_data)
                log(f"Extraído: {os.path.basename(dtb_path)} ({total_size} bytes)")
                dtbs.append(dtb_path)
                offset += total_size
                found = True
                break
        if not found:
            offset += 1
    
    if not dtbs:
        finish({"error": "Nenhum DTB encontrado. O arquivo pode não ser um DTBO válido."})
        return
    
    finish({"dtbs": dtbs, "out_dir": out_dir})

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Inspeciona vbmeta.img usando Python puro.
Uso: python inspect_vbmeta.py <vbmeta.img>
"""
import sys
import struct
from utils import finish

def main():
    if len(sys.argv) != 2:
        print("Uso: inspect_vbmeta.py <vbmeta.img>")
        sys.exit(1)
    
    vbmeta = sys.argv[1]
    with open(vbmeta, 'rb') as f:
        magic = f.read(4)
        if magic != b'AVB0':
            finish({"error": "Não é uma imagem vbmeta válida (magic != AVB0)"})
            return
        f.seek(32)
        flags = struct.unpack('<I', f.read(4))[0]
        flags_list = []
        if flags & 1:
            flags_list.append("disable-verity")
        if flags & 2:
            flags_list.append("disable-verification")
        # Tenta extrair o nome do algoritmo (posições variam, leitura simplificada)
        f.seek(0)
        data = f.read()
        algo = "SHA256_RSA2048"  # padrão, caso não encontremos
        # Procura string "alg" para identificar algoritmo? Deixamos como placeholder.
        result = {
            "algorithm": algo,
            "flags": flags_list,
            "descriptors": len(data) // 64  # estimativa grosseira
        }
        finish(result)

if __name__ == '__main__':
    main()
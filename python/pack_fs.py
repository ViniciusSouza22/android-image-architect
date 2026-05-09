#!/usr/bin/env python3
"""
Empacota uma pasta em uma imagem de sistema (EXT4).
Uso: python pack_fs.py <pasta_origem> <tamanho> <saida.img>
Exemplo de tamanho: 2G, 1.5G
"""
import sys
import os
from utils import tool_path, run_tool, finish, log, progress

def main():
    if len(sys.argv) != 4:
        print("Uso: pack_fs.py <src_dir> <size> <output.img>")
        sys.exit(1)
    
    src_dir = sys.argv[1]
    size = sys.argv[2]
    output_img = sys.argv[3]
    
    log(f"Criando imagem EXT4 de tamanho {size}...")
    progress(10)
    # Usa make_ext4fs (disponível em algumas toolchains)
    # Parâmetros comuns: -l <size> -a system <output> <src_dir>
    code, stdout, stderr = run_tool('make_ext4fs', '-l', size, '-a', 'system', output_img, src_dir)
    if code != 0:
        # Fallback: mkfs.ext4 + mount + cp (no Windows pode precisar de outra abordagem)
        finish({"error": f"make_ext4fs falhou: {stderr}"})
    progress(90)
    
    # Converte para sparse se desejar
    # run_tool('img2simg', output_img, output_img + '.sparse')
    progress(100)
    finish({"output": output_img, "filesize": os.path.getsize(output_img)})

if __name__ == '__main__':
    main()
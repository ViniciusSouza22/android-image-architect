#!/usr/bin/env python3
"""
Reempacota boot.img a partir de uma pasta com componentes e boot_info.json.
Uso: python pack_boot.py <pasta_origem> <boot_info.json> <saida.img>
"""
import sys
import os
import json
from utils import tool_path, run_tool, finish, log, progress

def main():
    if len(sys.argv) != 4:
        print("Uso: pack_boot.py <source_dir> <info.json> <output.img>")
        sys.exit(1)
    
    src_dir = sys.argv[1]
    info_file = sys.argv[2]
    output_img = sys.argv[3]
    
    # Carrega as informações do cabeçalho
    with open(info_file) as f:
        info = json.load(f)
    header = info.get('header', {})
    
    cmd_args = ['--output', output_img]
    
    # Adiciona argumentos de acordo com os arquivos presentes
    kernel = os.path.join(src_dir, 'kernel')
    if os.path.exists(kernel):
        cmd_args += ['--kernel', kernel]
    ramdisk = os.path.join(src_dir, 'ramdisk')
    if os.path.exists(ramdisk):
        cmd_args += ['--ramdisk', ramdisk]
    dtb = os.path.join(src_dir, 'boot.img-dtb')
    if os.path.exists(dtb):
        cmd_args += ['--dtb', dtb]
    
    # Parâmetros do cabeçalho
    if 'cmdline' in header:
        cmd_args += ['--cmdline', header['cmdline']]
    if 'base' in header:
        cmd_args += ['--base', header['base']]
    if 'pagesize' in header:
        cmd_args += ['--pagesize', header['pagesize']]
    if 'os_version' in header:
        cmd_args += ['--os_version', header['os_version']]
    if 'os_patch_level' in header:
        cmd_args += ['--os_patch_level', header['os_patch_level']]
    
    log(f"Executando mkbootimg com: {cmd_args}")
    progress(30)
    code, stdout, stderr = run_tool('mkbootimg', *cmd_args)
    progress(90)
    
    if code != 0:
        finish({"error": f"Falha ao reempacotar: {stderr}"})
    
    finish({"output": output_img, "filesize": os.path.getsize(output_img)})

if __name__ == '__main__':
    main()
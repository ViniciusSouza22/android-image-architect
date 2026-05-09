#!/usr/bin/env python3
"""
Reempacota super.img a partir de uma pasta com partições modificadas.
Uso: python pack_super.py <pasta_particoes> <config.txt> <saida.img>
O arquivo config.txt deve conter os argumentos para lpmake (um por linha,
ex: '--metadata-size 65536').
"""
import sys
import os
from utils import tool_path, run_tool, finish, log, progress

def main():
    if len(sys.argv) != 4:
        print("Uso: pack_super.py <partitions_dir> <config.txt> <output.img>")
        sys.exit(1)
    
    parts_dir = sys.argv[1]
    config_file = sys.argv[2]
    output_img = sys.argv[3]
    
    log("Lendo configuração do super...")
    cmd_args = []
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            # Substitui caminhos relativos das imagens pelo caminho absoluto
            if line.startswith('--image ') or line.startswith('--partition_image '):
                # Exemplo: --image system=system.img
                parts = line.split('=', 1)
                if len(parts) == 2:
                    img_name = parts[1].strip().split()[0]  # system.img
                    img_path = os.path.join(parts_dir, img_name)
                    if os.path.exists(img_path):
                        # Reconstrói argumento com caminho correto
                        new_arg = f"{parts[0]}={img_path}"
                        cmd_args.append(new_arg)
                        continue
            # Para outros argumentos, apenas adiciona
            cmd_args.append(line)
    
    cmd_args += ['--output', output_img]
    
    log(f"Executando lpmake com {len(cmd_args)} argumentos...")
    progress(20)
    code, stdout, stderr = run_tool('lpmake', *cmd_args)
    progress(90)
    
    if code != 0:
        finish({"error": f"Falha ao reempacotar super: {stderr}"})
    
    # Se desejado, converte para sparse
    # run_tool('img2simg', output_img, output_img + '.sparse')
    finish({"output": output_img, "filesize": os.path.getsize(output_img)})

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Extrai conteúdo de imagens de sistema (EXT4/EROFS/F2FS/SquashFS)
Conversão sparse automática via Python puro (lp_unpack)
Uso: python extract_fs.py <imagem.img> <pasta_destino>
"""
import sys
import os
import struct
from utils import finish, log, progress, tool_path, run_tool

def is_sparse(img_path):
    """Verifica se a imagem é sparse (magic 0xED26FF3A)"""
    with open(img_path, 'rb') as f:
        return f.read(4) == b'\x3a\xff\x26\xed'

def detect_fs(img_path):
    """
    Tenta identificar o sistema de arquivos pelo magic number.
    Retorna: 'ext4', 'erofs', 'f2fs', 'squashfs' ou None
    """
    with open(img_path, 'rb') as f:
        # EXT4 superblock em 0x400 (offset 1024) -> magic em 0x438
        f.seek(0x438)
        sb = f.read(2)
        if sb == b'\x53\xef':
            return 'ext4'
        # EROFS magic no início
        f.seek(0)
        magic = f.read(4)
        if magic == b'\xe2\xe1\xf5\x04':
            return 'erofs'
        # F2FS magic em 0x400
        f.seek(0x400)
        magic = f.read(4)
        if magic == b'\x10\x20\xf5\xf2':
            return 'f2fs'
        # SquashFS magic (4 variantes)
        f.seek(0)
        magic = f.read(4)
        if magic in (b'hsqs', b'sqsh', b'shsq', b'qshs'):
            return 'squashfs'
    return None

def main():
    if len(sys.argv) != 3:
        print("Uso: extract_fs.py <imagem.img> <out_dir>")
        sys.exit(1)
    
    img = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    
    # ── Conversão sparse ──────────────────────
    if is_sparse(img):
        log("Imagem sparse detectada. Convertendo...")
        raw_img = os.path.join(out_dir, 'raw_temp.img')
        # Tenta simg2img externo
        code, _, stderr = run_tool('simg2img', img, raw_img)
        if code == 0:
            img = raw_img
        else:
            # Fallback Python puro usando lp_unpack
            try:
                from lp_unpack import SparseImage
                with open(img, 'rb') as f:
                    sparse = SparseImage(f)
                    if sparse.check():
                        log("Usando conversão Python pura (lp_unpack)...")
                        unsparse = sparse.unsparse()
                        img = str(unsparse)
                    else:
                        finish({"error": "Falha na verificação sparse."})
                        return
            except Exception as e:
                finish({"error": f"Falha na conversão sparse: {e}"})
                return
        log("Conversão concluída.")
    
    # ── Detecção do sistema de arquivos ────────
    fs = detect_fs(img)
    
    # Se 7z estiver disponível, usa-o como método preferencial
    if os.path.exists(tool_path('7z')):
        log(f"Extraindo com 7z (sistema de arquivos: {fs or 'desconhecido'})...")
        code, _, stderr = run_tool('7z', 'x', f'-o{out_dir}', '-y', img)
        if code == 0:
            finish({"out_dir": out_dir})
        else:
            log(f"7z falhou: {stderr}")
            # Continua para métodos Python se 7z falhar
    
    # Se não detectou e não tem 7z, erro
    if not fs:
        finish({"error": "Sistema de arquivos não suportado e 7z não disponível. "
                         "Coloque 7z.exe na pasta tools/ ou instale a biblioteca 'ext4' (pip install ext4)."})
        return
    
    log(f"Sistema de arquivos detectado: {fs}")
    
    # ── Método Python puro para EXT4 ───────────
    if fs == 'ext4':
        try:
            from ext4 import Volume
            with open(img, 'rb') as f:
                vol = Volume(f)
                def extract_dir(directory, current_path):
                    for entry in directory.iter_entries():
                        if entry.name in ('.', '..'):
                            continue
                        full_path = os.path.join(current_path, entry.name)
                        if entry.is_dir:
                            os.makedirs(full_path, exist_ok=True)
                            extract_dir(entry, full_path)
                        else:
                            with open(full_path, 'wb') as out:
                                out.write(entry.read())
                os.makedirs(out_dir, exist_ok=True)
                extract_dir(vol.root, out_dir)
            finish({"out_dir": out_dir})
        except ImportError:
            finish({"error": "Biblioteca 'ext4' não instalada. "
                             "Use 'pip install ext4' ou coloque 7z.exe na pasta tools/ para extrair EXT4."})
    else:
        # Para outros sistemas (erofs, f2fs, squashfs) sem 7z, não podemos extrair em Python puro
        finish({"error": f"Extração de {fs} não implementada em Python puro. "
                         "Adicione 7z.exe na pasta tools/ para extrair este formato."})

if __name__ == '__main__':
    main()
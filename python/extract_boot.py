#!/usr/bin/env python3
"""
Extrai boot.img usando parsing Python puro.
Suporta cabeçalhos v2, v3, v4 e fallback para versões desconhecidas.
Também tenta identificar o modelo do dispositivo via campo 'name' ou ramdisk.
"""
import sys
import os
import struct
import gzip
import io
import re

from utils import finish, log, progress

def main():
    if len(sys.argv) != 3:
        print("Uso: extract_boot.py <boot.img> <out_dir>")
        sys.exit(1)
    
    boot_img = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    
    log(f"Iniciando extracao de {boot_img}")
    progress(10)
    
    try:
        with open(boot_img, 'rb') as f:
            data = f.read()
    except Exception as e:
        finish({"error": f"Nao foi possivel ler o arquivo: {str(e)}"})
        return
    
    if data[:8] != b'ANDROID!':
        finish({"error": "Arquivo nao e uma imagem boot valida (magic != ANDROID!)"})
        return
    
    header_version = struct.unpack('<I', data[8:12])[0]
    kernel_size = struct.unpack('<I', data[12:16])[0]
    ramdisk_size = struct.unpack('<I', data[20:24])[0]
    page_size = struct.unpack('<I', data[40:44])[0] if len(data) > 43 else 2048
    
    # Força v2 se versão inválida mas tamanhos coerentes
    if header_version not in (0, 1, 2, 3, 4):
        log(f"Aviso: versao de cabecalho {header_version} desconhecida. Tentando v2.")
        if kernel_size <= 0 or ramdisk_size <= 0 or kernel_size > len(data) or ramdisk_size > len(data):
            finish({"error": "Tamanhos invalidos. Arquivo corrompido."})
            return
        header_version = 2
    
    log(f"Versao do cabecalho: {header_version}")
    progress(30)
    
    header_info = {
        "magic": "ANDROID!",
        "version": header_version,
        "page_size": page_size,
        "kernel_size": kernel_size,
        "ramdisk_size": ramdisk_size
    }
    
    # Tenta ler o campo 'name' (offset 48, 16 bytes para v0/v1, 32 bytes para v2+)
    try:
        if header_version in (0, 1, 2):
            name_len = 32 if header_version >= 2 else 16
            name_bytes = data[48:48+name_len].split(b'\x00')[0]
            name = name_bytes.decode('ascii', errors='ignore').strip()
            if name:
                header_info['device_name'] = name
    except:
        pass
    
    # Tenta ler cmdline
    try:
        if header_version in (0, 1, 2):
            cmdline_off = 64
            end = data[cmdline_off:].find(b'\x00')
            if end > 0:
                cmdline = data[cmdline_off:cmdline_off+end].decode('latin-1')
                header_info['cmdline'] = cmdline
    except:
        pass
    
    files = []
    
    # Extração conforme versão
    if header_version in (0, 1, 2):
        kernel_offset = page_size
        ramdisk_offset = ((kernel_offset + kernel_size - 1) // page_size + 1) * page_size
        
        kernel_data = data[kernel_offset:kernel_offset+kernel_size]
        ramdisk_data = data[ramdisk_offset:ramdisk_offset+ramdisk_size]
        
        if kernel_size > 0:
            with open(os.path.join(out_dir, 'kernel'), 'wb') as f:
                f.write(kernel_data)
            files.append({"name": "kernel", "size": kernel_size})
            log(f"kernel extraido ({kernel_size} bytes)")
        
        if ramdisk_size > 0:
            ramdisk_path = os.path.join(out_dir, 'ramdisk.cpio.gz')
            with open(ramdisk_path, 'wb') as f:
                f.write(ramdisk_data)
            files.append({"name": "ramdisk.cpio.gz", "size": ramdisk_size})
            log(f"ramdisk extraido ({ramdisk_size} bytes)")
            
            # Tenta obter modelo da ramdisk (default.prop)
            try:
                with gzip.open(ramdisk_path, 'rb') as gz:
                    cpio_bytes = gz.read()
                # Procura por padrão ro.product.model=...
                match = re.search(rb'ro\.product\.model=(.*?)\n', cpio_bytes)
                if match:
                    model = match.group(1).decode('utf-8', errors='ignore').strip()
                    header_info['model_from_ramdisk'] = model
                    log(f"Modelo detectado na ramdisk: {model}")
            except:
                # ramdisk pode não ser gzip (ex: lz4), ignora
                pass
        
        # DTB (opcional)
        second_size = struct.unpack('<I', data[28:32])[0]
        second_offset = ((ramdisk_offset + ramdisk_size - 1) // page_size + 1) * page_size
        dtb_offset = second_offset + second_size
        dtb_data = b''
        dtb_size = 0
        remaining = data[dtb_offset:]
        dtb_magic = b'\xd0\x0d\xfe\xed'
        idx = remaining.find(dtb_magic)
        if idx != -1:
            dtb_offset += idx
            if len(remaining) > idx + 8:
                dtb_total_size = struct.unpack('>I', remaining[idx+4:idx+8])[0]
                dtb_data = remaining[idx:idx+dtb_total_size]
                dtb_size = dtb_total_size
            if dtb_size > 0:
                with open(os.path.join(out_dir, 'boot.img-dtb'), 'wb') as f:
                    f.write(dtb_data)
                files.append({"name": "boot.img-dtb", "size": dtb_size})
                log(f"dtb extraido ({dtb_size} bytes)")
    
    elif header_version in (3, 4):
        header_size = 4096 if header_version == 3 else struct.unpack('<I', data[44:48])[0]
        kernel_offset = header_size
        ramdisk_offset = kernel_offset + kernel_size
        kernel_data = data[kernel_offset:kernel_offset+kernel_size]
        ramdisk_data = data[ramdisk_offset:ramdisk_offset+ramdisk_size]
        
        if kernel_size > 0:
            with open(os.path.join(out_dir, 'kernel'), 'wb') as f:
                f.write(kernel_data)
            files.append({"name": "kernel", "size": kernel_size})
        if ramdisk_size > 0:
            ramdisk_path = os.path.join(out_dir, 'ramdisk.cpio.gz')
            with open(ramdisk_path, 'wb') as f:
                f.write(ramdisk_data)
            files.append({"name": "ramdisk.cpio.gz", "size": ramdisk_size})
            # Tentativa de extrair modelo (igual acima)
            try:
                with gzip.open(ramdisk_path, 'rb') as gz:
                    cpio_bytes = gz.read()
                match = re.search(rb'ro\.product\.model=(.*?)\n', cpio_bytes)
                if match:
                    model = match.group(1).decode('utf-8', errors='ignore').strip()
                    header_info['model_from_ramdisk'] = model
                    log(f"Modelo detectado na ramdisk: {model}")
            except:
                pass
    
    progress(90)
    result = {
        "header": header_info,
        "files": files,
        "out_dir": out_dir
    }
    finish(result)

if __name__ == '__main__':
    main()
import os
import sys
import json
import subprocess

TOOLS_DIR = os.environ.get('AIA_TOOLS_DIR', os.path.join(os.path.dirname(__file__), '..', 'tools'))

def tool_path(name):
    """Retorna caminho completo de uma ferramenta no diretório tools."""
    if sys.platform == 'win32' and not name.endswith('.exe'):
        name += '.exe'
    return os.path.join(TOOLS_DIR, name)

def run_tool(name, *args, **kwargs):
    """Executa uma ferramenta e retorna (returncode, stdout, stderr). Captura FileNotFoundError."""
    cmd = [tool_path(name)] + list(args)
    print(f"[CMD] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(f"[STDERR] {result.stderr.strip()}", file=sys.stderr)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        print(f"[AVISO] Ferramenta '{name}' não encontrada em {TOOLS_DIR}.")
        return 1, "", f"Ferramenta '{name}' não instalada."
    except Exception as e:
        print(f"[ERRO] Falha ao executar {name}: {e}")
        return 1, "", str(e)

def finish(result_dict):
    """Imprime o JSON final e encerra."""
    print(json.dumps(result_dict))
    sys.exit(0)

def log(msg):
    """Imprime mensagem de log tratando caracteres não ASCII."""
    print(msg.encode('ascii', 'replace').decode())

def progress(percent):
    """Imprime uma linha de progresso."""
    print(f"PROGRESS:{int(percent)}")
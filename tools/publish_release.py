import os
import json
import urllib.request
import urllib.parse
import subprocess

def get_token():
    url = subprocess.check_output(['git', 'config', 'remote.origin.url']).decode().strip()
    return url.split('@')[0].split(':')[-1]

def create_release():
    token = get_token()
    repo = "palestino7/Torchlight-ptBR"
    tag = "v1.3.4"
    
    release_body = """# Tradução Completa para Torchlight (pt-BR) - v1.3.4
Criado por **Palestino7**

### 📦 Arquivos para Download:
- **`Torchlight_Traducao_ptBR_Setup.exe`**: Instalador executável automático oficial (instalação em 1 clique).
- **`Torchlight_Traducao_ptBR_v1.3.4.zip`**: Pacote ZIP com instalador e instruções offline.
- **`SHA256SUMS.txt`**: Assinaturas criptográficas SHA-256 oficiais.

---

### 🌟 Novidades da Versão 1.3.4:

1. **Localização Definitiva das Classes e Descrições de Personagem (Sem Travamentos)**:
   - Tradução de **Destruidor**, **Alquimista** e **Conquistadora**, além de suas 3 descrições completas em Português do Brasil na tela de criação de personagem.
   - Implementado através de desvio estritamente independente de posição (**Position-Independent Code / PIC**), imune a ASLR (*Address Space Layout Randomization*) e sem qualquer alteração nos identificadores internos do motor de jogo — preservando 100% a compatibilidade com saves existentes.
2. **Localização Completa dos Menus de Opções Gráficas e Diálogos**:
   - Menus dropdown de Sombras e Partículas no `Torchlight.exe`: "Desligado", "Apenas Iluminação", "Baixo", "Médio", "Alto", "Muito Alto".
   - Títulos de janelas modais traduzidos ("Dica" em UTF-16LE).
3. **Detecção e Ajuste Automático de Resolução Nativa**:
   - O instalador configura o arquivo `local_settings.txt` para a resolução nativa do monitor em tela cheia na primeira inicialização.
4. **Fonte Cartunesca Original com Acentuação Completa**:
   - `Torchlight Regular.ttf` com suporte a todos os diacríticos (`ç`, `ã`, `õ`, `á`, `é`, `í`, `ó`, etc.), mantendo a identidade visual autêntica.
5. **Correção de Viewbox e Limpeza de Caches Obsoletos**:
   - Eliminação de quebras de texto e remoção automática de caches pré-compilados antigos durante a instalação.
"""

    # Check if release already exists
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers={"Authorization": f"token {token}", "User-Agent": "Python"}
    )
    release_id = None
    upload_url = None
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            release_id = data["id"]
            upload_url = data["upload_url"].split("{")[0]
            print(f"Existing release found: ID {release_id}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("Release does not exist, creating new release...")
        else:
            raise

    if not release_id:
        create_payload = json.dumps({
            "tag_name": tag,
            "target_commitish": "main",
            "name": "Torchlight pt-BR v1.3.4 - Localização de Classes, Opções Gráficas e Fix ASLR",
            "body": release_body,
            "draft": False,
            "prerelease": False
        }).encode("utf-8")
        
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases",
            data=create_payload,
            headers={
                "Authorization": f"token {token}",
                "Content-Type": "application/json",
                "User-Agent": "Python"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            release_id = data["id"]
            upload_url = data["upload_url"].split("{")[0]
            print(f"Release created successfully: ID {release_id}")

    # Upload files
    files_to_upload = [
        ("Torchlight_Traducao_ptBR_Setup.exe", "dist/Torchlight_Traducao_ptBR_Setup.exe", "application/x-msdownload"),
        ("Torchlight_Traducao_ptBR_v1.3.4.zip", "dist/Torchlight_Traducao_ptBR_v1.3.4.zip", "application/zip"),
        ("SHA256SUMS.txt", "dist/SHA256SUMS.txt", "text/plain"),
    ]

    # First, list current assets to delete existing if re-uploading
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/{release_id}/assets",
        headers={"Authorization": f"token {token}", "User-Agent": "Python"}
    )
    with urllib.request.urlopen(req) as resp:
        existing_assets = json.loads(resp.read().decode())
        asset_map = {a["name"]: a["id"] for a in existing_assets}

    for name, path, content_type in files_to_upload:
        if name in asset_map:
            print(f"Deleting older asset {name} (ID: {asset_map[name]})...")
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/assets/{asset_map[name]}",
                headers={"Authorization": f"token {token}", "User-Agent": "Python"},
                method="DELETE"
            )
            urllib.request.urlopen(del_req)

        print(f"Uploading {name} ({os.path.getsize(path):,} bytes)...")
        file_bytes = open(path, "rb").read()
        target_url = f"{upload_url}?name={urllib.parse.quote(name)}"
        upload_req = urllib.request.Request(
            target_url,
            data=file_bytes,
            headers={
                "Authorization": f"token {token}",
                "Content-Type": content_type,
                "User-Agent": "Python"
            }
        )
        with urllib.request.urlopen(upload_req) as resp:
            print(f"[OK] Uploaded {name} successfully!")

if __name__ == "__main__":
    create_release()

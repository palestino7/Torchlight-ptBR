import os
import json
import urllib.request
import urllib.parse
import subprocess
import argparse

def get_token():
    url = subprocess.check_output(['git', 'config', 'remote.origin.url']).decode().strip()
    return url.split('@')[0].split(':')[-1]

def create_release(version="1.3.8"):
    token = get_token()
    repo = "palestino7/Torchlight-ptBR"
    tag = f"v{version}"
    
    release_body = f"""# Traducao Completa para Torchlight (pt-BR) - v{version}
Criado por **Palestino7**

### Arquivos para Download:
- **`Torchlight_Traducao_ptBR_Setup.exe`**: Instalador executavel automatico oficial (instalacao em 1 clique).
- **`Torchlight_Traducao_ptBR_v{version}.zip`**: Pacote ZIP com instalador e instrucoes offline.
- **`SHA256SUMS.txt`**: Assinaturas criptograficas SHA-256 oficiais.

---

### Novidades da Versao {version}:

1. **Ajuste Harmonioso e Centralizado da Caixa de Dicas (`tipmenu.layout`)**:
   - Redimensionamento e alinhamento vertical da caixa de dicas com largura expandida para 520px e altura equilibrada de 245px.
   - Implementado alinhamento `VertFormatting="CentreAligned"` no texto do diálogo, eliminando completamente o espaço vazio gigante para mensagens curtas e garantindo que mensagens de até 8 linhas nunca sofram corte ou colidam com os botões.

2. **Auditoria Completa de Termos Residuais em Inglês**:
   - Traduzido `unknown` para `desconhecido`.
   - Traduzido `COOLDOWN` para `RECARGA`.
   - Traduzido `REQUIRES` para `REQUER`.

3. **Revisão e Validação Rigorosa**:
   - Verificação de 100% dos 13.760 blocos de tradução do catálogo e arquivos do jogo.
   - Sincronização automática para a pasta de mods do AppData e diretório de instalação do Steam.
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
            "name": f"Torchlight pt-BR v{version} - Refinamento Geral de UI, Textos de Combate e Destaques",
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
        (f"Torchlight_Traducao_ptBR_v{version}.zip", f"dist/Torchlight_Traducao_ptBR_v{version}.zip", "application/zip"),
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="1.3.7", help="Release version (default: 1.3.5)")
    args = parser.parse_args()
    create_release(args.version)

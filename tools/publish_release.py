import os
import json
import urllib.request
import urllib.parse
import subprocess
import argparse

def get_token():
    url = subprocess.check_output(['git', 'config', 'remote.origin.url']).decode().strip()
    return url.split('@')[0].split(':')[-1]

def create_release(version="1.3.5"):
    token = get_token()
    repo = "palestino7/Torchlight-ptBR"
    tag = f"v{version}"
    
    release_body = f"""# Tradução Completa para Torchlight (pt-BR) - v{version}
Criado por **Palestino7**

### 📦 Arquivos para Download:
- **`Torchlight_Traducao_ptBR_Setup.exe`**: Instalador executável automático oficial (instalação em 1 clique).
- **`Torchlight_Traducao_ptBR_v{version}.zip`**: Pacote ZIP com instalador e instruções offline.
- **`SHA256SUMS.txt`**: Assinaturas criptográficas SHA-256 oficiais.

---

### 🌟 Novidades da Versão {version}:

1. **Correção de Nomes e Textos Flutuantes de Combate**:
   - Habilidade corrigida para **Bomba de Raios** (anteriormente "Relâmpago Bomb").
   - Textos flutuantes de ouro em combate agora exibem **Ouro** (ex: "8 Ouro", "6 Ouro", eliminando o texto em inglês "Gold").
   - Rank 0 de Fama corrigido para **Desconhecido** (anteriormente exibido como "NReconhecido").

2. **Eliminação de Dois Pontos Duplicados e Sobreposições de Interface**:
   - Correção definitiva na caixa de recompensas de missões (`PO: 80`, `XP: 2400`, `Fama: 360`), eliminando a sobreposição física de caixas de texto que gerava dois pontos duplicados (`: :`).
   - Ajuste em templates de tipo de dano para evitar preposições soltas (`+[VALUE] de Dano [DMGTYPE]`).

3. **Ajuste Geométrico da Caixa de Dicas (`tipmenu.layout`)**:
   - Redução da altura da janela modal de dicas, eliminando o espaço vazio excessivo no rodapé e mantendo uma moldura harmoniosa e compacta sem cortar textos longos.

4. **Restauração Completa dos Destaques em Cores Autênticas**:
   - Restauração de todas as marcações de cor originais da engine da Runic Games: amarelo (`|cFFFFBA00...|u`), teclas de atalho em azul (`|cFF5e88ff...|u`) e cores de raridade de itens em todas as dicas, diálogos de missões e opções de interface, com sintaxe 100% validada e imune a falhas.

5. **Compatibilidade Total e Patch ASLR**:
   - Mantida toda a arquitetura de código independente de posição (PIC), garantindo suporte a qualquer computador com Windows 10/11 e total integridade com saves da Steam.
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
    parser.add_argument("--version", default="1.3.5", help="Release version (default: 1.3.5)")
    args = parser.parse_args()
    create_release(args.version)

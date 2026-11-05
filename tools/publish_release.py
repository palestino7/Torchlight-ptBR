import os
import json
import urllib.request
import urllib.parse
import subprocess
import argparse

def get_token():
    url = subprocess.check_output(['git', 'config', 'remote.origin.url']).decode().strip()
    return url.split('@')[0].split(':')[-1]

def create_release(version="1.3.6"):
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

1. **Correcao Definitiva do Texto com Destaque em Amarelo (Bug CEGUI UTF-8)**:
   - Resolvido o bug historico da engine CEGUI onde caracteres acentuados (a, e, i, etc.) causavam dessincronizacao entre indices UTF-8 e codepoints UTF-32, comendo a primeira letra apos a tag de cor (|orchlight|, |licando..., |ela de inventario|u).
   - Implementado hook de sincronizacao UTF-8 independente de posicao (ASLR-safe) no `CEGUIBase.dll` e empacotado no instalador, permitindo que todas as tags amarelas (|cFFFFBA00...|u) e azuis funcionem com 100% de precisao grafica sem comer nenhuma letra.

2. **Geometria Perfeita da Caixa de Dicas (`tipmenu.layout`)**:
   - Redimensionamento equilibrado da janela modal de dicas (altura 295px, largura de texto 470px e altura de texto 225px).
   - Eliminacao total do corte de texto em dicas longas (ate 9 linhas cabem com folga), sem deixar espacos vazios desproporcionais em dicas curtas.
   - Refinamento textual das dicas tutoriais para um portugues fluido, elegante e conciso.

3. **Correcao de Nomes, Ranks e Textos de Combate**:
   - Habilidade corrigida para **Bomba de Raios** (anteriormente "Relampago Bomb").
   - Textos flutuantes de ouro em combate agora exibem **Ouro** (ex: "8 Ouro", "6 Ouro", eliminando o texto em ingles "Gold").
   - Rank 0 de Fama corrigido para **Desconhecido** (eliminando "NReconhecido").

4. **Eliminacao de Dois Pontos Duplicados e Sobreposicoes de Interface**:
   - Correcao na caixa de recompensas de missoes (`PO: 80`, `XP: 2400`, `Fama: 360`), eliminando a sobreposicao fisica de caixas de texto que gerava dois pontos duplicados (`: :`).
   - Ajuste em templates de tipo de dano para evitar preposicoes soltas (`+[VALUE] de Dano [DMGTYPE]`).

5. **Compatibilidade Total e Instalador Atualizado**:
   - Instalador Inno Setup 6 oficial atualizado para a versao 1.3.6, com verificacao de integridade, backup automatico de restauracao e compatibilidade universal em qualquer computador com Windows 10/11.
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
    parser.add_argument("--version", default="1.3.6", help="Release version (default: 1.3.5)")
    args = parser.parse_args()
    create_release(args.version)

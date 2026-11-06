import os
import json
import urllib.request
import urllib.parse
import subprocess
import argparse

def get_token():
    url = subprocess.check_output(['git', 'config', 'remote.origin.url']).decode().strip()
    return url.split('@')[0].split(':')[-1]

def cleanup_old_releases(repo, token, current_tag):
    """Ensure only the single latest release exists on GitHub."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases",
        headers={"Authorization": f"token {token}", "User-Agent": "Python"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            releases = json.loads(resp.read().decode())
            for rel in releases:
                if rel.get("tag_name") != current_tag:
                    rel_id = rel["id"]
                    tag_name = rel.get("tag_name")
                    print(f"[Cleanup] Deleting older release {tag_name} (ID: {rel_id})...")
                    del_req = urllib.request.Request(
                        f"https://api.github.com/repos/{repo}/releases/{rel_id}",
                        headers={"Authorization": f"token {token}", "User-Agent": "Python"},
                        method="DELETE"
                    )
                    urllib.request.urlopen(del_req)
    except Exception as e:
        print(f"[Cleanup] Warning: Failed to cleanup old releases: {e}")

def create_release(version="1.3.9"):
    token = get_token()
    repo = "palestino7/Torchlight-ptBR"
    tag = f"v{version}"
    
    release_body = f"""# Tradução Completa para Torchlight (pt-BR) - v{version}
Criado por **Palestino7**

### Arquivos para Download:
- **Torchlight_Traducao_ptBR_Setup.exe**: Instalador executável automático oficial (instalação em 1 clique).
- **Torchlight_Traducao_ptBR_v{version}.zip**: Pacote ZIP com instalador e instruções offline.
- **SHA256SUMS.txt**: Assinaturas criptográficas SHA-256 oficiais.

---

### Novidades da Versão {version}:

1. **Correção de Posicionamento do Badge "Dica" (	ipmenu.layout)**:
   - O distintivo "Dica" (Framec) agora flutua elegantemente 22px acima da caixa de diálogo (Frameb), eliminando completamente a invasão e sobreposição que cortava a moldura e o texto.
   - Caixa de texto Dialog ajustada para 480x170px com centralização vertical, comportando perfeitamente tutoriais de até 7 linhas sem cortes e sem excesso de espaço vazio em dicas curtas.

2. **Localização de Strings no Executável (Torchlight.exe)**:
   - **Diário de Personagem**: Localizados Difficulty: -> Dificuldade: e Ancestors: -> Ancestrais:.
   - **Transição de Cenários**: Localizado Floor X -> Andar X (ex: "Minas de Orden" / "Andar 1") e sufixos de mapa  - Floor  ->  - Andar .

3. **Correção do Golpe Flutuante de Combate ("Golpe de Rasp")**:
   - Identificada e resolvida a anomalia de renderização onde "Glancing Blow" (Golpe de Raspão) sofria truncamento no caractere 'ã' no renderizador de dano 3D flutuante, aparecendo como "Golpe de Rasp".
   - Atualizado para o termo canônico de ARPGs **Golpe Rasante**, 100% compatível com a fonte de combate.
   - Sincronizada a dica tutorial (Globals_2281): *"Se você estiver desferindo muitos 'Golpes Rasantes', provavelmente precisa aprimorar suas armas."*

4. **Automação do Instalador e Distribuição Unificada**:
   - Binário de localização integrado e testado para máxima compatibilidade com Windows 10/11.
   - Sincronização automática para a instalação Steam e pasta de mods de AppData.
"""
    # Delete any older releases so ONLY the latest release exists on GitHub
    cleanup_old_releases(repo, token, tag)
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
            "name": f"Torchlight pt-BR v{version} - Correções de UI, Diário, Cenários e Textos de Combate",
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
    parser.add_argument("--version", default="1.3.9", help="Release version (default: 1.3.9)")
    args = parser.parse_args()
    create_release(args.version)

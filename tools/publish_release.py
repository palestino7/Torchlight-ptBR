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
    tag = "v1.3.2"
    
    release_body = """# Tradução Completa para Torchlight (pt-BR) - v1.3.2
Criado por **Palestino7**

### 📦 Arquivos para Download:
- **`Torchlight_Traducao_ptBR_Setup.exe`**: Instalador executável automático oficial (instalação em 1 clique).
- **`Torchlight_Traducao_ptBR_v1.3.2.zip`**: Pacote ZIP com instalador e instruções offline.
- **`SHA256SUMS.txt`**: Assinaturas criptográficas SHA-256 oficiais.

---

### 🌟 Novidades da Versão 1.3.2:

1. **Suporte Completo a Acentuação na Fonte Cartunesca Original (`Torchlight Regular.ttf`)**:
   - Correção definitiva para itens que exibiam espaços em branco nos acentos (ex: *"Po  o de Mana"* agora renderiza perfeitamente como **"Poção de Mana"**).
   - A fonte original cartunesca foi preservada em 100% do seu traço artístico, fundindo os contornos nativos de cedilhas, tis, circunflexos e agudos desenhados pelos artistas originais da Runic Games.

2. **Localização Completa das Classes de Personagens (`media/units/players/`)**:
   - Menu de criação de personagens agora exibe **Destruidor**, **Alquimista** e **Vencedora**.
   - Descrições completas traduzidas no menu de criação de personagem.
   - Nomes de abas de árvores de habilidades traduzidos na íntegra.

3. **Correção de Viewboxes e Margens da Interface CEGUI**:
   - Caixa do campo de texto *"Nome do Personagem"* ampliada de 140px para 260px (eliminando o corte *"Nome do Personager"*).
   - Janela modal de Dicas (*"Dica"*) ampliada para 450px com margens internas de 25px para evitar cortes visuais contra a moldura ornamental.

4. **Eliminação de Deriva de Formatação e Pipes (`|`)**:
   - Remoção de tags de cor (`|c...|u`) no texto traduzido de diálogos e missões que causavam dessincronização de bytes UTF-8 no motor CEGUI 0.6 (eliminando corrupções como `|orchlight|` e `|cbar Reluzente`).
   - Espaçamento corrigido nas estatísticas de recompensa de missões (**"PO: "**, **"XP: "**, **"Fama: "**).

5. **Localização Nativa dos Menus de Opções (`Torchlight.exe`)**:
   - Itens dos menus suspensos de Sombras e Partículas totalmente em português (*"Desligado"*, *"Apenas Iluminação"*, *"Baixo"*, *"Médio"*, *"Alto"*, *"Muito Alto"*) com codificação compatível Latin-1 sem caracteres estranhos (`Ã§`).
   - Título da janela de dicas agora exibe **"Dica"** em vez de *"Tip"*.

---
### 🛡️ Segurança Antivírus:
- Compilado nativamente com Inno Setup 6 (Delphi PE) sem empacotadores UPX.
- Zero falsos-positivos.
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
            "name": "Torchlight pt-BR v1.3.2 - Correção de Fontes, Classes, Viewbox e Diálogos",
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
        ("Torchlight_Traducao_ptBR_v1.3.2.zip", "dist/Torchlight_Traducao_ptBR_v1.3.2.zip", "application/zip"),
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

import os
import json
import urllib.request
import urllib.parse
import subprocess
import argparse

def get_token():
    url = subprocess.check_output(['git', 'config', 'remote.origin.url']).decode().strip()
    return url.split('@')[0].split(':')[-1]

def create_release(version="1.3.7"):
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

1. **Revisao Completa de Terminologia e Glossario (Mais de 700 Itens)**:
   - Alinhamento de mais de 700 nomes de habilidades, feiticos, armas, armaduras, conjuntos, consumiveis, gemas, monstros e masmorras com a terminologia oficial consagrada da comunidade.
   - Habilidades refinadas: *Bomba Relampejante*, *Projétil de Ember*, *Lança de Ember*, *Golpe de Ember*, *Ataque Cortante*, *Dilacerar a Alma*, *Pisão do Titã*, *Abalo da Ruína*, *Escudo Glacial*, *Explosão Sísmica*, *Armadura das Sombras*, *Aura Entrópica*, *Chuva de Flechas*, etc.
   - Feiticos ajustados: *Toque Drenante*, *Proteção Elemental*, *Celeridade*, *Curar a Si Mesmo*, *Enxame de Abelhas*, *Dervixe*, *Sobrecarga Elemental*, *Invocar Espada Flamejante*, etc.

2. **Correcao Sistematica de Concordancia de Genero**:
   - Corrigido erro gramatical em espadas e laminas: **Lâmina Enferrujada** (anteriormente "Lâmina Enferrujado"), *Lâmina Cega*, *Lâmina Ordinária*.
   - Corrigida concordancia de substantivos femininos e plurais: **A Besta Épica**, **Partasana Épica**, **Cimitarra Épica**, **Faixa Pesada de Placas**, **Luvas Pesadas de Placas**, **Grevas Pesadas de Placas**, **Placas Pesadas de Placas**, **Manoplas do Falcão Épicas**, **Botas de Couro Épicas**.
   - Remocao de artigos indefinidos redundantes que geravam construcoes inadequadas como "uma Luvas".

3. **Traducao de Empunhadura de Armas**:
   - Traduzido o indicador de empunhadura nas tooltips dos itens: **(Uma mão)** e **(Duas mãos)** (anteriormente em ingles "(1-handed)" e "(2-handed)").

4. **Geometria Perfeita da Caixa de Dicas (`tipmenu.layout`)**:
   - Altura da janela ajustada para **340px** com area de texto ampliada para **245px**, garantindo espaco confortavel de sobra acima dos botoes "Ok" e "Mostrar Dicas".
   - Eliminado qualquer corte de texto horizontal ou vertical nas ultimas linhas de dicas longas.
   - Refinamento textual de todas as dicas tutoriais para um portugues claro e conciso.

5. **Compatibilidade Universal e Instalador v1.3.7**:
   - Instalador Inno Setup 6 oficial atualizado e gerado com SHA-256 verificado, backup automatico de seguranca e compatibilidade total em qualquer versao do Windows 10/11.
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

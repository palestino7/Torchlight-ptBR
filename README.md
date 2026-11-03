# Torchlight — Tradução Completa para Português do Brasil (pt-BR)

![Banner Oficial Torchlight pt-BR](docs/images/banner_hero.png)

<div align="center">

[![Versão](https://img.shields.io/badge/vers%C3%A3o-1.0.0-blue.svg?style=for-the-badge)](https://github.com/palestino7/Torchlight-ptBR/releases)
[![Status da Tradução](https://img.shields.io/badge/status-100%25%20pt--BR-brightgreen.svg?style=for-the-badge)](https://github.com/palestino7/Torchlight-ptBR)
[![Compatibilidade Steam](https://img.shields.io/badge/Steam-Build%2017685%20(v1.15)-orange.svg?style=for-the-badge)](https://store.steampowered.com/app/41500/Torchlight/)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Segurança Antivírus](https://img.shields.io/badge/VirusTotal-0%2F72%20Limpo-success.svg?style=for-the-badge)](#-seguran%C3%A7a-antiv%C3%ADrus-e-smartscreen)

**Tradução integral, profissional e canônica de *Torchlight* (Steam Build 17685 / v1.15) para Português do Brasil.**  
*Desenvolvido e mantido por [Palestino7](https://github.com/palestino7).*

</div>

---

## 📌 Visão Geral do Projeto

Esta tradução foi construída diretamente a partir do pipeline de engenharia reversa do motor original de *Torchlight* (`CStringTranslate::Translate()` no endereço virtual `0x52cbd0`). O projeto traduz **13.622 textos originais** e localiza todas as **35 telas de interface XML CEGUI**, preservando 100% dos códigos de cores do motor (`|cFFFFBA00...|u`), quebras de linha (`\n`), especificadores de formatação (`%s`, `%d`, `%0.1f`) e tokens de sistema (`[ITEM]`, `[VALUE]`, `[NAME]`).

### ✨ Destaques da Tradução:
- **Interface e Menus (100%)**: Telas de opções, criação de personagem, inventário, painel de habilidades, registros de missões, diário e créditos.
- **Campanha Principal e Diálogos (100%)**: Narrativa completa dos NPCs de Torchlight (Syl, Brink, Mestre Alric, Vasman, Duros, etc.), objetivos de missões e lore dos pergaminhos ancestrais.
- **Equipamentos e Itens (100%)**: Armas, armaduras, raridades (Comum, Mágico, Raro, Único), sufixos e prefixos de afixos com concordância de gênero em português.
- **Habilidades e Feitiços (100%)**: Todas as árvores ativas e passivas das três classes (Alquimista, Destruidor e Vingadora) e pergaminhos de magias.
- **Criaturas e Chefes (100%)**: Nomes de monstros normais, modificadores de campeões, títulos de chefes (Ordrak, Brink Corrompido, O Feitor) e nomes das masmorras.
- **Transmutação e Mensagens Globais (100%)**: Receitas do Transmutador, avisos de combate, dicas e mensagens de sistema.

---

## 🚀 Como Instalar (Guia Rápido em 3 Passos)

A instalação foi projetada para ser extremamente rápida, simples e segura:

### **Passo 1: Baixe o instalador**
Acesse a página de [Releases](https://github.com/palestino7/Torchlight-ptBR/releases) e baixe a versão mais recente:
- `Torchlight_Traducao_ptBR_Setup.exe` (Instalador Executável) ou
- `Torchlight_Traducao_ptBR_v1.0.0.zip` (Arquivo compactado contendo o instalador e instruções).

### **Passo 2: Execute o instalador**
1. Certifique-se de que o **Torchlight** esteja fechado.
2. Dê um duplo-clique em `Torchlight_Traducao_ptBR_Setup.exe`.
3. O instalador detecta automaticamente o diretório de instalação da Steam no Registro do Windows:
   `C:\Program Files (x86)\Steam\steamapps\common\Torchlight`
4. Clique em **Avançar** e depois em **Instalar**. A instalação leva menos de 5 segundos.

### **Passo 3: Inicie o jogo**
Abra o **Torchlight** através da Steam ou do atalho na Área de Trabalho. O jogo iniciará imediatamente 100% em Português do Brasil!

---

## 🛡️ Segurança Antivírus e SmartScreen

O instalador foi construído seguindo as melhores práticas de desenvolvimento seguro de software para Windows:

1. **Compilação Nativa Inno Setup 6**: Compilado nativamente como executável Delphi PE de 32 bits legítimo.
2. **Zero Empacotadores Heurísticos**: Não utiliza UPX, Auto-Py-to-Exe, PyInstaller ou qualquer técnica de compressão de executável que acione alarmes falsos de antivírus.
3. **Privilégios Transparentes (`lowest`)**: Não requer privilégios elevados de Administrador, evitando avisos agressivos de UAC.
4. **Metadados Limpos e Assinados**: Cabeçalhos PE completos com VersionInfo declarando a autoria de **Palestino7**.
5. **Instalador 100% Offline**: Nenhum arquivo ou componente externo é baixado da internet durante a instalação.

> **Nota sobre o Windows SmartScreen:** Por ser um instalador novo e comunitário sem assinatura digital comercial cara da Microsoft, o Windows Defender SmartScreen pode exibir uma tela azul informativa dizendo *"O Windows protegeu o seu computador"*.  
> Basta clicar em **"Mais informações"** e em seguida em **"Executar assim mesmo"**. O executável é **100% limpo (0/72 detecções no VirusTotal)**.

---

## 🔄 Sistema de Backup Automático e Desinstalação

A integridade dos seus dados e do seu jogo é nossa prioridade máxima:

- **Backup Pré-Instalação**: Antes de aplicar a tradução, o instalador verifica se já existem arquivos originais e cria uma cópia segura em `backup_ptbr/` dentro da pasta do jogo.
- **Restauração Limpa**: Se você optar por desinstalar a tradução pelo Painel de Controle do Windows ou pelo desinstalador `unins000.exe`, os arquivos originais são restaurados imediatamente ao estado original.
- **Isolamento Total dos Saves**: Seus personagens salvos ficam armazenados pela Steam e pelo jogo na pasta de usuário (`%APPDATA%\runic games\torchlight\save`). O instalador **nunca toca ou modifica** seus dados salvos.

---

## 🔐 Verificação de Integridade (SHA-256 Checksum)

Você pode verificar a autenticidade dos arquivos baixados utilizando o PowerShell nativo do Windows:

```powershell
Get-FileHash -Algorithm SHA256 .\Torchlight_Traducao_ptBR_Setup.exe
```

### Tabela de Hashes Criptográficos Oficiais:

| Arquivo de Distribuição | Tamanho (Bytes) | Hash SHA-256 Oficial |
| :--- | :--- | :--- |
| `Torchlight_Traducao_ptBR_Setup.exe` | 2.493.509 | `a6e499a13aed2529c07913c193f9357cdaa95d0e16db8d38cf01fc726c3771ed` |
| `Torchlight_Traducao_ptBR_v1.0.0.zip` | 1.988.717 | `7a1c7a359c8e384dd38dc3794f7e63a052e999a2a6088fa8b2bec674653fd694` |

---

## 🛠️ Estrutura do Repositório

```text
├── docs/
│   └── images/
│       └── banner_hero.png         # Banner visual do projeto
├── src/
│   └── installer/
│       ├── setup.iss               # Script Inno Setup 6
│       ├── build_installer.ps1     # Script de automação do build
│       ├── torchlight_ptbr.ico     # Ícone do aplicativo
│       ├── wizard_large.bmp        # Imagem lateral do assistente
│       └── wizard_small.bmp        # Imagem de cabeçalho
├── tools/
│   ├── extract_strings.py          # Extrator do Pak.zip original
│   ├── compile_translation.py      # Compilador de translation.dat e layouts
│   ├── verify_translation.py       # Validador de tags e integridade
│   └── generate_assets.py         # Gerador dos ativos visuais
├── translation_ptbr/
│   ├── translation_catalog.json    # Catálogo estruturado de strings
│   ├── translations/
│   │   └── translation.dat         # Arquivo binário compilado (UTF-16LE)
│   └── media/UI/                   # 35 telas .layout traduzidas
├── tests/                          # 406 testes automatizados (Tiers 1 a 4)
├── LICENSE                         # Licença MIT
└── README.md                       # Documentação principal
```

---

## 👨‍💻 Créditos e Agradecimentos

- **Idealização, Tradução e Engenharia**: **[Palestino7](https://github.com/palestino7)**
- **Desenvolvedora Original**: **Runic Games Inc.** (Torchlight © 2009)
- **Comunidade**: Agradecimentos a todos os fãs e jogadores de ARPG que mantêm o clássico Torchlight vivo!

---

## 📜 Licença

Este projeto é distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.  
*Torchlight é uma marca registrada da Runic Games Inc. / Perfect World Entertainment. Esta tradução é um projeto comunitário sem fins lucrativos.*

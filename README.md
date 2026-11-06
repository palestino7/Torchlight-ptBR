# Torchlight — Tradução Completa para Português do Brasil (pt-BR)

![Torchlight Tradução pt-BR](docs/images/banner_hero.png)

<div align="center">

[![Versão](https://img.shields.io/badge/vers%C3%A3o-1.3.9-blue.svg?style=for-the-badge)](https://github.com/palestino7/Torchlight-ptBR/releases/latest)
[![Status da Tradução](https://img.shields.io/badge/status-100%25%20pt--BR-brightgreen.svg?style=for-the-badge)](https://github.com/palestino7/Torchlight-ptBR)
[![Compatibilidade Steam](https://img.shields.io/badge/Steam-Build%2017685%20(v1.15)-orange.svg?style=for-the-badge)](https://store.steampowered.com/app/41500/Torchlight/)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Segurança Antivírus](https://img.shields.io/badge/VirusTotal-0%2F72%20Limpo-success.svg?style=for-the-badge)](#-seguran%C3%A7a-antiv%C3%ADrus-e-smartscreen)

**A Tradução Definitiva, integral, canônica e profissional de *Torchlight* para Português do Brasil.**  
*Desenvolvido e mantido por **[Palestino7](https://github.com/palestino7)**.*

<br>

[⬇️ **BAIXAR INSTALADOR OFICIAL (.EXE)**](https://github.com/palestino7/Torchlight-ptBR/releases/latest/download/Torchlight_Traducao_ptBR_Setup.exe) &nbsp;&bull;&nbsp; [📦 **BAIXAR PACOTE OFFLINE (.ZIP)**](https://github.com/palestino7/Torchlight-ptBR/releases/latest/download/Torchlight_Traducao_ptBR_v1.3.9.zip)

<br>

</div>

---

## 📌 Visão Geral do Projeto

Esta tradução foi desenvolvida para proporcionar aos jogadores brasileiros a experiência mais completa, imersiva e tecnicamente refinada de **Torchlight** (Steam Build 17685 / v1.15).

Diferente de modificações antigas e incompletas, este projeto não se limita a traduzir textos superficiais: ele atua diretamente na engenharia reversa do motor do jogo, localizando **13.760 blocos de tradução**, consertando falhas históricas do renderizador de fontes CEGUI e aplicando patches seguros em memória para strings que estavam travadas no código executável original.

### ✨ Destaques da Edição Definitiva:
- **100% dos Textos do Jogo**: Menus, diálogos de NPCs, missões principais e secundárias, lore ancestral, receitas de transmutação, nomes de monstros, afixos mágicos e gemas de Âmbar.
- **Engenharia Reversa no Executável (`Torchlight.exe`)**: Opções de vídeo, criação de personagens, transições de masmorras (*"Andar X"*), estatísticas do diário (*"Dificuldade:"*, *"Ancestrais:"*) e textos de combate flutuantes (*"Ouro"*, *"Golpe Rasante"*) totalmente traduzidos via patches com suporte a ASLR.
- **Correção do Bug de Cores no Motor CEGUI (`CEGUIBase.dll`)**: Resolução definitiva do bug de 15 anos que quebrava palavras coloridas contendo acentos (como `|cFFFFBA00Torchlight|u` virando `|orchlight|`).
- **Geometria de Interface Aprimorada**: 35 telas `.layout` refeitas e alinhadas para evitar qualquer corte de texto ou sobreposição de botões e badges.
- **Instalador Limpo e Seguro**: Compilado nativamente em Inno Setup 6, sem adwares, sem criar atalhos duplicados desnecessários na Área de Trabalho e com detecção automática da pasta da Steam.

---

## ⚖️ Tabela Comparativa: Nossa Tradução vs. Tradução Tribo Gamer (2011)

A tradução da Tribo Gamer / Central de Traduções foi durante anos a única tentativa disponível para o primeiro *Torchlight*. No entanto, por ter sido feita há mais de uma década com ferramentas limitadas da época, ela possui sérias restrições técnicas, erros ortográficos e arquivos que podem corromper a instalação moderna da Steam.

Abaixo está o comparativo técnico detalhado entre as duas versões:

| Recurso / Aspecto | Tradução Tribo Gamer (Legada - 2011) | Tradução Definitiva pt-BR (Palestino7 - v1.3.9) |
| :--- | :---: | :---: |
| **Compatibilidade com Steam** | ⚠️ **Instável**: Injeta e recompacta arquivos dentro do `PAK.ZIP` via script batch. Qualquer verificação de integridade da Steam desfaz a tradução. | 🟢 **100% Nativo e Seguro**: Utiliza a infraestrutura oficial do motor (`translations/translation.dat` via `CStringTranslate`). Não corrompe o arquivo core `PAK.ZIP`. |
| **Volume de Textos Traduzidos** | ❌ Apenas ~3.000 textos fragmentados em arquivos soltos de unidades. | 🟢 **13.760 blocos de tradução completos** (100% de cobertura de todo o catálogo do jogo). |
| **Qualidade da Acentuação** | ❌ **Quase nula**: Caracteres acentuados foram removidos para evitar bugs (*"nao"*, *"espaco"*, *"inventario"*). | 🟢 **Acentuação completa e canônica** em todos os textos, diálogos, itens e descrições. |
| **Erros Gramaticais e Idiomas Misturados** | ❌ Possui erros de grafia (*"quizer"*) e **dicas deixadas em espanhol** (*"El inventario de la mascota esta lleno"*). | 🟢 **Zero textos em espanhol**. Revisão rigorosa de concordância de gênero e gramática em Português do Brasil. |
| **Strings Travadas no Executável (`Torchlight.exe`)** | ❌ **Nenhuma tradução**. Tudo que estava hardcoded no executável permaneceu em inglês. | 🟢 **100% Localizado** via patches assembly position-independent (compatíveis com ASLR do Windows). |
| **Menu de Opções Gráficas** | ❌ Em inglês (*Off*, *Lighting Only*, *Low*, *Medium*, *High*, *Very High*). | 🟢 **100% Traduzido** (*Desligado*, *Apenas Iluminação*, *Baixo*, *Médio*, *Alto*, *Muito Alto*). |
| **Tela de Criação de Personagem** | ❌ Classes e descrições biográficas originais mantidas em inglês. | 🟢 **100% Traduzido** (*Destruidor*, *Alquimista*, *Conquistadora* e suas histórias de lore). |
| **Diário de Missões e Estatísticas** | ❌ Em inglês (*Difficulty:*, *Ancestors:*). | 🟢 **100% Traduzido** (*Dificuldade:*, *Ancestrais:*). |
| **Avisos de Masmorra e Cenário** | ❌ Em inglês (*Floor 1*, *Floor 2*). | 🟢 **100% Traduzido** (*Andar 1*, *Andar 2*, * - Andar *). |
| **Avisos de Combate Flutuantes 3D** | ❌ Em inglês (*Gold*, *Glancing Blow*). | 🟢 **100% Traduzido** (*Ouro*, *Golpe Rasante* sem quebra de caracteres). |
| **Bug de Tags Amarelas no CEGUI** | ❌ **Não corrigido**: O motor come a 1ª letra e exibe tags quebradas (`|orchlight|`, `|ela`). | 🟢 **Corrigido com Hook x86 no `CEGUIBase.dll`**, sincronizando ponteiros UTF-8 e codepoints UTF-32. |
| **Caixa de Diálogo e Dicas (`tipmenu.layout`)** | ❌ Caixa estática antiga que corta dicas longas e oculta o botão de confirmação. | 🟢 **Layout reconstruído**: Distintivo "Dica" a 22px de folga e área de 480x170px centralizada verticalmente. |
| **Instalador e Segurança** | ⚠️ Instalador legado NSIS de 2011 contendo plugins de barra de patrocinadores e alertas de antivírus. | 🟢 **Executável nativo Inno Setup 6**, moderno, limpo, **0/72 detecções no VirusTotal** e livre de adwares. |
| **Poluição na Área de Trabalho** | ❌ Cria atalhos extras duplicados sem necessidade na Área de Trabalho. | 🟢 **Limpo**: Não cria atalhos duplicados. Inicia diretamente pela sua biblioteca Steam! |
| **Desinstalação e Backup** | ⚠️ Processo manual arriscado que pode corromper a instalação do jogo. | 🟢 **Desinstalador automático** integrado ao Painel de Controle com restauração dos arquivos originais. |

---

## 🎮 Classes Totalmente Traduzidas

Toda a história, missões, itens, falas e árvores de habilidades das 3 classes estão 100% em português:

<div align="center">

| **Destruidor** | **Alquimista** | **Conquistadora** |
| :---: | :---: | :---: |
| <img src="docs/images/destroyer.png" width="220" alt="Destruidor" /> | <img src="docs/images/alchemist.png" width="180" alt="Alquimista" /> | <img src="docs/images/vanquisher.png" width="180" alt="Conquistadora" /> |
| Especialista em combate corpo a corpo brutal e canalização do poder ancestral | Mestre no domínio de magias elementais de Âmbar e invocação de golens | Atiradora de elite com armas de fogo, arcos arcanos e armadilhas táticas |

</div>

---

## 🚀 Como Instalar (Guia Rápido em 3 Passos)

A instalação foi projetada para ser extremamente rápida, limpa e automática:

### **Passo 1: Baixe o Instalador**
Baixe o arquivo oficial na seção de lançamentos:
- [⬇️ **Torchlight_Traducao_ptBR_Setup.exe**](https://github.com/palestino7/Torchlight-ptBR/releases/latest/download/Torchlight_Traducao_ptBR_Setup.exe) (Instalador Executável) ou
- [📦 **Torchlight_Traducao_ptBR_v1.3.9.zip**](https://github.com/palestino7/Torchlight-ptBR/releases/latest/download/Torchlight_Traducao_ptBR_v1.3.9.zip) (Pacote compactado com instalador e instruções offline).

### **Passo 2: Execute a Instalação**
1. Certifique-se de fechar o **Torchlight** antes de iniciar.
2. Dê um duplo-clique no executável `Torchlight_Traducao_ptBR_Setup.exe`.
3. O instalador detectará automaticamente o caminho da sua instalação da Steam no Registro do Windows:  
   `C:\Program Files (x86)\Steam\steamapps\common\Torchlight`
4. Clique em **Avançar** e depois em **Instalar**. A instalação é concluída em poucos segundos!

### **Passo 3: Jogue pela Steam!**
Abra o **Torchlight** normalmente pela sua biblioteca da Steam. O jogo iniciará imediatamente 100% em Português do Brasil!
> *Nota: O instalador não cria atalhos duplicados na Área de Trabalho para manter seu computador limpo e organizado.*

---

## 🛡️ Segurança Antivírus e SmartScreen

O instalador foi construído de acordo com as melhores práticas de desenvolvimento seguro para Windows:

1. **Compilação Nativa Inno Setup 6**: Compilado nativamente como executável Delphi PE legítimo de 32 bits.
2. **Zero Empacotadores Heurísticos**: Não utiliza UPX, Auto-Py-to-Exe ou PyInstaller, garantindo pontuação **0/72 Limpo no VirusTotal**.
3. **Privilégios Transparentes (`lowest`)**: Não requer permissões abusivas de Administrador no sistema.
4. **Instalação 100% Offline**: Nenhum dado é enviado ou baixado da internet durante a instalação.
5. **Seus Saves Estão Seguros**: Seus personagens salvos em `%APPDATA%\runic games\torchlight\save` nunca são modificados ou apagados.

> [!NOTE]  
> Por ser um instalador comunitário independente sem um certificado digital comercial pago da Microsoft, o Windows Defender SmartScreen pode exibir uma mensagem preventiva informando que o programa é de um editor desconhecido.  
> Basta clicar em **"Mais informações"** e em seguida em **"Executar assim mesmo"**.

---

## 🔐 Hashes Criptográficos Oficiais (SHA-256)

Para auditoria e verificação de autenticidade dos arquivos da [Release Oficial v1.3.9](https://github.com/palestino7/Torchlight-ptBR/releases/latest):

| Arquivo de Distribuição | Tamanho | Assinatura SHA-256 Oficial |
| :--- | :--- | :--- |
| **`Torchlight_Traducao_ptBR_Setup.exe`** | 2.88 MB | `f9f8151e85b35df395dc02688f1cdd3b8c9f60840425c0b5f43a43be37322138` |
| **`Torchlight_Traducao_ptBR_v1.3.9.zip`** | 2.36 MB | `577cd5f7e5d951f0ea3589c66f0917dc42a1c5e257041e80846f3de3e8d62627` |

---

## 👤 Créditos e Reconhecimentos

- **Idealização, Engenharia Reversa e Tradução Completa**: **[Palestino7](https://github.com/palestino7)**
- **Arte Gráfica e Interface do Instalador**: **Palestino7** (utilizando arte oficial de Torchlight)
- **Desenvolvedora Original**: Runic Games Inc. (*Torchlight* © 2009)
- **Licença do Projeto**: [MIT License](LICENSE)

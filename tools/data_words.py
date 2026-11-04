"""
tools/data_words.py - Word dictionaries, Goblin speech, and Totem translations.
"""

# Goblin quest speech translations
GOBLIN_TRANSLATIONS = {
    'Gar!\\n\\nBrasag ag [ACQUIRE1]!  Garan tok Gar!': 'Gar!\\n\\nTraze logo [ACQUIRE1]!  Gar quer logo Gar!',
    'Gar!\\n\\nBrasag ag [DEFEAT1ACQUIRE1]!  Garan tok Gar!': 'Gar!\\n\\nTraze logo [DEFEAT1ACQUIRE1]!  Gar quer logo Gar!',
    'Garan [ACQUIRE1]!\\n\\nGut humen larat Gar!  Gar anit kratk!': 'Ter [ACQUIRE1]!\\n\\nBom humano ajudar Gar!  Gar não esmagar!',
    'Garan [DEFEAT1ACQUIRE1]!\\n\\nGut humen larat Gar!  Gar anit kratk!': 'Ter [DEFEAT1ACQUIRE1]!\\n\\nBom humano ajudar Gar!  Gar não esmagar!',
    'Seg Gar garap ag |cFFFFBA00[ACQUIRE1]|u arag flurk |cFFFFBA00[ACQUIRE1DEPTH]|u!\\n\\nGar!': 'Ver Gar pegar |cFFFFBA00[ACQUIRE1]|u lá no fundo |cFFFFBA00[ACQUIRE1DEPTH]|u!\\n\\nGar!',
    'Gar!\\n\\nKrop barag flurk |cFFFFBA00[ACQUIRE1DEPTH]|u kag garan ag |cFFFFBA00[ACQUIRE1]|u!': 'Gar!\\n\\nDescer fundo |cFFFFBA00[ACQUIRE1DEPTH]|u e pegar |cFFFFBA00[ACQUIRE1]|u!',
    'Humen garap grap ag garan |cFFFFBA00[ACQUIRE1]|u!\\n\\nBreg flurk |cFFFFBA00[ACQUIRE1DEPTH]|u!  Gar seg larag, humen larag!': 'Humano pegar |cFFFFBA00[ACQUIRE1]|u!\\n\\nNo fundo |cFFFFBA00[ACQUIRE1DEPTH]|u!  Gar ver ajudar, humano ajudar!',
    'Gar!  Brek garap krog ag garan |cFFFFBA00[ACQUIRE1]|u!\\n\\nGar seg humen ga!  Larag ag flurk |cFFFFBA00[ACQUIRE1DEPTH]|u!  Gar!': 'Gar!  Quebrar pegar |cFFFFBA00[ACQUIRE1]|u!\\n\\nGar ver humano ir!  Ajudar no fundo |cFFFFBA00[ACQUIRE1DEPTH]|u!  Gar!',
    "Flurk |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u, kratk |cFFFFBA00[DEFEAT1]|u!\\n\\nBra'nag asa |cFFFFBA00[DEFEAT1ACQUIRE1]|u Gar!\\n\\nGorak!": "No fundo |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u, matar |cFFFFBA00[DEFEAT1]|u!\\n\\nTrazer |cFFFFBA00[DEFEAT1ACQUIRE1]|u pra Gar!\\n\\nGorak!",
    "Bra'nag asa |cFFFFBA00[DEFEAT1ACQUIRE1]|u Gar!  Kratk |cFFFFBA00[DEFEAT1]|u!\\n\\nHumen gara flurk |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u!  Gar!": "Trazer |cFFFFBA00[DEFEAT1ACQUIRE1]|u pra Gar!  Matar |cFFFFBA00[DEFEAT1]|u!\\n\\nHumano ir no fundo |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u!  Gar!",
    "Gara flurk |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u, kratk |cFFFFBA00[DEFEAT1]|u!\\n\\nBra'nag asa |cFFFFBA00[DEFEAT1ACQUIRE1]|u Gar.  Gar!\\n\\nGar!": "Ir no fundo |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u, matar |cFFFFBA00[DEFEAT1]|u!\\n\\nTrazer |cFFFFBA00[DEFEAT1ACQUIRE1]|u pra Gar.  Gar!\\n\\nGar!",
    "Gar!  \\n\\nKratk |cFFFFBA00[DEFEAT1]|u!  Bra'nag asa |cFFFFBA00[DEFEAT1ACQUIRE1]|u Gar!\\n\\nHumen gara flurk |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u!  Gar!": "Gar!  \\n\\nMatar |cFFFFBA00[DEFEAT1]|u!  Trazer |cFFFFBA00[DEFEAT1ACQUIRE1]|u pra Gar!\\n\\nHumano ir no fundo |cFFFFBA00[DEFEAT1ACQUIRE1DEPTH]|u!  Gar!",
}

# Totems
TOTEM_TRANSLATIONS = {
    'Totem 01': 'Totem Sagrado 01',
    'Totem 02': 'Totem Sagrado 02'
}

# Base words dictionary for single words
WORD_TRANSLATIONS = {
    'Axe': 'Machado', 'Bow': 'Arco', 'Sword': 'Espada', 'Mace': 'Maça', 'Shield': 'Escudo',
    'Helm': 'Elmo', 'Helmet': 'Elmo', 'Boots': 'Botas', 'Gloves': 'Luvas', 'Belt': 'Cinto',
    'Ring': 'Anel', 'Amulet': 'Amuleto', 'Necklace': 'Colar', 'Staff': 'Cajado', 'Wand': 'Varinha',
    'Pistol': 'Pistola', 'Rifle': 'Rifle', 'Crossbow': 'Besta', 'Gold': 'Ouro', 'Fish': 'Peixe',
    'Map': 'Mapa', 'Potion': 'Poção', 'Scroll': 'Pergaminho', 'Ruby': 'Rubi', 'Pearl': 'Pérola',
    'Skull': 'Caveira', 'Citrine': 'Citrino', 'Diamond': 'Diamante', 'Emerald': 'Esmeralda',
    'Sapphire': 'Safira', 'Amethyst': 'Ametista', 'Eyeball': 'Globo Ocular', 'Opal': 'Opala',
    'Town': 'Cidade', 'Cave': 'Caverna', 'Mine': 'Mina', 'Crypt': 'Cripta', 'Palace': 'Palácio',
    'Fortress': 'Fortaleza', 'Temple': 'Templo', 'Shrine': 'Santuário', 'Catacombs': 'Catacumbas',
    'Caverns': 'Cavernas', 'Mines': 'Minas', 'Lava': 'Lava', 'Fog': 'Névoa', 'Rat': 'Rato',
    'Dog': 'Cachorro', 'Cat': 'Gato', 'Bat': 'Morcego', 'Ghost': 'Fantasma', 'Zombie': 'Zumbi',
    'Ghoul': 'Carniçal', 'Troll': 'Troll', 'Spider': 'Aranha', 'Imp': 'Diabrete', 'Golem': 'Golem',
    'Beast': 'Fera', 'Wolf': 'Lobo', 'Bear': 'Urso', 'Boar': 'Javali', 'Dragon': 'Dragão',
    'Drake': 'Draconiano', 'Snake': 'Cobra', 'Serpent': 'Serpente', 'Eagle': 'Águia', 'Falcon': 'Falcão',
    'Lion': 'Leão', 'Tiger': 'Tigre', 'Frog': 'Rã', 'Lich': 'Liche', 'Wisp': 'Fogo-Fátuo',
    'Sage': 'Sábio', 'Mage': 'Mago', 'Boy': 'Garoto', 'Girl': 'Garota', 'Bard': 'Bardo',
    'Seer': 'Vidente', 'Garrison': 'Guarnição', 'Vault': 'Cofre', 'Chamber': 'Câmara', 'Tower': 'Torre',
    'Maze': 'Labirinto', 'Lair': 'Covil', 'Tomb': 'Tumba', 'Ruins': 'Ruínas', 'Wall': 'Parede',
    'Floor': 'Chão', 'Door': 'Porta', 'Gate': 'Portão', 'Bridge': 'Ponte', 'Lever': 'Alavanca',
    'Trap': 'Armadilha', 'Well': 'Poço', 'River': 'Rio', 'Lake': 'Lago', 'Water': 'Água',
    'Anvil': 'Bigorna', 'Crank': 'Manivela', 'Chest': 'Baú', 'Stash': 'Baú', 'Barrel': 'Barril',
    'Crate': 'Caixote', 'Torch': 'Tocha', 'Brazier': 'Braseiro', 'Vase': 'Vaso', 'Urn': 'Urna',
    'Corpse': 'Cadáver', 'Bones': 'Ossos', 'Rock': 'Rocha', 'Stone': 'Pedra', 'Crystal': 'Cristal',
    'Portal': 'Portal', 'Key': 'Chave', 'Keg': 'Barril', 'Coin': 'Moeda', 'Coins': 'Moedas',
    'Gems': 'Gemas', 'Bill': 'Podão', 'Tuck': 'Estoque', 'Bling': 'Joia', 'Ferox': 'Ferox',
    'Repel': 'Repelir', 'Pyre': 'Pira', 'Root': 'Raiz', 'Self': 'Próprio', 'Stop': 'Parar',
    'Stun': 'Atordoar', 'Stab': 'Estocada', 'Warp': 'Teletransporte', 'Charm': 'Encanto',
    'Enemy': 'Inimigo', 'Event': 'Evento', 'Melee': 'Corpo a Corpo', 'Quake': 'Tremor',
    'Shock': 'Choque', 'Spawn': 'Gerar', 'Cast': 'Conjurar', 'Flag': 'Bandeira', 'Flap': 'Bater de Asas',
    'Flux': 'Fluxo', 'Furl': 'Enrolar', 'Lady': 'Dama', 'Merc': 'Mercenário', 'Armed': 'Armado',
    'Above': 'Acima', 'Below': 'Abaixo', 'Error': 'Erro', 'Music': 'Música', 'Piece': 'Peça',
    'Props': 'Objetos', 'Tongs': 'Tenazes', 'Tools': 'Ferramentas', 'Tusks': 'Presas',
    'Bucket': 'Balde', 'Carpet': 'Tapete', 'Crater': 'Cratera', 'Folder': 'Pasta', 'Height': 'Altura',
    'Loot': 'Saque', 'Socks': 'Meias', 'Spell': 'Feitiço', 'Sabre': 'Sabre', 'Trout': 'Truta',
    'Frozen': 'Congelado', 'Retirement': 'Aposentadoria', 'Details': 'Detalhes', 'Complete': 'Completo',
    'Repeatable': 'Repetível', 'Cinematic': 'Cinemática', 'Populate': 'Povoar', 'Ruleset': 'Conjunto de Regras',
    'Image': 'Imagem', 'Intro': 'Introdução', 'Quest': 'Missão', 'Create': 'Criar', 'Defeat': 'Derrotar',
    'Dialog': 'Diálogo', 'Return': 'Retornar', 'Reward': 'Recompensa', 'Acquire': 'Adquirir',
    'Horse': 'Cavalo', 'Unit': 'Unidade', 'Text': 'Texto', 'Find': 'Encontrar', 'Main': 'Principal',
    'Mine': 'Mina', 'Good': 'Bom', 'Evil': 'Mal', 'Head': 'Cabeça', 'Heal': 'Curar', 'Hide': 'Esconder',
    'Idle': 'Inativo', 'Kill': 'Matar', 'Leap': 'Salto', 'None': 'Nenhum', 'Perk': 'Vantagem',
    'Pets': 'Mascotes', 'Proc': 'Efeito', 'Burn': 'Queimar', 'Hit': 'Golpe', 'Pet': 'Mascote',
    'All': 'Todos', 'Any': 'Qualquer', 'Save': 'Salvar', 'Set': 'Conjunto', 'Item': 'Item',
    'Class': 'Classe', 'Count': 'Contagem', 'Skill': 'Habilidade', 'Prefix': 'Prefixo',
    'Suffix': 'Sufixo', 'Recipe': 'Receita', 'Result': 'Resultado', 'Cap': 'Tampa', 'Base': 'Base',
    'Exit': 'Saída', 'Room': 'Sala', 'Trim': 'Borda', 'Chunk': 'Bloco', 'Floor': 'Chão',
}

# Build uppercase and lowercase variants
FULL_WORDS_MAP = {}
for en, pt in WORD_TRANSLATIONS.items():
    FULL_WORDS_MAP[en] = pt
    FULL_WORDS_MAP[en.upper()] = pt.upper()
    FULL_WORDS_MAP[en.lower()] = pt.lower()

import re

# Common English word roots in Torchlight
WORD_ROOTS = {
    'Cave': 'Caverna', 'Lava': 'Lava', 'Mine': 'Mina', 'Crypt': 'Cripta', 'Ruins': 'Ruínas',
    'Palace': 'Palácio', 'Fortress': 'Fortaleza', 'Temple': 'Templo', 'Town': 'Cidade',
    'Miner': 'Mineiro', 'Miners': 'Mineiros', 'Bard': 'Bardo', 'Guard': 'Guarda', 'Guards': 'Guardas',
    'Old': 'Velho', 'Man': 'Homem', 'People': 'Pessoas', 'Sisters': 'Irmãs', 'Sister': 'Irmã',
    'Ghost': 'Fantasma', 'Ember': 'Âmbar', 'Colossus': 'Colosso', 'Primal': 'Primitivo',
    'Savage': 'Selvagem', 'Adamant': 'Adamantino', 'Sanguin': 'Sanguíneo', 'Gleaming': 'Brilhante',
    'Random': 'Aleatório', 'Game': 'Jogo', 'Win': 'Vitória', 'Complete': 'Completo',
    'Intro': 'Introdução', 'Greet': 'Saudação', 'Greets': 'Saudações', 'Acquire': 'Adquirir',
    'Entered': 'Entrou', 'Hatch': 'Alçapão', 'Seal': 'Selo', 'Magic': 'Mágico', 'Pet': 'Mascote',
    'Merc': 'Mercenário', 'Boss': 'Chefe', 'Test': 'Teste', 'Item': 'Item', 'Combiner': 'Combinador',
    'Make': 'Criar', 'Champion': 'Campeão', 'Force': 'Forçar', 'Accept': 'Aceitar',
    'Rough': 'Rústico', 'Coughy': 'Tossidor', 'Scot': 'Scot', 'Varkaseer': 'Vidente Varkolyn',
    'Part': 'Parte', 'Pt': 'Parte', 'Room': 'Sala', 'Floor': 'Chão', 'Wall': 'Parede',
    'Door': 'Porta', 'Pillar': 'Pilar', 'Stairs': 'Escadas', 'Arch': 'Arco', 'Rock': 'Rocha',
    'Tree': 'Árvore', 'Pine': 'Pinheiro', 'Fern': 'Samambaia', 'Grass': 'Grama', 'Scrub': 'Arbusto',
    'Bowl': 'Tigela', 'Hut': 'Cabana', 'Keg': 'Barril', 'Mug': 'Caneca', 'Urn': 'Urna',
    'Vent': 'Respiradouro', 'Beam': 'Viga', 'Lamp': 'Lâmpada', 'Tower': 'Torre', 'Exit': 'Saída',
    'Gold': 'Ouro', 'Fame': 'Fama', 'Xp': 'XP', 'Min': 'Mínimo', 'Max': 'Máximo', 'Pct': 'Percentual',
    'Show': 'Mostrar', 'Tips': 'Dicas', 'Mesh': 'Malha', 'File': 'Arquivo', 'Unit': 'Unidade',
    'Name': 'Nome', 'Display': 'Exibição', 'Type': 'Tipo', 'Quest': 'Missão', 'Floaty': 'Flutuante',
    'Text': 'Texto', 'Can': 'Pode', 'Abandon': 'Abandonar', 'Camera': 'Câmera', 'Mod': 'Modificador',
    'Spawn': 'Spawn', 'Class': 'Classe', 'Rule': 'Regra', 'Ruleset': 'Conjunto de Regras',
    'Monster': 'Monstro', 'Dungeon': 'Masmorra', 'Count': 'Contagem', 'Create': 'Criação',
    'Populate': 'Povoar', 'Repeatable': 'Repetível', 'Cinematic': 'Cinemática',
    'Male': 'Masculino', 'Female': 'Feminino', 'Strata': 'Estrato', 'Caustics': 'Cáustica',
    'Noshadow': 'Sem Sombra', 'Rimlight': 'Luz de Borda', 'Midwater': 'Meia-Água', 'Scalable': 'Escalável',
    'Straight': 'Reto', 'Quarter': 'Quarto', 'Half': 'Metade', 'Convex': 'Convexo', 'Concave': 'Côncavo',
    'Diagonal': 'Diagonal', 'Tileset': 'Conjunto de Peças', 'Automap': 'Automapa', 'Skybox': 'Céu',
    'Props': 'Objetos', 'Prop': 'Objeto', 'Rail': 'Trilho', 'Trim': 'Borda', 'Chunk': 'Bloco',
    'Anvil': 'Bigorna', 'Crank': 'Manivela', 'Tongs': 'Tenazes', 'Tools': 'Ferramentas',
    'Tusks': 'Presas', 'Bucket': 'Balde', 'Carpet': 'Tapete', 'Crater': 'Cratera', 'Folder': 'Pasta',
    'Height': 'Altura', 'Water': 'Água', 'Chair': 'Cadeira', 'Catapult': 'Catapulta',
    'Cauldron': 'Caldeirão', 'Crucible': 'Crisol', 'Grinder': 'Moedor', 'Meatrack': 'Suporte de Carne',
    'Scraps': 'Restos', 'Trough': 'Calha', 'Waygate': 'Portal',
}

# Add uppercase and lowercase versions
ROOTS_MAP = {}
for en, pt in WORD_ROOTS.items():
    ROOTS_MAP[en] = pt
    ROOTS_MAP[en.upper()] = pt.upper()
    ROOTS_MAP[en.lower()] = pt.lower()

def try_compound_translate(s: str) -> str | None:
    # 1. Match STRATA[0-9]+
    m_strata = re.match(r'^STRATA([0-9]+)$', s, re.I)
    if m_strata:
        return f"ESTRATO{m_strata.group(1)}"

    # 2. Match [PLACE]PT[0-9]+ or [Place]Pt[0-9]+
    m_pt = re.match(r'^([a-zA-Z]+)(PT|Pt|pt)([0-9]+(\.[0-9]+)?)$', s)
    if m_pt:
        place, _, num, _ = m_pt.groups()
        place_pt = ROOTS_MAP.get(place, place)
        return f"{place_pt} Parte {num}"

    # 3. Match MALE1, FEMALE1, FEMALE2
    m_gender = re.match(r'^(MALE|FEMALE)([0-9]+)$', s, re.I)
    if m_gender:
        g, num = m_gender.groups()
        g_pt = "MASCULINO" if g.upper() == "MALE" else "FEMININO"
        return f"{g_pt} {num}"

    # 4. Match [Prefix]Greet e.g. BARDGREET, MINERGREET
    m_greet = re.match(r'^([A-Z]+)GREETS?$', s)
    if m_greet:
        who = m_greet.group(1)
        who_pt = ROOTS_MAP.get(who, who)
        return f"SAUDAÇÃO DE {who_pt}"

    # 5. Match ENTERED[A-Z]+
    m_ent = re.match(r'^ENTERED([A-Z]+)$', s)
    if m_ent:
        where = m_ent.group(1)
        where_pt = ROOTS_MAP.get(where, where)
        return f"ENTROU EM {where_pt}"

    # 6. Match [Noun]Boss / [Noun]Test e.g. CaveBoss, MineBoss
    m_boss = re.match(r'^([A-Z][a-z]+)(Boss|Test)$', s)
    if m_boss:
        place, kind = m_boss.groups()
        pl_pt = ROOTS_MAP.get(place, place)
        k_pt = "Chefe" if kind == "Boss" else "Teste"
        return f"{k_pt} {pl_pt}"

    # 7. Match ALL CAPS compound tokens e.g. ISRANDOM, MAXCOUNT, MINCOUNT
    if s in ROOTS_MAP:
        return ROOTS_MAP[s]

    # Split CamelCase or PascalCase into words
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', s)
    if len(words) >= 2:
        translated_words = []
        all_found = True
        for w in words:
            if w in ROOTS_MAP:
                translated_words.append(ROOTS_MAP[w])
            else:
                all_found = False
                break
        if all_found:
            return " ".join(translated_words)

    return None


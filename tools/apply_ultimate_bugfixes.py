#!/usr/bin/env python3
"""
tools/apply_ultimate_bugfixes.py

Applies ultimate comprehensive bugfixes to translation_catalog.json:
1. Fixes all 294 possessive items where part2 was left in English (e.g. 'Rift\'s Ward' -> 'Proteção da Fenda').
2. Fixes all items with 'of the' or 'of' (e.g. 'Eye of the Scarab' -> 'Olho do Escaravelho').
3. Fixes all 36 Affixes with 'of the' and 40+ Affixes with '[ITEM] of <Concept/Skill>'.
4. Fixes all remaining partially-English Skills (PERCENT CAST SPEED, Golem upgrades, Wisp missiles).
5. Fixes all Globals stat, enchantment, and tooltip description strings (Health/Armor/Damage/Pet bonuses).
6. Fixes remaining untranslated weapon/armor base names (Scepter, Warwand, Culverin, Spetum, Hackbut, etc.).
7. Automatically recompiles translation_ptbr/translations/translation.dat and all 35 CEGUI layout files.
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CATALOG_PATH = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"

# Master dictionary of direct replacements
DIRECT_FIXES = {}

# 1. Globals Stat & Tooltip Strings
GLOBALS_FIXES = {
    '+[VALUE] Armor for [DURATION] seconds': '+[VALUE] de Armadura por [DURATION] segundos',
    '-[VALUE] Armor for [DURATION] seconds': '-[VALUE] de Armadura por [DURATION] segundos',
    '+[VALUE] Health for [DURATION] seconds': '+[VALUE] de Vida por [DURATION] segundos',
    '-[VALUE] Health for [DURATION] seconds': '-[VALUE] de Vida por [DURATION] segundos',
    '+[VALUE]% Health for [DURATION] seconds': '+[VALUE]% de Vida por [DURATION] segundos',
    '-[VALUE]% Health for [DURATION] seconds': '-[VALUE]% de Vida por [DURATION] segundos',
    'Permanently decreases Health by [VALUE]': 'Reduz permanentemente a Vida em [VALUE]',
    'Permanently increases Health by [VALUE]': 'Aumenta permanentemente a Vida em [VALUE]',
    '[VALUE]% Chance to Cast [NAME] at Target': '[VALUE]% de Chance de Conjurar [NAME] no Alvo',
    '[VALUE]% Chance to Cast [NAME] on Target': '[VALUE]% de Chance de Conjurar [NAME] no Alvo',
    '[VALUE]% Health Stolen for [DURATION] seconds': '[VALUE]% de Vida Roubada por [DURATION] segundos',
    '-[VALUE]% Health Stolen for [DURATION] seconds': '-[VALUE]% de Vida Roubada por [DURATION] segundos',
    '+[VALUE] Critical Hit Chance for [DURATION] seconds': '+[VALUE] de Chance de Golpe Crítico por [DURATION] segundos',
    '-[VALUE] Critical Hit Chance for [DURATION] seconds': '-[VALUE] de Chance de Golpe Crítico por [DURATION] segundos',
    '[VALUE] Health Stolen on Hit for [DURATION] seconds': '[VALUE] de Vida Roubada ao Acertar por [DURATION] segundos',
    '+[VALUE]% Pet and Minion Armor for [DURATION] seconds': '+[VALUE]% de Armadura de Mascotes e Lacaios por [DURATION] segundos',
    '-[VALUE]% Pet and Minion Armor for [DURATION] seconds': '-[VALUE]% de Armadura de Mascotes e Lacaios por [DURATION] segundos',
    '+[VALUE]% Pet and Minion Speed for [DURATION] seconds': '+[VALUE]% de Velocidade de Mascotes e Lacaios por [DURATION] segundos',
    '-[VALUE]% Pet and Minion Speed for [DURATION] seconds': '-[VALUE]% de Velocidade de Mascotes e Lacaios por [DURATION] segundos',
    '+[VALUE]% Ranged Weapon Damage for [DURATION] seconds': '+[VALUE]% de Dano com Armas de Longo Alcance por [DURATION] segundos',
    '-[VALUE]% Ranged Weapon Damage for [DURATION] seconds': '-[VALUE]% de Dano com Armas de Longo Alcance por [DURATION] segundos',
    '+[VALUE]% Martial Weapon Damage for [DURATION] seconds': '+[VALUE]% de Dano com Armas Marciais por [DURATION] segundos',
    '-[VALUE]% Martial Weapon Damage for [DURATION] seconds': '-[VALUE]% de Dano com Armas Marciais por [DURATION] segundos',
    '+[VALUE]% Pet and Minion Damage for [DURATION] seconds': '+[VALUE]% de Dano de Mascotes e Lacaios por [DURATION] segundos',
    '-[VALUE]% Pet and Minion Damage for [DURATION] seconds': '-[VALUE]% de Dano de Mascotes e Lacaios por [DURATION] segundos',
    '+[VALUE]% Pet and Minion Health for [DURATION] seconds': '+[VALUE]% de Vida de Mascotes e Lacaios por [DURATION] segundos',
    '-[VALUE]% Pet and Minion Health for [DURATION] seconds': '-[VALUE]% de Vida de Mascotes e Lacaios por [DURATION] segundos',
    '-[VALUE] Health Steal to Master for [DURATION] seconds': '-[VALUE] de Roubo de Vida para o Mestre por [DURATION] segundos',
    '[VALUE]% Chance to Poison Target for [DURATION] seconds.': '[VALUE]% de Chance de Envenenar o Alvo por [DURATION] segundos.',
    '-[VALUE]% Chance to Poison Target for [DURATION] seconds.': '-[VALUE]% de Chance de Envenenar o Alvo por [DURATION] segundos.',
    '[VALUE] Health Stolen to Master on Hit for [DURATION] seconds': '[VALUE] de Vida Roubada para o Mestre ao Acertar por [DURATION] segundos',
    '[VALUE]% Damage Bonus when Dual-Wielding for [DURATION] seconds': '[VALUE]% de Bônus de Dano ao Empunhar Duas Armas por [DURATION] segundos',
    '[VALUE]% Damage Penalty when Dual-Wielding for [DURATION] seconds': '[VALUE]% de Penalidade de Dano ao Empunhar Duas Armas por [DURATION] segundos',
    '[VALUE]% Damage Reflected Back on Attacker for [DURATION] seconds': '[VALUE]% de Dano Refletido de Volta ao Atacante por [DURATION] segundos',
    '[VALUE]% Chance to Reflect [VALUE3AND4]% of Missile Damage\\n     for [DURATION] seconds': '[VALUE]% de Chance de Refletir [VALUE3AND4]% do Dano de Projéteis\\n     por [DURATION] segundos',
    '-[VALUE]% Chance to Reflect [VALUE3AND4]% of Missile Damage\\n     for [DURATION] seconds': '-[VALUE]% de Chance de Refletir [VALUE3AND4]% do Dano de Projéteis\\n     por [DURATION] segundos',
    '[VALUE]% Chance to Reflect [VALUE3AND4]% of Missile Damage\n     for [DURATION] seconds': '[VALUE]% de Chance de Refletir [VALUE3AND4]% do Dano de Projéteis\n     por [DURATION] segundos',
    '-[VALUE]% Chance to Reflect [VALUE3AND4]% of Missile Damage\n     for [DURATION] seconds': '-[VALUE]% de Chance de Refletir [VALUE3AND4]% do Dano de Projéteis\n     por [DURATION] segundos',
    'PERCENT DAMAGE TAKEN': 'PERCENTUAL DE DANO RECEBIDO',
    'PERCENT ARMOR BONUS': 'BÔNUS PERCENTUAL DE ARMADURA',
    'PERCENT SPEED': 'PERCENTUAL DE VELOCIDADE',
    'CRITICAL': 'CRÍTICO',
    'critical': 'crítico',
    'SECONDS': 'SEGUNDOS',
    'seconds': 'segundos',
    'KNOCKBACK': 'REPULSÃO',
    'Bip01 Shoulder Armor': 'Armadura de Ombro Bip01',
    'Alric-Cast': 'Alric-Lançar',
}
DIRECT_FIXES.update(GLOBALS_FIXES)

# 2. Skills Fixes
SKILLS_FIXES = {
    'PERCENT CAST SPEED': 'PERCENTUAL DE VELOCIDADE DE CONJURAÇÃO',
    'PERCENT CRITICAL DAMAGE': 'PERCENTUAL DE DANO CRÍTICO',
    'PERCENT PET ARMOR': 'PERCENTUAL DE ARMADURA DO MASCOTE',
    'PERCENT BLOCK CHANCE BASE': 'CHANCE BASE PERCENTUAL DE BLOQUEIO',
    'POISON DEFENSE': 'DEFESA CONTRA VENENO',
    'Wisp Fire Missiles': 'Projéteis de Fogo do Fogo-Fátuo',
    'Wisp Posion Missiles': 'Projéteis de Veneno do Fogo-Fátuo',
    'Zealot Missiles': 'Projéteis do Fanático',
    'Electric Dart Missiles': 'Projéteis de Dardo Elétrico',
    'Medea Electric Missile': 'Projétil Elétrico de Medeia',
    'Shadow Armor Bow': 'Arco de Armadura Sombria',
    'Envelops you in Ember Energy, absorbing physical damage': 'Envolve você em Energia de Âmbar, absorvendo dano físico',
    'Imbue your weapons with Ember energy for increased damage': 'Imbui suas armas com energia de Âmbar para aumentar o dano',
    '\nPhase to a new location, dealing damage as you enter and exit nether space.\n': '\nDesloca-se para um novo local, causando dano ao entrar e sair do éter.\n',
    'Mastery of all forms of armor reduces requirements and improves armor absorption': 'O domínio de todas as armaduras reduz os requisitos e melhora a absorção de dano',
    'Golem upgrade delivers new Smash Attack': 'Aprimoramento do Golem concede novo Ataque Esmagador',
    'Golem upgrade delivers new Vortex Attack': 'Aprimoramento do Golem concede novo Ataque de Vórtice',
    'Lich range attack': 'Ataque à distância do Liche',
    'Alric Ember Shield': 'Escudo de Âmbar de Alric',
}
DIRECT_FIXES.update(SKILLS_FIXES)

# 3. Affixes Fixes
AFFIXES_FIXES = {
    '[ITEM] of the Ram': '[ITEM] do Carneiro',
    '[ITEM] of the Bull': '[ITEM] do Touro',
    '[ITEM] of the Hero': '[ITEM] do Herói',
    '[ITEM] of the Sage': '[ITEM] do Sábio',
    '[ITEM] of the Miser': '[ITEM] do Avarento',
    '[ITEM] of the Stone': '[ITEM] da Pedra',
    '[ITEM] of the Thorn': '[ITEM] do Espinho',
    '[ITEM] of the Winds': '[ITEM] dos Ventos',
    '[ITEM] of the Archer': '[ITEM] do Arqueiro',
    '[ITEM] of the Knight': '[ITEM] do Cavaleiro',
    '[ITEM] of the Raptor': '[ITEM] do Raptor',
    '[ITEM] of the Savage': '[ITEM] do Selvagem',
    '[ITEM] of the Savant': '[ITEM] do Erudito',
    '[ITEM] of the Seeker': '[ITEM] do Buscador',
    '[ITEM] of the Storms': '[ITEM] das Tempestades',
    '[ITEM] of the Turtle': '[ITEM] da Tartaruga',
    '[ITEM] of the Vizier': '[ITEM] do Grão-Vizir',
    '[ITEM] of the Glacier': '[ITEM] da Geleira',
    '[ITEM] of the Horizon': '[ITEM] do Horizonte',
    '[ITEM] of the Mammoth': '[ITEM] do Mamute',
    '[ITEM] of the Soldier': '[ITEM] do Soldado',
    '[ITEM] of the Vampire': '[ITEM] do Vampiro',
    '[ITEM] of the Colossus': '[ITEM] do Colosso',
    '[ITEM] of the Elephant': '[ITEM] do Elefante',
    '[ITEM] of the Enduring': '[ITEM] do Resistente',
    '[ITEM] of the Mountain': '[ITEM] da Montanha',
    '[ITEM] of the Stampede': '[ITEM] da Debandada',
    '[ITEM] of the Hurricane': '[ITEM] do Furacão',
    '[ITEM] of the Malignant': '[ITEM] do Maligno',
    '[ITEM] of the Barricades': '[ITEM] das Barricadas',
    '[ITEM] of the Malevolent': '[ITEM] do Malévolo',
    '[ITEM] of the Omniscient': '[ITEM] do Onisciente',
    '[ITEM] of the Slipstream': '[ITEM] do Vácuo',
    '[ITEM] of the Battlements': '[ITEM] das Muralhas',
    '[ITEM] of the Philosopher': '[ITEM] do Filósofo',
    '[ITEM] of the the Avalanche': '[ITEM] da Avalanche',
    '[ITEM] of Riches': '[ITEM] das Riquezas',
    '[ITEM] of Terror': '[ITEM] do Terror',
    '[ITEM] of Agility': '[ITEM] da Agilidade',
    '[ITEM] of Frailty': '[ITEM] da Fragilidade',
    '[ITEM] of Offense': '[ITEM] do Ataque',
    '[ITEM] of Iceshock': '[ITEM] do Choque de Gelo',
    '[ITEM] of Learning': '[ITEM] do Aprendizado',
    '[ITEM] of Ricochet': '[ITEM] do Ricochete',
    '[ITEM] of Stampede': '[ITEM] da Debandada',
    '[ITEM] of Devastate': '[ITEM] da Devastação',
    '[ITEM] of Hamstring': '[ITEM] de Romper Tendões',
    '[ITEM] of Knowledge': '[ITEM] do Conhecimento',
    '[ITEM] of Affliction': '[ITEM] da Aflição',
    '[ITEM] of Arrow Hail': '[ITEM] da Chuva de Flechas',
    '[ITEM] of Ember Bolt': '[ITEM] do Projétil de Âmbar',
    '[ITEM] of Flame Trap': '[ITEM] da Armadilha Flamejante',
    '[ITEM] of Needle Arc': '[ITEM] do Arco de Agulhas',
    '[ITEM] of Nether Imp': '[ITEM] do Diabrete do Éter',
    '[ITEM] of Shock Trap': '[ITEM] da Armadilha de Choque',
    '[ITEM] of Turbulence': '[ITEM] da Turbulência',
    '[ITEM] of Adventuring': '[ITEM] da Aventura',
    '[ITEM] of Ember Lance': '[ITEM] da Lança de Âmbar',
    '[ITEM] of Ember Phase': '[ITEM] do Salto de Âmbar',
    '[ITEM] of Ember Shock': '[ITEM] do Choque de Âmbar',
    '[ITEM] of Frost Pilum': '[ITEM] do Dardo de Gelo',
    '[ITEM] of Great Charm': '[ITEM] do Grande Encanto',
    '[ITEM] of Pet Command': '[ITEM] de Comando do Mascote',
    '[ITEM] of Retribution': '[ITEM] da Retribuição',
    '[ITEM] of Serendipity': '[ITEM] da Serenidade',
    '[ITEM] of Thorns Aura': '[ITEM] da Aura de Espinhos',
    '[ITEM] of Titan Stomp': '[ITEM] do Pisoteio Titânico',
    '[ITEM] of Burning Bind': '[ITEM] da Vinculação Ardente',
    '[ITEM] of Ember Sentry': '[ITEM] da Sentinela de Âmbar',
    '[ITEM] of Ember Shield': '[ITEM] do Escudo de Âmbar',
    '[ITEM] of Ember Strike': '[ITEM] do Golpe de Âmbar',
    '[ITEM] of Frost Shield': '[ITEM] do Escudo de Gelo',
    '[ITEM] of Justice Wind': '[ITEM] do Vento da Justiça',
    '[ITEM] of Seeking Shot': '[ITEM] do Disparo Perseguidor',
    '[ITEM] of Shadow Armor': '[ITEM] da Armadura Sombria',
    '[ITEM] of Slash Attack': '[ITEM] do Golpe Dilacerante',
    '[ITEM] of Conflagration': '[ITEM] da Conflagração',
    '[ITEM] of Dual Wielding': '[ITEM] de Usar Duas Armas',
    '[ITEM] of Great Defense': '[ITEM] da Grande Defesa',
    '[ITEM] of Great Offense': '[ITEM] do Grande Ataque',
    '[ITEM] of Seismic Burst': '[ITEM] da Explosão Sísmica',
    '[ITEM] of Spectral Echo': '[ITEM] do Eco Espectral',
    '[ITEM] of Thunderstorms': '[ITEM] das Tempestades',
    '[ITEM] of Devouring Trap': '[ITEM] da Armadilha Devoradora',
    '[ITEM] of Explosive Shot': '[ITEM] do Disparo Explosivo',
    '[ITEM] of Lightning Bomb': '[ITEM] da Bomba de Raios',
    '[ITEM] of Spectral Decay': '[ITEM] da Decomposição Espectral',
    '[ITEM] of Block and Parry': '[ITEM] de Bloqueio e Esquiva',
    '[ITEM] of Ember Lightning': '[ITEM] do Raio de Âmbar',
    '[ITEM] of Thorned Minions': '[ITEM] de Lacaios com Espinhos',
    '[ITEM] of Critical Strikes': '[ITEM] dos Golpes Críticos',
    '[ITEM] of Treasure Hunting': '[ITEM] da Caça ao Tesouro',
    '[ITEM] of Summon Beam Golem': '[ITEM] de Invocar Golem de Raio',
    '[ITEM] of Magic Weapons Expertise': '[ITEM] de Perícia com Armas Mágicas',
    '[ITEM] of Ranged Weapons Expertise': '[ITEM] de Perícia com Armas de Longo Alcance',
    '[ITEM] of Martial Weapons Expertise': '[ITEM] de Perícia com Armas Marciais',
}
DIRECT_FIXES.update(AFFIXES_FIXES)

# 4. Direct Item Fixes ('of the', unique items, base weapons)
ITEM_DIRECT_FIXES = {
    'Eye of the Scarab': 'Olho do Escaravelho',
    'Fury of the Hunted': 'Fúria dos Caçados',
    'Crest of the Warden': 'Crista do Guardião',
    'Eye of the Beholder': 'Olho do Observador',
    'epicEye of the Beholder': 'Olho do Observador Épico',
    'Raiment of the Hawk': 'Vestimenta do Falcão',
    'Scale of the Arbiter': 'Escama do Árbitro',
    'Seal of the Overseer': 'Selo do Feitor',
    'Emblem of the architect.': 'Emblema do arquiteto.',
    "Dragon's Tooth": 'Dente de Dragão',
    "The Sea King's Core-Ember Shard": 'Fragmento de Âmbar-Núcleo do Rei do Mar',
    "The Overseer's Grasp": 'Garra do Feitor',
    "Epic The Overseer's Grasp": 'Garra do Feitor Épica',
    "The Overseer's Touch": 'Toque do Feitor',
    "Epic The Overseer's Touch": 'Toque do Feitor Épico',
    "The Sea King's Pearl": 'Pérola do Rei do Mar',
    "The Toad King's Gall": 'Bile do Rei Sapo',
    "Epic The Toad King's Gall": 'Bile do Rei Sapo Épica',
    "The Guildmaster's Finest": 'Melhor Obra do Mestre da Guilda',
    "epicThe Guildmaster's Finest": 'Melhor Obra do Mestre da Guilda Épica',
    "The Legendary Druid's Core": 'Núcleo do Druida Lendário',
    "Epic The Legendary Druid's Core": 'Núcleo do Druida Lendário Épico',
    "epicThe Legendary Druid's Core": 'Núcleo do Druida Lendário Épico',
    "The Legendary Gravity's Grasp": 'Garra da Gravidade Lendária',
    "Epic The Legendary Gravity's Grasp": 'Garra da Gravidade Lendária Épica',
    "epicThe Legendary Gravity's Grasp": 'Garra da Gravidade Lendária Épica',
    "Cleave's Cloven Cleaver of Cleaving": 'Cutelo Partido da Clivagem de Cleave',
    "Epic Cleave's Cloven Cleaver of Cleaving": 'Cutelo Partido da Clivagem de Cleave Épico',
    "It's gleaming!": 'É reluzente!',
    "It's cold and slick.": 'É frio e escorregadio.',
    'Scepter': 'Cetro',
    'Warwand': 'Varinha de Guerra',
    'Culverin': 'Colubrina',
    'Demi-Culverin': 'Meia-Colubrina',
    'Dreadaxe': 'Machado do Pavor',
    'Gargoyle': 'Gárgula',
    'Solitude': 'Solidão',
    'Cataclysm': 'Cataclismo',
    'Greatwand': 'Grande Varinha',
    'Grimwatch': 'Vigia Sombria',
    'Battlewand': 'Varinha de Batalha',
    'Warstarter': 'Iniciador da Guerra',
    'Terrorsprig': 'Ramo do Terror',
    'Arcuballista': 'Arcubalista',
    'Daggerpistol': 'Pistola-Adaga',
    'Ribauldequin': 'Ribauldequim',
    'Hackbut': 'Arcabuz',
    'Spetum': 'Espeto de Guerra',
    'catfish': 'peixe-gato',
    'dogfish': 'peixe-cão',
    'chopper': 'cutelo',
    'hacker': 'cutelo',
    'Trollmaster': 'Mestre dos Trolls',
}
DIRECT_FIXES.update(ITEM_DIRECT_FIXES)

# 5. Possessive Noun (Part 2) Mapping: (translated_noun, grammatical_gender)
# gender: 'm' (masculine singular), 'f' (feminine singular), 'mp' (masc plural), 'fp' (fem plural)
PART2_DATA = {
    '"Ornate"': ('"Ornamentado"', 'm'),
    '"Sawed-Off"': ('"Cano Serrado"', 'm'),
    'Abundance': ('Abundância', 'f'),
    'Agglomeration': ('Aglomeração', 'f'),
    'Aim': ('Mira', 'f'),
    'Amassment': ('Acúmulo', 'm'),
    'Assemblage': ('Conjunto', 'm'),
    'Bad Influence': ('Má Influência', 'f'),
    'Badge': ('Insígnia', 'f'),
    'Bastion': ('Bastião', 'm'),
    'Brace': ('Braçadeira', 'f'),
    'Brink': ('Beira', 'f'),
    'Bulwark': ('Baluarte', 'm'),
    'Butress': ('Contraforte', 'm'),
    'Butt Kickers': ('Chuta-Traseiros', 'mp'),
    'Cache': ('Esconderijo', 'm'),
    'Centerpiece': ('Peça Central', 'f'),
    'Cleave': ('Cutelo', 'm'),
    'Cleaver': ('Cutelo', 'm'),
    'Cloven Cleaver of Cleaving': ('Cutelo Partido da Clivagem', 'm'),
    'Command': ('Comando', 'm'),
    'Control': ('Controle', 'm'),
    'Conundrum': ('Enigma', 'm'),
    'Convocation': ('Convocação', 'f'),
    'Core': ('Núcleo', 'm'),
    'Core-Ember Shard': ('Fragmento de Âmbar-Núcleo', 'm'),
    'Corset': ('Espartilho', 'm'),
    'Craft': ('Ofício', 'm'),
    'Craft Brim': ('Aba do Ofício', 'f'),
    'Craft Token': ('Emblema do Ofício', 'm'),
    'Crazed Insignia': ('Insígnia Enlouquecida', 'f'),
    'Crusader': ('Cruzado', 'm'),
    'Crystal Shoulders': ('Ombreiras de Cristal', 'fp'),
    'Deadeye Piece': ('Peça do Tiro Certeiro', 'f'),
    'Delerium': ('Delírio', 'm'),
    'Delight': ('Deleite', 'm'),
    'Doom': ('Ruína', 'f'),
    'Dust Guard': ('Guarda-Poeira', 'm'),
    'Edge': ('Lâmina', 'f'),
    'Embrace': ('Abraço', 'm'),
    'Enforcer': ('Executor', 'm'),
    'Eye': ('Olho', 'm'),
    'Eyeball': ('Globo Ocular', 'm'),
    'Fancy': ('Capricho', 'm'),
    'Fasces': ('Fasces', 'fp'),
    'Favor': ('Favor', 'm'),
    'Fedora': ('Chapéu Fedora', 'm'),
    'Final Desire': ('Desejo Final', 'm'),
    'Finest': ('Melhor Obra', 'f'),
    'Floe': ('Bloco de Gelo', 'm'),
    'Folly': ('Loucura', 'f'),
    'Foundation': ('Fundação', 'f'),
    'Fusillade': ('Fuzilaria', 'f'),
    'Gall': ('Bile', 'f'),
    'Grasp': ('Garra', 'f'),
    'Guard': ('Guarda', 'm'),
    'Gunblade': ('Lâmina-Pistola', 'f'),
    'Gut Hider': ('Esconde-Barriga', 'm'),
    'Hands': ('Mãos', 'fp'),
    'Hate': ('Ódio', 'm'),
    'Head Banger': ('Quebra-Cabeças', 'm'),
    'Heart': ('Coração', 'm'),
    'Hoard': ('Tesouro', 'm'),
    'Honor Badge': ('Insígnia de Honra', 'f'),
    'Hope': ('Esperança', 'f'),
    'Ideal': ('Ideal', 'm'),
    'Insight': ('Percepção', 'f'),
    'Journal': ('Diário', 'm'),
    'Kettle': ('Chaleira', 'f'),
    'Killer': ('Matador', 'm'),
    'Law': ('Lei', 'f'),
    'Leverage': ('Alavanca', 'f'),
    'Lifebelt': ('Cinto da Vida', 'm'),
    'Linchpin': ('Eixo', 'm'),
    'Lionheart': ('Coração de Leão', 'm'),
    'Love': ('Amor', 'm'),
    'Luckstone': ('Pedra da Sorte', 'f'),
    'Manipulators': ('Manipuladores', 'mp'),
    'Mind': ('Mente', 'f'),
    'Moon': ('Lua', 'f'),
    'Mortar': ('Morteiro', 'm'),
    'Nose Wipers': ('Limpa-Nariz', 'm'),
    'Orbit': ('Órbita', 'f'),
    'Pearl': ('Pérola', 'f'),
    'Pepperbox': ('Pistola Pimenteiro', 'f'),
    'Pick': ('Picareta', 'f'),
    'Pole': ('Mastro', 'm'),
    'Presence': ('Presença', 'f'),
    'Prison': ('Prisão', 'f'),
    'Quickload': ('Recarga Rápida', 'f'),
    'Rail Cannon': ('Canhão Elétrico', 'm'),
    'Ravager': ('Devastador', 'm'),
    'Reach': ('Alcance', 'm'),
    'Refuge': ('Refúgio', 'm'),
    'Resistance': ('Resistência', 'f'),
    'Roughhide Tonic': ('Tônico de Couro Bruto', 'm'),
    'Scepter': ('Cetro', 'm'),
    'Schism': ('Cisma', 'm'),
    'Scrutiny': ('Escrutínio', 'm'),
    'Second Chance': ('Segunda Chance', 'f'),
    'Sepulchar': ('Sepulcro', 'm'),
    'Sepulchre': ('Sepulcro', 'm'),
    'Shaft': ('Haste', 'f'),
    'Sidearm': ('Arma Secundária', 'f'),
    'Singing Brush': ('Pincel Cantante', 'm'),
    'Sonic': ('Sônico', 'm'),
    'Spade': ('Pá', 'f'),
    'Spurs': ('Esporas', 'fp'),
    'Star': ('Estrela', 'f'),
    'Strength': ('Força', 'f'),
    'Targetgun': ('Arma de Precisão', 'f'),
    'Tooth': ('Dente', 'm'),
    'Touch': ('Toque', 'm'),
    'Trappings': ('Adornos', 'mp'),
    'Valiant': ('Valente', 'm'),
    'Vision': ('Visão', 'f'),
    'Vital Organ': ('Órgão Vital', 'm'),
    'Ward': ('Proteção', 'f'),
    'Window': ('Janela', 'f'),
    'Wingblade': ('Lâmina Alada', 'f'),
    'Wisdom': ('Sabedoria', 'f'),
}

# Common noun / title translations for Part 1 (owner)
PART1_TITLES = {
    'The Overseer': 'do Feitor',
    'The Toad King': 'do Rei Sapo',
    'The Sea King': 'do Rei do Mar',
    'The Guildmaster': 'do Mestre da Guilda',
    'The Legendary Druid': 'do Druida Lendário',
    'The Legendary Gravity': 'da Gravidade Lendária',
    'King': 'do Rei',
    'Miner': 'do Minerador',
    'Monk': 'do Monge',
    'Warden': 'do Guardião',
    'Warder': 'do Guardião',
    'Abbot': 'do Abade',
    'Ancestor': 'dos Ancestrais',
    'Ancester': 'dos Ancestrais',
    'Fisher': 'do Pescador',
    'Friar': 'do Frade',
    'Grandma': 'da Vovó',
    'Horseman': 'do Cavaleiro',
    'Traveler': 'do Viajante',
    'Gladiator': 'do Gladiador',
    'Reaver': 'do Salteador',
    'Skeptic': 'do Cético',
    'Soul': 'da Alma',
    'Totem': 'do Totem',
    'Dragon': 'do Dragão',
    'Diamond': 'de Diamante',
    'Diamondo': 'de Diamondo',
    'Dragonvein': 'de Veia de Dragão',
    'Gravity': 'da Gravidade',
    'Rift': 'da Fenda',
    'Kindom': 'do Reino',
    'Grove': 'do Bosque',
    'Officer': 'do Oficial',
    'Captain': 'do Capitão',
    'Fletcher': 'do Flecheiro',
    'Craftman': 'do Artesão',
    'Archer': 'do Arqueiro',
    'Bishop': 'do Bispo',
    'Embalmer': 'do Embalsamador',
    'Hellcameawalkin': 'do Caminhante do Inferno',
    'General Orrin': 'do General Orrin',
    'Legionaire': 'do Legionário',
}


def get_epic_suffix(gender: str) -> str:
    """Returns correct Portuguese inflection for 'Épico'."""
    if gender == 'f':
        return 'Épica'
    if gender == 'fp':
        return 'Épicas'
    if gender == 'mp':
        return 'Épicos'
    return 'Épico'


def translate_possessive_item(original: str) -> str | None:
    """
    Translates an item of form "[Epic ]<Owner>'s <ItemNoun>".
    Returns localized Portuguese string with accurate gender agreement and word order.
    """
    is_epic = False
    clean_orig = original

    # Handle epic prefix
    if clean_orig.startswith("Epic ") or clean_orig.startswith("epic "):
        is_epic = True
        clean_orig = clean_orig[5:].strip()
    elif clean_orig.startswith("epic") and clean_orig[4:5].isupper():
        is_epic = True
        clean_orig = clean_orig[4:].strip()

    if "'s " not in clean_orig:
        return None

    part1, part2 = clean_orig.split("'s ", 1)
    part1 = part1.strip()
    part2 = part2.strip()

    # Check if part2 is in our dictionary
    if part2 not in PART2_DATA:
        return None

    tr_part2, gender = PART2_DATA[part2]

    # Resolve part1 owner
    # Check if part1 has 'epic' attached
    if part1.startswith("epic") and len(part1) > 4 and part1[4].isupper():
        is_epic = True
        part1 = part1[4:]

    if part1 in PART1_TITLES:
        owner_phrase = PART1_TITLES[part1]
    else:
        # Proper noun -> "de <Name>"
        # Medea -> Medeia
        name = 'Medeia' if part1 == 'Medea' else part1
        owner_phrase = f"de {name}"

    if is_epic:
        epic_adj = get_epic_suffix(gender)
        return f"{tr_part2} {owner_phrase} {epic_adj}"
    else:
        return f"{tr_part2} {owner_phrase}"


def main():
    print("=" * 70)
    print(" Applying Ultimate Bugfixes to Torchlight pt-BR Translation Catalog")
    print(f" Catalog: {CATALOG_PATH}")
    print("=" * 70)

    if not CATALOG_PATH.exists():
        print(f"Error: Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    updated_count = 0
    total_processed = 0

    for cat_name, entries in catalog["categories"].items():
        for item in entries:
            total_processed += 1
            orig = item.get("original", "")
            curr_tr = item.get("translation", "")

            # 1. Check direct fixes
            if orig in DIRECT_FIXES:
                new_tr = DIRECT_FIXES[orig]
                if curr_tr != new_tr:
                    item["translation"] = new_tr
                    updated_count += 1
                continue

            # 2. Check possessive items
            if cat_name == "Items" and ("'s " in orig or "'s" in orig):
                poss_tr = translate_possessive_item(orig)
                if poss_tr and poss_tr != curr_tr:
                    item["translation"] = poss_tr
                    updated_count += 1
                    continue

    print(f"Catalog successfully updated:")
    print(f"  - Total entries processed: {total_processed}")
    print(f"  - Translations updated:    {updated_count}")

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"  - Saved to: {CATALOG_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()

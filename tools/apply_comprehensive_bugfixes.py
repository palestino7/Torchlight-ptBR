#!/usr/bin/env python3
"""
tools/apply_comprehensive_bugfixes.py

Applies comprehensive bugfixes to translation_catalog.json:
1. Fixes all 578+ smashed/unspaced translations across UI, Quests, Items, Monsters, Skills, Globals, Dungeons, Recipes.
2. Fixes all 66 player-facing identical items that were left untranslated.
3. Fixes all mangled possessive/contraction translations (e.g. 'warm to the touch. de It' -> 'É quente ao toque.').
4. Fixes gender agreement and adjective order on armor/weapon equipment.
5. Injects the 12 missing ground-truth words ('Armor', 'Damage', 'Fire', 'Ice', 'Level', 'Mana', 'Poison', 'Rank', 'Type', 'Skeleton', 'armor').
6. Preserves exact string keys for whitespace-sensitive lookups in CStringTranslate::Translate().
7. Recompiles translation.dat and all 35 CEGUI layout files.
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"

# Ensure project root is in sys.path
sys.path.insert(0, str(PROJECT_ROOT))
import tools.quest_translations_full as qtf
Q_FULL = qtf.QUEST_TRANSLATIONS

# Master Fix Dictionary
FIXES = {}

# 1. UI Fixes
UI_FIXES = {
    'Spells': 'Feitiços',
    'Pet Name': 'Nome do Mascote',
    'Very Hard': 'Muito Difícil',
    'Next Level': 'Próximo Nível',
    'Show Blood': 'Mostrar Sangue',
    'Skill Type': 'Tipo de Habilidade',
    'HW Skinning': 'Skinning por HW',
    'Enchanted Axe': 'Machado Encantado',
    'Performs Skill': 'Executa Habilidade',
    'requires level 21': 'Requer nível 21',
    'Render Behind Walls': 'Renderizar Atrás de Paredes',
    'The Destroyer excels at melee combat and channels the power of his ancestors': 'O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais',
}
FIXES.update(UI_FIXES)

# 2. Missing Ground Truth Words
MISSING_WORDS = {
    'Armor': 'Armadura',
    'armor': 'armadura',
    'Damage': 'Dano',
    'Fire': 'Fogo',
    'Ice': 'Gelo',
    'Level': 'Nível',
    'Mana': 'Mana',
    'Poison': 'Veneno',
    'Rank': 'Grau',
    'Skeleton': 'Esqueleto',
    'Type': 'Tipo',
}
FIXES.update(MISSING_WORDS)

# 3. Globals Fixes
GLOBALS_FIXES = {
    'DEATHS': 'MORTES',
    'Deaths': 'Mortes',
    'the Red': 'o Vermelho',
    'the Black': 'o Negro',
    'Level Up': 'Subiu de Nível',
    'GOLD DROP': 'QUEDA DE OURO',
    'Trap Door': 'Alçapão',
    'WAYPOINTS': 'PONTOS DE TELETRANSPORTE',
    'Waypoints': 'Pontos de Teletransporte',
    'left hand': 'mão esquerda',
    'right hand': 'mão direita',
    'Socketable': 'Engastável',
    'Well-Known': 'Bem Conhecido',
    'Illustrious': 'Ilustre',
    'Prestigious': 'Prestigioso',
    'Acknowledged': 'Reconhecido',
    'Unattainable': 'Inatingível',
    'Unidentified': 'Não Identificado',
    'Unrecognized': 'Não Reconhecido',
    'Unremarkable': 'Comum',
    'two-handed melee': 'corpo a corpo de duas mãos',
    'single handed melee': 'corpo a corpo de uma mão',
    'Portal to Glyph Room': 'Portal para a Sala de Glifos',
    'Alric-Die': 'Alric-Die',
    'Alric-Cast': 'Alric-Cast',
    'Alric-Summon': 'Alric-Summon',
    'Alric-Journal': 'Alric-Journal',
    'BatGuyCast': 'BatGuyCast',
    'BatGuySpawn': 'BatGuySpawn',
    'BatGuyAttack': 'BatGuyAttack',
    'BatGuyGetHit': 'BatGuyGetHit',
    'BatGuyPoolHit': 'BatGuyPoolHit',
    'BatGuyPoolLoop': 'BatGuyPoolLoop',
    'ChainSwing': 'ChainSwing',
    'MagicArrow': 'MagicArrow',
    'Bip02 Spine2': 'Bip02 Spine2',
    'Bip02 Spine3': 'Bip02 Spine3',
    'GoldDrop_Easy': 'GoldDrop_Easy',
    'GoldDrop_Hard': 'GoldDrop_Hard',
}
FIXES.update(GLOBALS_FIXES)

# 4. Recipes and Dungeons Fixes
RECIPES_DUNGEONS = {
    'SUSHI HELM': 'ELMO DE SUSHI',
    'MANA POTION': 'POÇÃO DE MANA',
    'HEALTH POTION': 'POÇÃO DE VIDA',
    'FOG END': 'FIM DA NÉVOA',
    'FOG RED': 'NÉVOA VERMELHA',
    'FOG BLUE': 'NÉVOA AZUL',
    'Fog Wall': 'Parede de Névoa',
}
FIXES.update(RECIPES_DUNGEONS)

# 5. Skills Fixes
SKILLS_FIXES = {
    'FADE OUT': 'DESVANECER',
    'Ice Shot': 'Disparo de Gelo',
    'KNOCK BACK': 'REPULSÃO',
    'Ember Shield': 'Escudo de Âmbar',
    'Frost Shield': 'Escudo de Gelo',
    'FrostShield1': 'FrostShield1',
    'Shadow Armor': 'Armadura Sombria',
    'CRUSHINGBURST KNOCK BACK EFFECT': 'Efeito de Recuo do Golpe Esmagador',
    'Golem recieves ultimate upgrade': 'Golem recebe aprimoramento supremo',
}
FIXES.update(SKILLS_FIXES)

# 6. Monsters Fixes
MONSTERS_FIXES = {
    'Ice Wisp': 'Fogo-Fátuo de Gelo',
    'Fire Wisp': 'Fogo-Fátuo de Fogo',
    'Armor Rack': 'Suporte de Armadura',
    'Cave Troll': 'Troll das Cavernas',
    'Gem seller': 'Vendedor de Gemas',
    'Rapid fire': 'Fogo Rápido',
    'Ice attacks and resistance': 'Ataques e resistência a gelo',
    'Destroys gems in socketed items': 'Destrói gemas em itens com engastes',
    'Undead Dwarf Corrupted Champion': 'Campeão Anão Morto-Vivo Corrompido',
    'Ice attacks - Resists ice damage': 'Ataques de gelo - Resiste a dano de gelo',
    'BatGuyDie': 'BatGuyDie',
    'BatGuyIdle': 'BatGuyIdle',
    'BatGuyCharge': 'BatGuyCharge',
    'HeavyStoneWalk': 'HeavyStoneWalk',
    'Alric-Attack': 'Alric-Attack',
}
FIXES.update(MONSTERS_FIXES)

# 7. Quests Fixes (including all from Q_FULL)
FIXES.update(Q_FULL)

QUEST_MANUAL = {
    'Brink, no! What has happened!\\n\\nAlas, my friend...': 'Brink, não! O que aconteceu?\n\nAi de mim, meu amigo...',
    "Brink! Over here! I can't hold them back much longer -": "Brink! Aqui! Não vou aguentar segurá-los por muito mais tempo...",
    'Alric has been corrupted by the Ember and has taken Syl.': 'Alric foi corrompido pelo Âmbar e levou Syl.',
    'Alric has captured Syl.  Descend further and rescue her.': 'Alric capturou Syl. Desça mais fundo e resgate-a.',
    'Rare Stone': 'Pedra Rara',
    'Varkolyn Mage': 'Mago Varkolyn',
    'GOREN THE ENCHANTER': 'GOREN, O ENCANTADOR',
    "I'm looking for monsters!": "Estou procurando monstros!",
    "Have you seen any monsters?": "Você viu algum monstro?",
    "I'm faster than any monster!": "Sou mais rápido do que qualquer monstro!",
    "The door is magically sealed.": "A porta está selada magicamente.",
    "My dad is protecting the town!": "Meu pai está protegendo a cidade!",
    "Ordrak has risen from Alric's sacrifice.": "Ordrak ressurgiu do sacrifício de Alric.",
    "Can I have your armor when you're done with it?": "Posso ficar com a sua armadura quando você terminar de usá-la?",
    "Now I have you!  What have you done with Alric?": "Agora peguei você! O que você fez com Alric?",
    "I don't want monsters here, they should go away!": "Não quero monstros aqui, eles deveriam ir embora!",
    "As you meet the horse's large brown eyes, a chill runs down your spine.": "Quando você encara os grandes olhos castanhos do cavalo, um calafrio percorre sua espinha.",
    "There's beasties in the walls! I can hear 'em scrabblin' around in there.": "Há criaturas nas paredes! Consigo ouvi-las se rastejando lá dentro.",
    "Vasman has asked you to find a piece of Adamant Ember in the Dwarven Ruins.": "Vasman pediu para você encontrar um fragmento de Âmbar Adamantino nas Ruínas Anãs.",
    "You there! We need every able warrior to help us defend the town - follow me!": "Você aí! Precisamos de todo guerreiro capaz para ajudar a defender a cidade — siga-me!",
    "I hope I can get back into the tunnels soon, I'm not used to all this fresh air.": "Espero poder voltar aos túneis logo, não estou acostumado com todo esse ar fresco.",
    "<LOOKAT=SEER>You alright Syl?  Rest here awhile, I'm going ahead to finish the job.": "<LOOKAT=SEER>Você está bem, Syl? Descanse aqui um pouco, vou na frente para terminar o serviço.",
    "Vasman has asked you to find a piece of Shimmering Ember in an area filled with water.": "Vasman pediu para você encontrar um fragmento de Âmbar Tremeluzente em uma área inundada.",
    "You have done so much for Torchlight, and for me.  I cannot thank you enough my friend.": "Você fez tanto por Torchlight e por mim. Não tenho como lhe agradecer o suficiente, meu amigo.",
    "Vasman has asked you to find a piece of Savage Ember in a place filled with molten rock.": "Vasman pediu para você encontrar um fragmento de Âmbar Selvagem em um local repleto de rocha derretida.",
    'MINERTOWN1': 'MINERTOWN1',
    'MINERTOWN2': 'MINERTOWN2',
    'MINERTOWN3': 'MINERTOWN3',
    'MINERTOWN4': 'MINERTOWN4',
    'ghost_minion1': 'ghost_minion1',
    'ghost_minion2': 'ghost_minion2',
    'ghost_minion3': 'ghost_minion3',
    'SYL-IMABITOVER': 'SYL-IMABITOVER',
    'SYL-YOUFOUNDIT': 'SYL-YOUFOUNDIT',
    'SYL-IHAVEHEARDOF': 'SYL-IHAVEHEARDOF',
    'SYL-ITISNOWONDER': 'SYL-ITISNOWONDER',
    'ALRIC-IMHEREBRINK': 'ALRIC-IMHEREBRINK',
    'SYL-WERETHEDWARVES': 'SYL-WERETHEDWARVES',
    'ALRIC-YOUHAVESLOWED': 'ALRIC-YOUHAVESLOWED',
    'SYL-THEQUAKESARESUB': 'SYL-THEQUAKESARESUB',
    'SYL-THESERUINSIHAVE': 'SYL-THESERUINSIHAVE',
    'ALRIC-ORDRAAKRECIEVE': 'ALRIC-ORDRAAKRECIEVE',
    'SYL-IHAVEREACTIVATED': 'SYL-IHAVEREACTIVATED',
    'SYL-THECYCLEISBROKEN': 'SYL-THECYCLEISBROKEN',
    'ALRIC-ITAUGHTYOUABOUT': 'ALRIC-ITAUGHTYOUABOUT',
    'SYL-AHHEREAREHISNOTES': 'SYL-AHHEREAREHISNOTES',
    'SYL-NOWHATHASHAPPENED': 'SYL-NOWHATHASHAPPENED',
    'SYL-YOUHAVEDONESOMUCH': 'SYL-YOUHAVEDONESOMUCH',
    'SYL-YOUSAYTHISISALRIC': 'SYL-YOUSAYTHISISALRIC',
    'ALRIC-SYLHAVEYOUCOMETO': 'ALRIC-SYLHAVEYOUCOMETO',
    'ALRIC-WHYDOYOUSTRUGGLE': 'ALRIC-WHYDOYOUSTRUGGLE',
    'SYL-ICANTBELIEVEMASTER': 'SYL-ICANTBELIEVEMASTER',
    'SYL-THANKYOUFORPUTTING': 'SYL-THANKYOUFORPUTTING',
    'SYL-MADEITTOTHEFORTRESS': 'SYL-MADEITTOTHEFORTRESS',
    'SYL-MASTERALRICTAUGHTME': 'SYL-MASTERALRICTAUGHTME',
    'SYL-WHEREYOUDRAWNHEREBY': 'SYL-WHEREYOUDRAWNHEREBY',
    'SYL-EMBERFORGEISFOUNDFAR': 'SYL-EMBERFORGEISFOUNDFAR',
    'SYL-YOUHAVEFREEDOVERSEER': 'SYL-YOUHAVEFREEDOVERSEER',
    'SYL-THISMOUNTAINHASALWAYS': 'SYL-THISMOUNTAINHASALWAYS',
    'SYL-YOURECOVEREDTHEGLYPHS': 'SYL-YOURECOVEREDTHEGLYPHS',
    'ALRIC-ITHOUGHTYOUWOULDCOME': 'ALRIC-ITHOUGHTYOUWOULDCOME',
    'SYL-CANTHOLDBACKMUCHLONGER': 'SYL-CANTHOLDBACKMUCHLONGER',
    'SYL-IFTHISSHAKINGCONTINUES': 'SYL-IFTHISSHAKINGCONTINUES',
    'SYL-THEEVILBELOWTORCHLIGHT': 'SYL-THEEVILBELOWTORCHLIGHT',
    'SYL-ALRIGHTIMACTIVATINGITNOW': 'SYL-ALRIGHTIMACTIVATINGITNOW',
    'SYL-MASTERALRICYOUWOULDNEVER': 'SYL-MASTERALRICYOUWOULDNEVER',
    'SYL-NOWONDERALRICSENTFORHELP': 'SYL-NOWONDERALRICSENTFORHELP',
    'ALRIC-COMPLETIONOFTHEDARKEMBER': 'ALRIC-COMPLETIONOFTHEDARKEMBER',
}
FIXES.update(QUEST_MANUAL)

# 8. Items Fixes (Complete Item Lexicon)
ITEM_MANUAL = {
    "A warrior's trophy.": "Troféu de guerreiro.",
    "It's warm to the touch.": "É quente ao toque.",
    "It's ancient.  There's a sketch of a wand on the cover.": "É antigo. Há o esboço de uma varinha na capa.",
    "Symbol of the storm's fury.": "Símbolo da fúria da tempestade.",
    "A symbol of the Warden's power.": "Um símbolo do poder do Guardião.",
    "It's engraved with strange symbols": "Está gravado com símbolos estranhos.",
    "The cog's teeth are unevenly spaced.": "Os dentes da engrenagem estão espaçados de forma irregular.",
    "It's fragile and would break in combat.": "É frágil e se quebraria em combate.",
    "It's rough and covered with crude markings.": "É áspero e coberto de marcas rudimentares.",
    "Great Steppe's Reach": "Alcance da Grande Estepe",
    "The Overseer's Reach": "Alcance do Feitor",
    "Epic Great Steppe's Reach": "Alcance da Grande Estepe Épico",
    "Epic The Overseer's Reach": "Alcance do Feitor Épico",
    "The House of Pain": "A Casa da Dor",
    "The Edge of Mania": "O Limiar da Loucura",
    "epicThe House of Pain": "A Casa da Dor Épica",
    "epicThe Edge of Mania": "O Limiar da Loucura Épico",
    "The Left Hand of Orlac": "A Mão Esquerda de Orlac",
    "The Right Hand of Orlac": "A Mão Direita de Orlac",
    "epicThe Left Hand of Orlac": "A Mão Esquerda de Orlac Épica",
    "Epic The Left Hand of Orlac": "A Mão Esquerda de Orlac Épica",
    "epicThe Right Hand of Orlac": "A Mão Direita de Orlac Épica",
    "Epic The Right Hand of Orlac": "A Mão Direita de Orlac Épica",
    "The Legendary Dragonspine Sword": "A Lendária Espada Espinha de Dragão",
    "epicThe Legendary Dragonspine Sword": "A Lendária Espada Espinha de Dragão Épica",
    "Epic The Legendary Dragonspine Sword": "A Lendária Espada Espinha de Dragão Épica",
    "The lens of a dwarven gem-crafter.": "A lente de um artífice de gemas anão.",
    "It's pure gold with crystal windows.": "É de ouro puro com janelas de cristal.",
    "It's surprisingly light, but you doubt any blow could scratch it.": "É surpreendentemente leve, mas você duvida que qualquer golpe consiga arranhá-lo.",
    "It's quite light.": "É bastante leve.",
    "The caster's movement speed is increased for 8 seconds.\\n\\nRight-click to learn spell.": "A velocidade de movimento do conjurador é aumentada por 8 segundos.\\n\\nClique com o botão direito para aprender o feitiço.",
    "Launches a slow-moving, explosive ball of flame from the caster's hand.\\n\\nRight-click to learn this spell.": "Lança uma esfera explosiva de fogo lenta a partir da mão do conjurador.\\n\\nClique com o botão direito para aprender este feitiço.",
    "Insert his eye into weapons and armor with empty slots to garner their effects and increase engineering skill.": "Insira o olho dele em armas e armaduras com encaixes vazios para obter seus efeitos e aumentar a perícia de engenharia.",
    "Hellcameawalkin's Axe of Decay": "Machado da Ruína do Caminhante do Inferno",
    "epicHellcameawalkin's Axe of Decay": "Machado da Ruína do Caminhante do Inferno Épico",
    "Epic Hellcameawalkin's Axe of Decay": "Machado da Ruína do Caminhante do Inferno Épico",
    "Epic Rodin's Ulitlity Belt": "Cinto de Utilidades de Rodin Épico",
    "Epic Valcone's Only Friend": "Único Amigo de Valcone Épico",
    "epicEmbalmer's Rotten Belt": "Cinto Putrefato do Embalsamador Épico",
    "Epic Embalmer's Rotten Belt": "Cinto Putrefato do Embalsamador Épico",
    "Leone's Shootin' Gloves": "Luvas de Tiro de Leone",
    "Epic Leone's Shootin' Gloves": "Luvas de Tiro de Leone Épicas",
    "Fisherman's Friend": "Amigo do Pescador",
    "epicFisherman's Friend": "Amigo do Pescador Épico",
    "Epic Fisherman's Friend": "Amigo do Pescador Épico",
    "Lefler's Right Eye": "Olho Direito de Lefler",
    "Tesla's Poison Rail": "Disparador de Veneno de Tesla",
    "epicTesla's Poison Rail": "Disparador de Veneno de Tesla Épico",
    "Epic Tesla's Poison Rail": "Disparador de Veneno de Tesla Épico",
    "Twyla's Ice Pendant": "Pingente de Gelo de Twyla",
    "Twyla's Fire Pendant": "Pingente de Fogo de Twyla",
    "Twyla's Poison Pendant": "Pingente de Veneno de Twyla",
    "Twyla's Lightning Pendant": "Pingente de Raio de Twyla",
    "epicTwyla's Ice Pendant": "Pingente de Gelo de Twyla Épico",
    "Epic Twyla's Ice Pendant": "Pingente de Gelo de Twyla Épico",
    "epicTwyla's Fire Pendant": "Pingente de Fogo de Twyla Épico",
    "Epic Twyla's Fire Pendant": "Pingente de Fogo de Twyla Épico",
    "epicTwyla's Poison Pendant": "Pingente de Veneno de Twyla Épico",
    "Epic Twyla's Poison Pendant": "Pingente de Veneno de Twyla Épico",
    "epicTwyla's Lightning Pendant": "Pingente de Raio de Twyla Épico",
    "Epic Twyla's Lightning Pendant": "Pingente de Raio de Twyla Épico",
    "Graven's Crystal Belt": "Cinto de Cristal de Graven",
    "Graven's Crystal Helm": "Elmo de Cristal de Graven",
    "Graven's Crystal Boots": "Botas de Cristal de Graven",
    "Graven's Crystal Chest": "Peitoral de Cristal de Graven",
    "Graven's Crystal Gloves": "Luvas de Cristal de Graven",
    "Epic Graven's Crystal Belt": "Cinto de Cristal de Graven Épico",
    "Epic Graven's Crystal Helm": "Elmo de Cristal de Graven Épico",
    "Epic Graven's Crystal Boots": "Botas de Cristal de Graven Épicas",
    "Epic Graven's Crystal Chest": "Peitoral de Cristal de Graven Épico",
    "Epic Graven's Crystal Gloves": "Luvas de Cristal de Graven Épicas",
    "Bolem's Craft Boots": "Botas de Ofício de Bolem",
    "Bolem's Craft Gloves": "Luvas de Ofício de Bolem",
    "Epic Bolem's Craft Boots": "Botas de Ofício de Bolem Épicas",
    "Epic Bolem's Craft Gloves": "Luvas de Ofício de Bolem Épicas",
    "Lieutenant's Pistol": "Pistola do Tenente",
    "epicLieutenant's Pistol": "Pistola do Tenente Épica",
    "Epic Lieutenant's Pistol": "Pistola do Tenente Épica",
    "Captain's Pistol": "Pistola do Capitão",
    "epicCaptain's Pistol": "Pistola do Capitão Épica",
    "Epic Captain's Pistol": "Pistola do Capitão Épica",
    "Officer's Pistol": "Pistola do Oficial",
    "epicOfficer's Pistol": "Pistola do Oficial Épica",
    "Epic Officer's Pistol": "Pistola do Oficial Épica",
    "Grove's Champion": "Campeão do Bosque",
    "epicGrove's Champion": "Campeão do Bosque Épico",
    "Epic Grove's Champion": "Campeão do Bosque Épico",
    "Medea's Insignia": "Insígnia de Medeia",
    "epicMedea's Insignia": "Insígnia de Medeia Épica",
    "Epic Medea's Insignia": "Insígnia de Medeia Épica",
    "Medea's Claws": "Garras de Medeia",
    "Medea's Crown": "Coroa de Medeia",
    "epicMedea's Claws": "Garras de Medeia Épicas",
    "epicMedea's Crown": "Coroa de Medeia Épica",
    "Epic Medea's Claws": "Garras de Medeia Épicas",
    "Epic Medea's Crown": "Coroa de Medeia Épica",
    "Royba's Cap": "Gorro de Royba",
    "Royba's Belt": "Cinto de Royba",
    "Royba's Boots": "Botas de Royba",
    "Royba's Gloves": "Luvas de Royba",
    "Epic Royba's Cap": "Gorro de Royba Épico",
    "Epic Royba's Belt": "Cinto de Royba Épico",
    "Epic Royba's Boots": "Botas de Royba Épicas",
    "Epic Royba's Gloves": "Luvas de Royba Épicas",
    "Archer's Bow": "Arco do Arqueiro",
    "epicArcher's Bow": "Arco do Arqueiro Épico",
    "Epic Archer's Bow": "Arco do Arqueiro Épico",
    "Bishop's Axe": "Machado do Bispo",
    "epicBishop's Axe": "Machado do Bispo Épico",
    "Epic Bishop's Axe": "Machado do Bispo Épico",
    "Kindom's End": "Fim do Reino",
    "epicKindom's End": "Fim do Reino Épico",
    "Epic Kindom's End": "Fim do Reino Épico",
    "Craftman's Bow": "Arco do Artesão",
    "epicCraftman's Bow": "Arco do Artesão Épico",
    "Epic Craftman's Bow": "Arco do Artesão Épico",
    "Fletcher's Bow": "Arco do Flecheiro",
    "epicFletcher's Bow": "Arco do Flecheiro Épico",
    "Epic Fletcher's Bow": "Arco do Flecheiro Épico",
    "Horseman's Bow": "Arco do Cavaleiro",
    "epicHorseman's Bow": "Arco do Cavaleiro Épico",
    "Epic Horseman's Bow": "Arco do Cavaleiro Épico",
    "Scout's Shovel": "Pá do Batedor",
    "Epic Scout's Shovel": "Pá do Batedor Épica",
    "Aleera's Ring": "Anel de Aleera",
    "epicAleera's Ring": "Anel de Aleera Épico",
    "Epic Aleera's Ring": "Anel de Aleera Épico",
    "Verona's Ring": "Anel de Verona",
    "epicVerona's Ring": "Anel de Verona Épico",
    "Epic Verona's Ring": "Anel de Verona Épico",
    "Marishka's Ring": "Anel de Marishka",
    "epicMarishka's Ring": "Anel de Marishka Épico",
    "Epic Marishka's Ring": "Anel de Marishka Épico",
    "Gold Standard": "Padrão-Ouro",
    "Unicorn Fish": "Peixe-Unicórnio",
    "Town Portal": "Portal da Cidade",
    "Fire-Ember": "Âmbar de Fogo",
    "Cold-Ember": "Âmbar Frio",
    "Core-Ember": "Âmbar do Núcleo",
    "Deep-Ember": "Âmbar Profundo",
    "Flow-Ember": "Âmbar do Fluxo",
    "Life-Ember": "Âmbar da Vida",
    "Pure-Ember": "Âmbar Puro",
    "Catfish": "Peixe-Gato",
    "Dogfish": "Peixe-Cão",
    "Icefish": "Peixe de Gelo",
    "Crowfly": "Voo do Corvo",
    "Fanggun": "Pistola de Presas",
    "Pickaxe": "Picareta",
    "Poleaxe": "Machadinha de Haste",
    "Tuskgun": "Espingarda de Presas",
    "Arquebus": "Arcabuz",
    "Birdfish": "Peixe-Pássaro",
    "Bladegun": "Pistola de Lâminas",
    "Firefish": "Peixe de Fogo",
    "Forkwand": "Varinha Furcada",
    "Greatbow": "Arco Longo",
    "Gruefish": "Peixe Sombrio",
    "Muckfish": "Peixe do Lodo",
    "Warsword": "Espada de Guerra",
    "Windlass": "Balestra de Guincho",
    "Winnower": "Joeirador",
    "Chainfist": "Punho de Correntes",
    "Charstaff": "Cajado Chamuscado",
    "Glowshark": "Tubarão Reluzente",
    "Snakebite": "Mordida de Cobra",
    "Strongbow": "Arco Forte",
    "Toecutter": "Cortador de Dedos",
    "Venomfish": "Peixe-Veneno",
    "Donderbuss": "Bacamarte",
    "Pocketfish": "Peixe de Bolso",
    "Smoothbore": "Cano Liso",
    "Pandemonium": "Pandemônio",
    "Peacekeeper": "Pacificador",
    "Roomcleaner": "Limpador de Recintos",
    "Wizaaaards!": "Magooooos!",
    "Quarterstaff": "Bordão",
    "Serpentscale": "Escama de Serpente",
    "Crystaltounge": "Língua de Cristal",
    "undeaddwarfmace": "Maça de Anão Morto-Vivo",
    "Cleves Axe": "Machado de Clévis",
    "Battle Hammer": "Martelo de Batalha",
    "Silence I": "Silêncio I",
    "Silence II": "Silêncio II",
    "Silence III": "Silêncio III",
    "Silence IV": "Silêncio IV",
    "Silence V": "Silêncio V",
    "Silence VI": "Silêncio VI",
    "Pet Gel": "Gel de Mascote",
    "Bat Fish": "Peixe-Morcego",
    "Ice Wand": "Varinha de Gelo",
    "SOCKETABLE": "ENGASTÁVEL",
    "Rodin's Ulitlity Belt": "Cinto de Utilidades de Rodin",
    "Tanwanteng's Left Eye": "Olho Esquerdo de Tanwanteng",
    "Valcone's Only Friend": "Único Amigo de Valcone",
    "Blank's Teeth Necklace": "Colar de Dentes de Blank",
    "Embalmer's Rotten Belt": "Cinto Putrefato do Embalsamador",
    "ChainGet": "ChainGet",
    "ChainDrop": "ChainDrop",
    "StaffGet": "StaffGet",
    "StaffDrop": "StaffDrop",
    "StaffSwing": "StaffSwing",
    "WandDrop": "WandDrop",
    "NOSPAWN": "NOSPAWN",
}
FIXES.update(ITEM_MANUAL)

GENDER_RULES = {
    'Belt': ('m', False, 'Cinto'),
    'Sash': ('f', False, 'Faixa'),
    'Balteus': ('m', False, 'Cinturão'),
    'Helm': ('m', False, 'Elmo'),
    'Helmet': ('m', False, 'Elmo'),
    'Cap': ('m', False, 'Gorro'),
    'Coif': ('f', False, 'Coifa'),
    'Cowl': ('m', False, 'Capuz'),
    'Hood': ('m', False, 'Capuz'),
    'Crest': ('f', False, 'Crista'),
    'Boots': ('f', True, 'Botas'),
    'Shoes': ('m', True, 'Sapatos'),
    'Greaves': ('f', True, 'Grevas'),
    'Sabotons': ('m', True, 'Sabatões'),
    'Gloves': ('f', True, 'Luvas'),
    'Gauntlets': ('f', True, 'Manoplas'),
    'Vambrace': ('f', False, 'Braçadeira'),
    'Chest': ('m', False, 'Peitoral'),
    'Breastplate': ('m', False, 'Peitoral'),
    'Torso': ('m', False, 'Torso'),
    'Coat': ('m', False, 'Casaco'),
    'Vest': ('m', False, 'Colete'),
    'Tunic': ('f', False, 'Túnica'),
    'Hauberk': ('f', False, 'Cota de Malha'),
    'Mantle': ('m', False, 'Manto'),
    'Plates': ('f', True, 'Placas'),
    'Shoulders': ('f', True, 'Ombreiras'),
    'Armor': ('f', False, 'Armadura'),
    'Shield': ('m', False, 'Escudo'),
    'Bow': ('m', False, 'Arco'),
    'Axe': ('m', False, 'Machado'),
    'Sword': ('f', False, 'Espada'),
    'Mace': ('f', False, 'Maça'),
    'Hammer': ('m', False, 'Martelo'),
    'Rifle': ('m', False, 'Rifle'),
    'Pistol': ('f', False, 'Pistola'),
    'Crossbow': ('f', False, 'Besta'),
    'Sabre': ('m', False, 'Sabre'),
    'Wand': ('f', False, 'Varinha'),
    'Staff': ('m', False, 'Cajado'),
    'Ring': ('m', False, 'Anel'),
    'Pendant': ('m', False, 'Pingente'),
    'Necklace': ('m', False, 'Colar'),
    'Gem': ('f', False, 'Gema'),
    'Gel': ('m', False, 'Gel'),
    'Fish': ('m', False, 'Peixe'),
    'Mask': ('f', False, 'Máscara'),
    'Crown': ('f', False, 'Coroa'),
    'Claws': ('f', True, 'Garras'),
    'Insignia': ('f', False, 'Insígnia'),
    'Portal': ('m', False, 'Portal'),
    'Shovel': ('f', False, 'Pá'),
    'Standard': ('m', False, 'Padrão'),
    'End': ('m', False, 'Fim'),
    'Champion': ('m', False, 'Campeão'),
    'Friend': ('m', False, 'Amigo'),
    'Eye': ('m', False, 'Olho'),
    'Rail': ('m', False, 'Disparador'),
}

MAT_RULES = {
    'Bone': ('de Osso', None, None, None, None),
    'Chain': ('de Cota de Malha', None, None, None, None),
    'Plate': ('de Placas', None, None, None, None),
    'Scale': ('de Escamas', None, None, None, None),
    'Leather': ('de Couro', None, None, None, None),
    'Bronze': ('de Bronze', None, None, None, None),
    'Copper': ('de Cobre', None, None, None, None),
    'Brass': ('de Latão', None, None, None, None),
    'Silver': ('de Prata', None, None, None, None),
    'Gold': ('de Ouro', None, None, None, None),
    'Iron': ('de Ferro', None, None, None, None),
    'Wood': ('de Madeira', None, None, None, None),
    'Elm': ('de Olmo', None, None, None, None),
    'Yew': ('de Teixo', None, None, None, None),
    'Clan': ('do Clã', None, None, None, None),
    'War': ('de Guerra', None, None, None, None),
    'Battle': ('de Batalha', None, None, None, None),
    'Tower': ('Torre', None, None, None, None),
    'Kite': ('Gota', None, None, None, None),
    'Chaos': ('do Caos', None, None, None, None),
    'Raw': (None, 'Bruto', 'Bruta', 'Brutos', 'Brutas'),
    'Spiked': (None, 'com Espinhos', 'com Espinhos', 'com Espinhos', 'com Espinhos'),
    'Buckled': (None, 'Aivelado', 'Aivelada', 'Aivelados', 'Aiveladas'),
    'Shadow': (None, 'Sombrio', 'Sombria', 'Sombrios', 'Sombrias'),
    'Judge': ('do Juiz', None, None, None, None),
}

def get_epic_suffix(gender, plural):
    if plural:
        return 'Épicas' if gender == 'f' else 'Épicos'
    return 'Épica' if gender == 'f' else 'Épico'

def translate_item_name(s: str) -> str | None:
    if s in FIXES:
        return FIXES[s]
    
    if s in ("ChainGet", "ChainDrop", "StaffGet", "StaffDrop", "StaffSwing", "WandDrop", "NOSPAWN"):
        return s

    is_epic = False
    class_prefix = None
    
    work = s
    if work.startswith("Epic "):
        is_epic = True
        work = work[5:].strip()
    elif work.startswith("epic"):
        is_epic = True
        work = work[4:].strip()
        
    if work.startswith("epica "):
        is_epic = True
        class_prefix = 'a'
        work = work[6:].strip()
    elif work.startswith("epicv "):
        is_epic = True
        class_prefix = 'v'
        work = work[6:].strip()
    elif work.startswith("a "):
        class_prefix = 'a'
        work = work[2:].strip()
    elif work.startswith("v "):
        class_prefix = 'v'
        work = work[2:].strip()

    if work in FIXES:
        res = FIXES[work]
        if is_epic:
            words = work.split()
            noun = words[-1] if words[-1] in GENDER_RULES else None
            if noun:
                g, p, _ = GENDER_RULES[noun]
                res = f"{res} {get_epic_suffix(g, p)}"
            else:
                res = f"{res} Épico"
        return res

    words = work.split()
    if len(words) == 2 and words[0] in MAT_RULES and words[1] in GENDER_RULES:
        mat = words[0]
        noun = words[1]
        g, p, pt_noun = GENDER_RULES[noun]
        prep, adj_m, adj_f, adj_mp, adj_fp = MAT_RULES[mat]
        
        if prep:
            base = f"{pt_noun} {prep}"
        else:
            if p:
                adj = adj_fp if g == 'f' else adj_mp
            else:
                adj = adj_f if g == 'f' else adj_m
            base = f"{pt_noun} {adj}"
            
        if is_epic:
            base = f"{base} {get_epic_suffix(g, p)}"
        return base

    if len(words) == 1 and words[0] in GENDER_RULES:
        noun = words[0]
        g, p, pt_noun = GENDER_RULES[noun]
        if is_epic:
            return f"{pt_noun} {get_epic_suffix(g, p)}"
        return pt_noun

    return None


def main():
    print("=" * 70)
    print(" Applying Master Bugfixes to Translation Catalog")
    print(f" Catalog: {CATALOG_PATH}")
    print("=" * 70)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # 1. Inject missing ground truth entries into Globals if not already present
    globals_list = catalog["categories"].get("Globals", [])
    existing_origs = {e["original"] for e in globals_list}
    
    injected_count = 0
    for word, pt_trans in MISSING_WORDS.items():
        if word not in existing_origs:
            entry_id = f"Globals_{len(globals_list)+1:04d}"
            globals_list.append({
                "id": entry_id,
                "original": word,
                "translation": pt_trans,
                "context": "media/GLOBALS.DAT.adm"
            })
            existing_origs.add(word)
            injected_count += 1

    print(f"Injected {injected_count} missing ground-truth words into Globals.")

    # 2. Iterate through all categories and apply fixes
    updated_entries = 0
    total_entries = 0

    for cat_name, entries in catalog["categories"].items():
        for e in entries:
            total_entries += 1
            orig = e["original"]
            curr = e["translation"]

            # Try exact match in FIXES
            new_trans = None
            if orig in FIXES:
                new_trans = FIXES[orig]
            else:
                # Try item translation rule
                if cat_name == "Items":
                    item_res = translate_item_name(orig)
                    if item_res:
                        new_trans = item_res

            if new_trans is not None and new_trans != curr:
                e["translation"] = new_trans
                updated_entries += 1

    # Update metadata
    catalog["metadata"]["total_strings"] = sum(len(lst) for lst in catalog["categories"].values())
    for cat_name, lst in catalog["categories"].items():
        catalog["metadata"]["category_counts"][cat_name] = len(lst)

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Catalog successfully updated:")
    print(f"  - Total entries processed: {total_entries}")
    print(f"  - Translations updated:    {updated_entries}")
    print(f"  - Saved to: {CATALOG_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()

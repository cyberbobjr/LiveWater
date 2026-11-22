"""Documentation images for the README, the wiki and the Steam Workshop page.

    python tools/make_doc_images.py [LANG ...]      (default: all languages)

Writes docs/images/diagrams/<name>_<lang>.png: recipe_book (craft cards + dismantling card, 640 px wide for the
Steam page), equipment (board of the parts), diagram (how it works). Same visual style as LiveWire's
tools/make_doc_images.py. Only Pillow is needed.
Recipes are read from the recipe scripts (no hand-written recipe table). Item names come from the mod's translations
(mod items) and the game's translations (vanilla items, skill names, vanilla places such as a well); figures come
from the wiki (docs/wiki/en/01-getting-started.md). Icons are collected into docs/images/icons (inventory icons of
the mod, vanilla icons read from the game's texture packs) and docs/images/icons/tiles (the mod's tile sprites).
"""
import io
import json
import os
import re
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "images", "diagrams")
ICONS = os.path.join(ROOT, "docs", "images", "icons")
TILES = os.path.join(ICONS, "tiles")
MOD = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater")
MEDIA = os.path.join(MOD, "42.21", "media")
SCRIPTS = os.path.join(MEDIA, "scripts")
RECIPES = os.path.join(SCRIPTS, "LWT_recipes.txt")
DISMANTLE = os.path.join(SCRIPTS, "LWT_dismantle.txt")
ITEM_SCRIPTS = (os.path.join(SCRIPTS, "LWT_items.txt"), os.path.join(SCRIPTS, "LWT_moveables.txt"))
MOD_TEX = os.path.join(MEDIA, "textures")
MOD_TR = os.path.join(MEDIA, "lua", "shared", "Translate")
TILE_PACK = os.path.join(MOD, "common", "media", "texturepacks", "batman_livewater_01.pack")
GAME_MEDIA = os.environ.get("PZ_MEDIA", r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media")
GAME_TR = os.environ.get("PZ_TRANSLATE", os.path.join(GAME_MEDIA, "lua", "shared", "Translate"))
GAME_ITEMS = os.path.join(GAME_MEDIA, "scripts", "generated", "items")
FONTS = os.environ.get("FONTS_DIR", r"C:\Windows\Fonts")
LANGS = ["EN", "FR", "DE", "ES", "PTBR", "PT", "RU", "CN", "JP", "KO", "TR"]

BG = (251, 247, 239)
CARD = (255, 255, 255)
LINE = (214, 207, 196)
INK = (31, 42, 51)
MUTED = (107, 114, 128)
ACCENT = (184, 98, 42)
ACCENT_BG = (243, 225, 211)
GREEN = (62, 154, 85)
GREEN_BG = (227, 241, 228)
BLUE = (46, 108, 176)
BLUE_BG = (224, 235, 247)
GREY = (150, 150, 150)

FONT_FILES = {
    "CN": ("msyh.ttc", "msyhbd.ttc"),
    "JP": ("YuGothM.ttc", "YuGothB.ttc"),
    "KO": ("malgun.ttf", "malgunbd.ttf"),
}
# Languages wrapped character by character (no spaces between words), and their list separator.
NO_SPACE = ("CN", "JP")
LIST_SEP = {"CN": "、", "JP": "、"}


def font(lang, size, bold=False):
    reg, bld = FONT_FILES.get(lang, ("segoeui.ttf", "segoeuib.ttf"))
    return ImageFont.truetype(os.path.join(FONTS, bld if bold else reg), size)


# --- Labels -------------------------------------------------------------------------------------
# Short UI strings of the images. Item, recipe and skill names are not here: they come from the translations.
# fig_<part>: the role line of each part on the equipment board (figures from the wiki).
STRINGS = {
    "EN": {
        "recipes": "RECIPES", "tools": "Tools (kept)", "no_level": "no level", "level": "%s %d",
        "dis_title": "DISMANTLING", "dis_note": "Never more than the part cost, scrap only",
        "fig_Pipe": "one per square, joins its neighbours on its own",
        "fig_PondPump": "50 L / 10 min · needs power (generator, grid or LiveWire)",
        "fig_Valve": "closed: no water to anything after it",
        "fig_FlowMeter": "litres of the last 10 min and total",
        "fig_HouseInlet": "feeds the house: 20 squares, every floor, 2 basement levels",
        "fig_WaterFilter": "cleans about 500 L, fitted in the house inlet",
        "fig_Sprinkler": "10 L / 10 min on 5 × 5 squares",
        "fig_SprinklerAuto": "opens every 6 h for 30 min · 5 W",
        "fig_DripLine": "0.5 L per square / 10 min · silent",
        "fig_BarrelFitting": "fills a barrel, rain collector or feeding trough",
        "d_title": "HOW IT WORKS", "d_source": "SOURCE", "d_natural": "River, lake, pond", "d_barrel": "Barrel",
        "d_pump_fig": "50 L every 10 minutes", "d_power": "power: generator,\ngrid or LiveWire",
        "d_pipes": "PIPES", "d_pipes_note": "one per square,\nall on one level",
        "d_valve": "+ %s:\ncloses the line",
        "d_outlets": "OUTLETS", "d_house": "Sinks, bathtubs, showers,\ntoilets, washing machines",
        "d_with": "+ %s", "d_crops": "Crops", "d_fill": "%s, %s, %s",
        "d_rule": "One liquid per network: the first pump sets it (water or gasoline).",
    },
    "FR": {
        "recipes": "RECETTES", "tools": "Outils (conservés)", "no_level": "sans niveau", "level": "%s %d",
        "dis_title": "DÉMONTAGE", "dis_note": "Jamais plus que le coût de la pièce, rebuts seulement",
        "fig_Pipe": "un par case, se raccorde seul à ses voisins",
        "fig_PondPump": "50 L / 10 min · courant requis (groupe, réseau ou LiveWire)",
        "fig_Valve": "fermée : plus d'eau après elle",
        "fig_FlowMeter": "litres des 10 dernières min et total",
        "fig_HouseInlet": "alimente la maison : 20 cases, tous les étages, 2 niveaux de sous-sol",
        "fig_WaterFilter": "nettoie environ 500 L, posée dans l'arrivée d'eau",
        "fig_Sprinkler": "10 L / 10 min sur 5 × 5 cases",
        "fig_SprinklerAuto": "s'ouvre toutes les 6 h pendant 30 min · 5 W",
        "fig_DripLine": "0,5 L par case / 10 min · silencieuse",
        "fig_BarrelFitting": "remplit un baril, un collecteur de pluie ou une mangeoire",
        "d_title": "COMMENT ÇA MARCHE", "d_source": "SOURCE", "d_natural": "Rivière, lac, étang", "d_barrel": "Baril",
        "d_pump_fig": "50 L toutes les 10 minutes", "d_power": "courant : groupe électrogène,\nréseau ou LiveWire",
        "d_pipes": "TUYAUX", "d_pipes_note": "un par case,\ntous au même niveau",
        "d_valve": "+ %s :\nferme la ligne",
        "d_outlets": "SORTIES", "d_house": "Éviers, baignoires, douches,\ntoilettes, lave-linge",
        "d_with": "+ %s", "d_crops": "Cultures", "d_fill": "%s, %s, %s",
        "d_rule": "Un seul liquide par réseau : la première pompe le fixe (eau ou essence).",
    },
    "DE": {
        "recipes": "REZEPTE", "tools": "Werkzeuge (bleiben)", "no_level": "ohne Stufe", "level": "%s %d",
        "dis_title": "ZERLEGEN", "dis_note": "Nie mehr als die Teilkosten, nur Schrott",
        "fig_Pipe": "eins pro Feld, verbindet sich selbst mit Nachbarn",
        "fig_PondPump": "50 L / 10 Min. · braucht Strom (Generator, Netz oder LiveWire)",
        "fig_Valve": "zu: kein Wasser mehr dahinter",
        "fig_FlowMeter": "Liter der letzten 10 Min. und gesamt",
        "fig_HouseInlet": "versorgt das Haus: 20 Felder, alle Etagen, 2 Kellerebenen",
        "fig_WaterFilter": "reinigt etwa 500 L, sitzt im Hauswassereinlass",
        "fig_Sprinkler": "10 L / 10 Min. auf 5 × 5 Feldern",
        "fig_SprinklerAuto": "öffnet alle 6 Std. für 30 Min. · 5 W",
        "fig_DripLine": "0,5 L pro Feld / 10 Min. · lautlos",
        "fig_BarrelFitting": "füllt ein Fass, einen Regenfänger oder einen Futtertrog",
        "d_title": "SO FUNKTIONIERT ES", "d_source": "QUELLE", "d_natural": "Fluss, See, Teich", "d_barrel": "Fass",
        "d_pump_fig": "50 L alle 10 Minuten", "d_power": "Strom: Generator,\nNetz oder LiveWire",
        "d_pipes": "ROHRE", "d_pipes_note": "eins pro Feld,\nalle auf einer Ebene",
        "d_valve": "+ %s:\nsperrt die Leitung",
        "d_outlets": "VERBRAUCHER", "d_house": "Spülen, Badewannen, Duschen,\nToiletten, Waschmaschinen",
        "d_with": "+ %s", "d_crops": "Pflanzen", "d_fill": "%s, %s, %s",
        "d_rule": "Eine Flüssigkeit pro Netz: die erste Pumpe legt sie fest (Wasser oder Benzin).",
    },
    "ES": {
        "recipes": "RECETAS", "tools": "Herramientas (se conservan)", "no_level": "sin nivel", "level": "%s %d",
        "dis_title": "DESMONTAJE", "dis_note": "Nunca más de lo que costó la pieza, solo chatarra",
        "fig_Pipe": "uno por casilla, se une solo a sus vecinos",
        "fig_PondPump": "50 L / 10 min · necesita corriente (generador, red o LiveWire)",
        "fig_Valve": "cerrada: nada de agua después",
        "fig_FlowMeter": "litros de los últimos 10 min y total",
        "fig_HouseInlet": "abastece la casa: 20 casillas, todas las plantas, 2 sótanos",
        "fig_WaterFilter": "limpia unos 500 L, va en la entrada de agua",
        "fig_Sprinkler": "10 L / 10 min en 5 × 5 casillas",
        "fig_SprinklerAuto": "se abre cada 6 h durante 30 min · 5 W",
        "fig_DripLine": "0,5 L por casilla / 10 min · silencioso",
        "fig_BarrelFitting": "llena un barril, un colector de lluvia o un comedero",
        "d_title": "CÓMO FUNCIONA", "d_source": "FUENTE", "d_natural": "Río, lago, estanque", "d_barrel": "Barril",
        "d_pump_fig": "50 L cada 10 minutos", "d_power": "corriente: generador,\nred o LiveWire",
        "d_pipes": "TUBERÍAS", "d_pipes_note": "una por casilla,\ntodas en un nivel",
        "d_valve": "+ %s:\ncierra la línea",
        "d_outlets": "SALIDAS", "d_house": "Fregaderos, bañeras, duchas,\ninodoros, lavadoras",
        "d_with": "+ %s", "d_crops": "Cultivos", "d_fill": "%s, %s, %s",
        "d_rule": "Un solo líquido por red: la primera bomba lo fija (agua o gasolina).",
    },
    "PTBR": {
        "recipes": "RECEITAS", "tools": "Ferramentas (mantidas)", "no_level": "sem nível", "level": "%s %d",
        "dis_title": "DESMONTAGEM", "dis_note": "Nunca mais do que a peça custou, só sucata",
        "fig_Pipe": "um por quadrado, liga-se sozinho aos vizinhos",
        "fig_PondPump": "50 L / 10 min · precisa de energia (gerador, rede ou LiveWire)",
        "fig_Valve": "fechado: sem água depois dele",
        "fig_FlowMeter": "litros dos últimos 10 min e total",
        "fig_HouseInlet": "abastece a casa: 20 quadrados, todos os andares, 2 subsolos",
        "fig_WaterFilter": "limpa cerca de 500 L, vai na entrada de água",
        "fig_Sprinkler": "10 L / 10 min em 5 × 5 quadrados",
        "fig_SprinklerAuto": "abre a cada 6 h por 30 min · 5 W",
        "fig_DripLine": "0,5 L por quadrado / 10 min · silenciosa",
        "fig_BarrelFitting": "enche um barril, um coletor de chuva ou um cocho",
        "d_title": "COMO FUNCIONA", "d_source": "FONTE", "d_natural": "Rio, lago, lagoa", "d_barrel": "Barril",
        "d_pump_fig": "50 L a cada 10 minutos", "d_power": "energia: gerador,\nrede ou LiveWire",
        "d_pipes": "CANOS", "d_pipes_note": "um por quadrado,\ntodos num só nível",
        "d_valve": "+ %s:\nfecha a linha",
        "d_outlets": "SAÍDAS", "d_house": "Pias, banheiras, chuveiros,\nvasos sanitários, máquinas de lavar",
        "d_with": "+ %s", "d_crops": "Plantações", "d_fill": "%s, %s, %s",
        "d_rule": "Um só líquido por rede: a primeira bomba define (água ou gasolina).",
    },
    "PT": {
        "recipes": "RECEITAS", "tools": "Ferramentas (mantidas)", "no_level": "sem nível", "level": "%s %d",
        "dis_title": "DESMONTAGEM", "dis_note": "Nunca mais do que a peça custou, só sucata",
        "fig_Pipe": "um por quadrícula, liga-se sozinho aos vizinhos",
        "fig_PondPump": "50 L / 10 min · precisa de energia (gerador, rede ou LiveWire)",
        "fig_Valve": "fechada: sem água a seguir",
        "fig_FlowMeter": "litros dos últimos 10 min e total",
        "fig_HouseInlet": "abastece a casa: 20 quadrículas, todos os pisos, 2 caves",
        "fig_WaterFilter": "limpa cerca de 500 L, vai na entrada de água",
        "fig_Sprinkler": "10 L / 10 min em 5 × 5 quadrículas",
        "fig_SprinklerAuto": "abre a cada 6 h durante 30 min · 5 W",
        "fig_DripLine": "0,5 L por quadrícula / 10 min · silenciosa",
        "fig_BarrelFitting": "enche um barril, uma cisterna ou um comedouro",
        "d_title": "COMO FUNCIONA", "d_source": "FONTE", "d_natural": "Rio, lago, charco", "d_barrel": "Barril",
        "d_pump_fig": "50 L a cada 10 minutos", "d_power": "energia: gerador,\nrede ou LiveWire",
        "d_pipes": "CANOS", "d_pipes_note": "um por quadrícula,\ntodos no mesmo nível",
        "d_valve": "+ %s:\nfecha a linha",
        "d_outlets": "SAÍDAS", "d_house": "Lava-loiças, banheiras, chuveiros,\nsanitas, máquinas de lavar",
        "d_with": "+ %s", "d_crops": "Culturas", "d_fill": "%s, %s, %s",
        "d_rule": "Um só líquido por rede: a primeira bomba define-o (água ou gasolina).",
    },
    "RU": {
        "recipes": "РЕЦЕПТЫ", "tools": "Инструменты (остаются)", "no_level": "без уровня", "level": "%s %d",
        "dis_title": "РАЗБОРКА", "dis_note": "Не больше стоимости детали, только лом",
        "fig_Pipe": "одна на клетку, сама соединяется с соседями",
        "fig_PondPump": "50 л / 10 мин · нужен ток (генератор, сеть или LiveWire)",
        "fig_Valve": "закрыт: дальше воды нет",
        "fig_FlowMeter": "литры за последние 10 мин и всего",
        "fig_HouseInlet": "снабжает дом: 20 клеток, все этажи, 2 уровня подвала",
        "fig_WaterFilter": "очищает около 500 л, ставится во ввод",
        "fig_Sprinkler": "10 л / 10 мин на 5 × 5 клеток",
        "fig_SprinklerAuto": "открывается каждые 6 ч на 30 мин · 5 Вт",
        "fig_DripLine": "0,5 л на клетку / 10 мин · бесшумная",
        "fig_BarrelFitting": "наполняет бочку, сборщик дождя или кормушку",
        "d_title": "КАК ЭТО РАБОТАЕТ", "d_source": "ИСТОЧНИК", "d_natural": "Река, озеро, пруд", "d_barrel": "Бочка",
        "d_pump_fig": "50 л каждые 10 минут", "d_power": "ток: генератор,\nсеть или LiveWire",
        "d_pipes": "ТРУБЫ", "d_pipes_note": "одна на клетку,\nвсе на одном уровне",
        "d_valve": "+ %s:\nперекрывает линию",
        "d_outlets": "ПОТРЕБИТЕЛИ", "d_house": "Раковины, ванны, души,\nунитазы, стиральные машины",
        "d_with": "+ %s", "d_crops": "Грядки", "d_fill": "%s, %s, %s",
        "d_rule": "Одна жидкость на сеть: её задаёт первый насос (вода или бензин).",
    },
    "CN": {
        "recipes": "配方", "tools": "工具（保留）", "no_level": "无等级", "level": "%s %d",
        "dis_title": "拆解", "dis_note": "返还不超过部件成本，只有废料",
        "fig_Pipe": "每格一根，自动与相邻管道连接",
        "fig_PondPump": "每 10 分钟 50 L · 需要供电（发电机、电网或 LiveWire）",
        "fig_Valve": "关闭后，后方不再有水",
        "fig_FlowMeter": "最近 10 分钟的升数和总量",
        "fig_HouseInlet": "为房屋供水：20 格，所有楼层，地下 2 层",
        "fig_WaterFilter": "可净化约 500 L，装在房屋进水口",
        "fig_Sprinkler": "每 10 分钟 10 L，覆盖 5 × 5 格",
        "fig_SprinklerAuto": "每 6 小时开启 30 分钟 · 5 W",
        "fig_DripLine": "每格每 10 分钟 0.5 L · 无声",
        "fig_BarrelFitting": "灌满桶、雨水收集器或喂食槽",
        "d_title": "工作原理", "d_source": "水源", "d_natural": "河、湖、池塘", "d_barrel": "桶",
        "d_pump_fig": "每 10 分钟 50 L", "d_power": "供电：发电机、\n电网或 LiveWire",
        "d_pipes": "管道", "d_pipes_note": "每格一根，\n全部在同一层",
        "d_valve": "+ %s：\n关闭管线",
        "d_outlets": "出水端", "d_house": "水槽、浴缸、淋浴、\n马桶、洗衣机",
        "d_with": "+ %s", "d_crops": "作物", "d_fill": "%s、%s、%s",
        "d_rule": "每个管网只有一种液体：由第一台水泵决定（水或汽油）。",
    },
    "JP": {
        "recipes": "レシピ", "tools": "道具（消費しない）", "no_level": "レベル不要", "level": "%s %d",
        "dis_title": "分解", "dis_note": "部品のコストを超えては戻らず、スクラップのみ",
        "fig_Pipe": "1マスに1本、\n隣と自動でつながる",
        "fig_PondPump": "10分ごとに50 L · 電力が必要（発電機、送電網、LiveWire）",
        "fig_Valve": "閉じると先に水が流れない",
        "fig_FlowMeter": "直近10分のリットル数と合計",
        "fig_HouseInlet": "家に給水：20マス、上の全階、地下2階",
        "fig_WaterFilter": "約500 Lを浄化、家の給水口に装着",
        "fig_Sprinkler": "10分ごとに10 L、5 × 5マス",
        "fig_SprinklerAuto": "6時間ごとに30分開く · 5 W",
        "fig_DripLine": "1マスあたり10分で0.5 L · 無音",
        "fig_BarrelFitting": "樽、雨樽、給餌桶を満たす",
        "d_title": "しくみ", "d_source": "水源", "d_natural": "川、湖、池", "d_barrel": "樽",
        "d_pump_fig": "10分ごとに50 L", "d_power": "電力：発電機、\n送電網、LiveWire",
        "d_pipes": "パイプ", "d_pipes_note": "1マスに1本、\nすべて同じ階",
        "d_valve": "+ %s：\nラインを止める",
        "d_outlets": "出口", "d_house": "シンク、浴槽、シャワー、\nトイレ、洗濯機",
        "d_with": "+ %s", "d_crops": "作物", "d_fill": "%s、%s、%s",
        "d_rule": "1つの配管網に液体は1種類：最初のポンプで決まる（水またはガソリン）。",
    },
    "KO": {
        "recipes": "레시피", "tools": "도구 (유지)", "no_level": "레벨 없음", "level": "%s %d",
        "dis_title": "분해", "dis_note": "부품 비용 이상은 돌려받지 못함, 고철만",
        "fig_Pipe": "한 칸에 하나, 이웃과 자동 연결",
        "fig_PondPump": "10분마다 50 L · 전력 필요 (발전기, 전력망, LiveWire)",
        "fig_Valve": "잠그면 그 뒤로 물이 가지 않음",
        "fig_FlowMeter": "최근 10분 리터 수와 합계",
        "fig_HouseInlet": "집에 급수: 20칸, 위 모든 층, 지하 2층",
        "fig_WaterFilter": "약 500 L 정화, 집 급수구에 장착",
        "fig_Sprinkler": "10분마다 10 L, 5 × 5칸",
        "fig_SprinklerAuto": "6시간마다 30분 열림 · 5 W",
        "fig_DripLine": "칸당 10분에 0.5 L · 무소음",
        "fig_BarrelFitting": "통, 빗물받이, 여물통을 채움",
        "d_title": "작동 방식", "d_source": "수원", "d_natural": "강, 호수, 연못", "d_barrel": "통",
        "d_pump_fig": "10분마다 50 L", "d_power": "전력: 발전기,\n전력망 또는 LiveWire",
        "d_pipes": "파이프", "d_pipes_note": "한 칸에 하나,\n모두 같은 층",
        "d_valve": "+ %s:\n라인 차단",
        "d_outlets": "출수구", "d_house": "싱크대, 욕조, 샤워기,\n변기, 세탁기",
        "d_with": "+ %s", "d_crops": "작물", "d_fill": "%s, %s, %s",
        "d_rule": "배관망 하나에 액체 하나: 첫 번째 펌프가 정함 (물 또는 휘발유).",
    },
    "TR": {
        "recipes": "TARİFLER", "tools": "Aletler (kalır)", "no_level": "seviye yok", "level": "%s %d",
        "dis_title": "SÖKME", "dis_note": "Parçanın maliyetinden fazlası asla, yalnızca hurda",
        "fig_Pipe": "kare başına bir, komşularına kendiliğinden bağlanır",
        "fig_PondPump": "10 dk'da 50 L · elektrik gerekir (jeneratör, şebeke veya LiveWire)",
        "fig_Valve": "kapalıyken arkasına su gitmez",
        "fig_FlowMeter": "son 10 dk'nın litresi ve toplam",
        "fig_HouseInlet": "evi besler: 20 kare, tüm üst katlar, 2 bodrum katı",
        "fig_WaterFilter": "yaklaşık 500 L temizler, ev su girişine takılır",
        "fig_Sprinkler": "10 dk'da 10 L, 5 × 5 kare",
        "fig_SprinklerAuto": "her 6 saatte 30 dk açılır · 5 W",
        "fig_DripLine": "kare başına 10 dk'da 0,5 L · sessiz",
        "fig_BarrelFitting": "varil, yağmur toplayıcı veya yemlik doldurur",
        "d_title": "NASIL ÇALIŞIR", "d_source": "KAYNAK", "d_natural": "Nehir, göl, gölet", "d_barrel": "Varil",
        "d_pump_fig": "10 dakikada 50 L", "d_power": "elektrik: jeneratör,\nşebeke veya LiveWire",
        "d_pipes": "BORULAR", "d_pipes_note": "kare başına bir,\nhepsi aynı katta",
        "d_valve": "+ %s:\nhattı kapatır",
        "d_outlets": "ÇIKIŞLAR", "d_house": "Lavabolar, küvetler, duşlar,\ntuvaletler, çamaşır makineleri",
        "d_with": "+ %s", "d_crops": "Ekinler", "d_fill": "%s, %s, %s",
        "d_rule": "Ağ başına tek sıvı: ilk pompa belirler (su veya benzin).",
    },
}
# Vanilla places and containers named with the game's own words (Translate/<LANG>/*.json of the game).
GAME_TERMS = {"well": "Fluid_Container_Well", "collector": "Fluid_Container_Collector",
              "trough": "ContextMenu_FeedingTrough", "gaspump": "IGUI_GasPump"}

# --- Drawing helpers ----------------------------------------------------------------------------


def text(d, xy, s, f, fill=INK, anchor="la", spacing=4, align="left"):
    d.multiline_text(xy, s, font=f, fill=fill, anchor=anchor, spacing=spacing, align=align)


def tsize(d, s, f, spacing=4):
    b = d.multiline_textbbox((0, 0), s, font=f, spacing=spacing)
    return b[2] - b[0], b[3] - b[1]


def fit(d, s, lang, size, width, bold=False):
    """Largest font up to size whose widest line fits in width."""
    while size > 10:
        f = font(lang, size, bold)
        if tsize(d, s, f)[0] <= width:
            return f
        size -= 1
    return font(lang, size, bold)


# CN / JP line breaking rules: these never start a line, those never end one.
NO_LINE_START = set("\u3001\u3002\uff0c\uff0e\u30fb\uff1a\uff1b\uff01\uff1f\uff09\u300d\u300f\u30fc"
                    "\u30a1\u30a3\u30a5\u30a7\u30a9\u30c3\u30e3\u30e5\u30e7\u3041\u3043\u3045\u3047\u3049\u3063"
                    "\u3083\u3085\u3087)")
NO_LINE_END = set("\uff08\u300c\u300e(")


def fit_or_wrap(d, s, lang, size, width, min_size, bold=False):
    """(text, font): one line shrunk down to min_size, else two balanced lines at min_size."""
    f = fit(d, s, lang, size, width, bold)
    if f.size >= min_size:
        return s, f
    f = font(lang, min_size, bold)
    return wrap(d, s, f, width, lang), f


def wrap_lines(d, s, f, width, lang):
    """Greedy wrap of one paragraph: by words, or for CN / JP by characters (runs of Latin letters and digits
    kept whole) with their line breaking rules."""
    # A number stays with the word after it ("5 W", "20 squares"): the space becomes a no-break space.
    s = re.sub(r"(?<=\d) (?=\S)", "\u00a0", s)
    if lang in NO_SPACE:
        units, sep = re.findall(r"[A-Za-z0-9.,\u00a0\u00d7]+|.", s), ""
    else:
        units, sep = s.split(" "), " "
    lines, cur = [], ""
    for u in units:
        cand = cur + sep + u if cur else u
        if cur and tsize(d, cand, f)[0] > width and u not in NO_LINE_START:
            carry = ""
            while cur and cur[-1] in NO_LINE_END:
                cur, carry = cur[:-1], cur[-1] + carry
            lines.append(cur.rstrip())
            cur = (carry + u).lstrip()
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def wrap(d, s, f, width, lang):
    """Balanced wrap: as few lines as the greedy wrap, with the narrowest width that keeps that count (no orphan
    word or character on the last line)."""
    n = len(wrap_lines(d, s, f, width, lang))
    best = width
    w = width - 4
    while n > 1 and w > width / 2 and len(wrap_lines(d, s, f, w, lang)) == n:
        best, w = w, w - 4
    return "\n".join(wrap_lines(d, s, f, best, lang))


def bottom(d, xy, s, f, spacing=4):
    """Lowest pixel row of a text drawn at xy (anchor "la")."""
    return d.multiline_textbbox(xy, s, font=f, spacing=spacing)[3]


def arrow(d, x0, y0, x1, y1, w=5, head=16, fill=ACCENT):
    """Horizontal (x1 > x0) or downward vertical (y1 > y0) arrow."""
    if x1 > x0:
        d.line((x0, y0, x1 - head, y1), fill=fill, width=w)
        d.polygon([(x1, y1), (x1 - head, y1 - head * 0.6), (x1 - head, y1 + head * 0.6)], fill=fill)
    else:
        d.line((x0, y0, x1, y1 - head), fill=fill, width=w)
        d.polygon([(x1, y1), (x1 - head * 0.6, y1 - head), (x1 + head * 0.6, y1 - head)], fill=fill)


def caps(s, lang):
    """Capitals with the Turkish dotted / dotless i (i -> İ, ı -> I)."""
    if lang == "TR":
        s = s.replace("i", "İ").replace("ı", "I")
    return s.upper()


def save(im, name, lang):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "%s_%s.png" % (name, lang.lower()))
    im.save(p, optimize=True)
    print("wrote", os.path.relpath(p, ROOT), im.size)


# --- Recipes, read from the recipe scripts ------------------------------------------------------

# A tag input is shown as a representative vanilla item that carries the tag (checked in the game's item scripts).
TAG_ITEM = {"metalsaw": "Base.Saw", "screwdriver": "Base.Screwdriver", "wrench": "Base.Wrench",
            "pipewrench": "Base.PipeWrench", "sharpknife": "Base.KitchenKnife", "charcoal": "Base.Charcoal"}
INPUT_LINE = re.compile(r"^item (\d+) (?:tags\[([^\]]+)\]|\[([^\]]+)\])(.*)$")
OUTPUT_LINE = re.compile(r"^item (\d+) ([A-Za-z_][\w.]*)$")
SKILL = re.compile(r"SkillRequired\s*=\s*(\w+):(\d+)")


def short(full):
    """Icon / board key of a full item type: "Base.Mov_LiveWater_Pipe" -> Pipe, "LiveWater.WaterFilter" -> WaterFilter."""
    name = full.split(".", 1)[1]
    return name[len("Mov_LiveWater_"):] if name.startswith("Mov_LiveWater_") else name


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def section_lines(src):
    for line in src.split("}")[0].splitlines():
        line = line.strip().rstrip(",")
        if line.startswith("item "):
            yield line


def parse_recipes(path):
    """Every craftRecipe block of a recipe script: name, skill (perk, level) or None, inputs, tools, outputs.
    Items are full types; a tag input becomes its representative item; a kept input is a tool (alternatives of a
    tag list are all kept, the first one first)."""
    with open(path, encoding="utf-8-sig") as f:
        src = strip_comments(f.read())
    recipes = []
    for block in re.split(r"\bcraftRecipe\s+", src)[1:]:
        name = re.match(r"\w+", block).group(0)
        skill = SKILL.search(block)
        _, _, rest = block.partition("inputs")
        ins_src, _, outs_src = rest.partition("outputs")
        ins, tools, outs = [], [], []
        for line in section_lines(ins_src):
            m = INPUT_LINE.match(line)
            if not m:
                raise ValueError("%s: unparsed input line %r" % (name, line))
            qty, tags, alts, flags = int(m.group(1)), m.group(2), m.group(3), m.group(4)
            if tags:
                fulls = [TAG_ITEM[t.split(":", 1)[1]] for t in tags.split(";")]
            elif ";" in alts:
                raise ValueError("%s: unexpected alternatives %s" % (name, alts))
            else:
                fulls = [alts]
            if "mode:keep" in flags:
                tools.append(fulls)
            else:
                ins.append((qty, fulls[0]))
        for line in section_lines(outs_src):
            m = OUTPUT_LINE.match(line)
            if not m:
                raise ValueError("%s: unparsed output line %r" % (name, line))
            outs.append((int(m.group(1)), m.group(2)))
        if not ins or not outs:
            raise ValueError("%s: no inputs or outputs parsed" % name)
        recipes.append({"name": name, "skill": (skill.group(1), int(skill.group(2))) if skill else None,
                        "ins": ins, "tools": tools, "outs": outs})
    return recipes


CRAFTS = parse_recipes(RECIPES)
DISMANTLES = parse_recipes(DISMANTLE)
if any(r["skill"] for r in DISMANTLES):
    raise ValueError("a dismantling recipe needs a level: the dismantling card says 'no level'")
if any(len(r["ins"]) != 1 for r in DISMANTLES):
    raise ValueError("a dismantling recipe consumes more than the dismantled part")


def all_items():
    keys = set()
    for r in CRAFTS + DISMANTLES:
        keys.update(full for _, full in r["ins"] + r["outs"])
        keys.update(full for alts in r["tools"] for full in alts)
    return keys


# --- Translations -------------------------------------------------------------------------------


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def tr(folder, lang, *files):
    out = {}
    for name in files:
        out.update(load_json(os.path.join(folder, "EN", name)))
    for name in files:
        out.update(load_json(os.path.join(folder, lang, name)))
    return out


class Names:
    """Translated names of one language: items (mod first, then game), recipes, skills, vanilla terms."""

    def __init__(self, lang):
        self.lang = lang
        self.mod_items = tr(MOD_TR, lang, "ItemName.json")
        self.game_items = tr(GAME_TR, lang, "ItemName.json")
        self.recipes = tr(MOD_TR, lang, "Recipes.json")
        self.game_ui = tr(GAME_TR, lang, "IG_UI.json", "ContextMenu.json", "Fluids.json")

    def item(self, full):
        for table in (self.mod_items, self.game_items):
            if full in table:
                return table[full]
        raise KeyError("no translation for %s (%s)" % (full, self.lang))

    def recipe(self, key):
        if key not in self.recipes:
            raise KeyError("no translation for recipe %s (%s)" % (key, self.lang))
        return self.recipes[key]

    def ui(self, key):
        if key not in self.game_ui:
            raise KeyError("no game translation %s (%s)" % (key, self.lang))
        return self.game_ui[key]

    def skill(self, perk):
        return self.ui("IGUI_perks_" + perk)

    def term(self, name):
        return self.ui(GAME_TERMS[name])


# Languages that write a common noun in lower case inside a sentence (German keeps its capitals, CJK has none).
LOWER_MID_LIST = ("EN", "FR", "ES", "PTBR", "PT", "RU", "TR")


def mid_list(lang, s):
    """A game term placed after the first item of a list: lower-case initial where the language wants it."""
    if lang == "EN":
        return s.lower()  # the English game terms are in Title Case
    return s[:1].lower() + s[1:] if lang in LOWER_MID_LIST and s else s


def level_label(lang, names, skill):
    t = STRINGS[lang]
    return t["no_level"] if skill is None else t["level"] % (names.skill(skill[0]), skill[1])


# --- Icons --------------------------------------------------------------------------------------

ITEM_ICON = re.compile(r"\bitem\s+(\w+)\s*\{(.*?)\}", re.S)
ICON_FIELD = re.compile(r"\b(?:Icon|IconsForTexture)\s*=\s*(\w+)")
ICON_PACKS = ("UI.pack", "UI2.pack")


def read_pack(path, wanted):
    """Images of the named entries of a texture pack, each placed at its offset in its full frame. Pack format of
    TexturePackPage.loadFromPackFile, version 1 ("PZPK", version, page count; per page: name, entries, mask,
    entries x (name, x, y, w, h, ox, oy, full w, full h), PNG length, PNG); integers little-endian, strings prefixed
    by their length."""
    with open(path, "rb") as f:
        b = f.read()
    if b[:4] != b"PZPK" or struct.unpack_from("<i", b, 4)[0] != 1:
        raise ValueError("%s: unsupported pack format" % path)
    found = {}
    pages, o = struct.unpack_from("<i", b, 8)[0], 12
    for _ in range(pages):
        n = struct.unpack_from("<i", b, o)[0]
        o += 4 + n
        count = struct.unpack_from("<i", b, o)[0]
        o += 8
        entries = []
        for _ in range(count):
            n = struct.unpack_from("<i", b, o)[0]
            name = b[o + 4:o + 4 + n].decode("latin-1")
            o += 4 + n
            entries.append((name, struct.unpack_from("<8i", b, o)))
            o += 32
        size = struct.unpack_from("<i", b, o)[0]
        png = b[o + 4:o + 4 + size]
        o += 4 + size
        page = None
        for name, (x, y, w, h, ox, oy, fw, fh) in entries:
            if name in wanted and name not in found:
                page = page or Image.open(io.BytesIO(png)).convert("RGBA")
                im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                im.paste(page.crop((x, y, x + w, y + h)), (ox, oy))
                found[name] = im
    return found


def script_icons(paths, module):
    """{full type: icon name} of the item blocks of item scripts (first IconsForTexture entry when no Icon)."""
    out = {}
    for path in paths:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            src = strip_comments(f.read())
        mod = re.search(r"\bmodule\s+(\w+)", src)
        for name, body in ITEM_ICON.findall(src):
            m = ICON_FIELD.search(body)
            if m:
                out.setdefault("%s.%s" % (mod.group(1) if mod else module, name), m.group(1))
    return out


def sprite_of_moveables():
    """{board key: tile sprite name} from WorldObjectSprite of the mod's moveables."""
    with open(ITEM_SCRIPTS[1], encoding="utf-8-sig") as f:
        src = strip_comments(f.read())
    out = {}
    for name, body in ITEM_ICON.findall(src):
        m = re.search(r"WorldObjectSprite\s*=\s*(\w+)", body)
        if m:
            out[short("Base." + name)] = m.group(1)
    return out


def collect_icons():
    """Every item of the recipes gets docs/images/icons/<key>.png: the mod's texture when it has one, else the game's
    inventory icon from its texture packs. The moveables' tile sprites go to docs/images/icons/tiles/<key>.png."""
    os.makedirs(TILES, exist_ok=True)
    mod_icons = script_icons(ITEM_SCRIPTS, "LiveWater")
    game_paths = [os.path.join(GAME_ITEMS, f) for f in os.listdir(GAME_ITEMS) if f.endswith(".txt")]
    game_icons = script_icons(game_paths, "Base")
    vanilla = {}
    for full in sorted(all_items()):
        ic = mod_icons.get(full)
        src = os.path.join(MOD_TEX, "Item_%s.png" % ic) if ic else None
        if src and os.path.exists(src):
            Image.open(src).convert("RGBA").save(os.path.join(ICONS, short(full) + ".png"), optimize=True)
        elif full in game_icons:
            vanilla[full] = "Item_" + game_icons[full]
        else:
            raise KeyError("no icon for %s" % full)
    found = {}
    for pack in ICON_PACKS:
        found.update(read_pack(os.path.join(GAME_MEDIA, "texturepacks", pack), set(vanilla.values()) - set(found)))
    missing = set(vanilla.values()) - set(found)
    if missing:
        raise KeyError("icons not found in the game packs: %s" % ", ".join(sorted(missing)))
    for full, entry in vanilla.items():
        found[entry].save(os.path.join(ICONS, short(full) + ".png"), optimize=True)
    sprites = sprite_of_moveables()
    tiles = read_pack(TILE_PACK, set(sprites.values()))
    for key, name in sprites.items():
        if name not in tiles:
            raise KeyError("tile %s not in %s" % (name, os.path.basename(TILE_PACK)))
        tiles[name].save(os.path.join(TILES, key + ".png"), optimize=True)


def icon(full_or_key, size):
    key = short(full_or_key) if "." in full_or_key else full_or_key
    im = Image.open(os.path.join(ICONS, key + ".png")).convert("RGBA")
    im = im.crop(im.getbbox())
    k = size / max(im.width, im.height)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                   Image.NEAREST if max(im.width, im.height) <= 32 else Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im)
    return out


def sprite(key):
    """Tile sprite of a part (its inventory icon when the part has no tile, e.g. the filter cartridge), cropped."""
    p = os.path.join(TILES, key + ".png")
    if not os.path.exists(p):
        p = os.path.join(ICONS, key + ".png")
    im = Image.open(p).convert("RGBA")
    return im.crop(im.getbbox())


# --- 1. Recipe book -----------------------------------------------------------------------------


def tool_icons(im, d, tools, x, y, size, gap):
    """Tools drawn right to left from x; alternatives (pipe wrench or wrench) separated by a slash.
    Returns the left edge."""
    slash = ImageFont.truetype(os.path.join(FONTS, "segoeui.ttf"), size * 3 // 4)
    for alts in reversed(tools):
        for k, full in enumerate(reversed(alts)):
            if k:
                text(d, (x - 1, y + size // 2), "/", slash, MUTED, anchor="rm")
                x -= 10
            ic = icon(full, size)
            im.paste(ic, (x - size, y), ic)
            x -= size + gap
    return x


def recipe_book(lang):
    """Recipe book, 640 px wide: Steam shows description images in a column of about 640 px, so a wider
    board would be scaled down and become unreadable. Crafts as cards; dismantling as one compact card."""
    t, names = STRINGS[lang], Names(lang)
    W, PAD = 640, 12
    fT, fS = font(lang, 30, True), font(lang, 15)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    cards = [(r, 84 + ((len(r["ins"]) + 1) // 2) * 40 + 8) for r in CRAFTS]
    ROW = 36
    dis_h = 48 + ROW * len(DISMANTLES) + 34
    H = 70 + sum(ch + 10 for _, ch in cards) + dis_h + 16
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (PAD + 4, 18), t["recipes"], fT)
    text(d, (W - PAD - 4, 32), t["tools"], fS, MUTED, anchor="ra")
    y = 66
    for r, ch in cards:
        d.rounded_rectangle((PAD, y, W - PAD, y + ch), 12, fill=CARD, outline=LINE, width=2)
        # Header: result icon(s), recipe name, skill badge; tools on the right.
        ox = PAD + 12
        for q, o in r["outs"]:
            ic = icon(o, 52)
            im.paste(ic, (ox, y + 12), ic)
            if q > 1:
                text(d, (ox + 52, y + 64), "%d×" % q, font(lang, 14, True), ACCENT, anchor="rd")
            ox += 56
        left = tool_icons(im, d, r["tools"], W - PAD - 12, y + 16, 32, 8)
        rn = names.recipe(r["name"])
        text(d, (ox + 8, y + 12), rn, fit(d, rn, lang, 20, left - 8 - (ox + 8), True))
        lv = level_label(lang, names, r["skill"])
        bw = tsize(probe, lv, fS)[0]
        has = r["skill"] is not None
        d.rounded_rectangle((ox + 8, y + 44, ox + 8 + bw + 18, y + 68), 9, fill=ACCENT_BG if has else (235, 235, 235))
        text(d, (ox + 17, y + 56), lv, fS, ACCENT if has else MUTED, anchor="lm")
        # Ingredients on two columns.
        d.line((PAD + 12, y + 78, W - PAD - 12, y + 78), fill=LINE, width=1)
        colw = (W - 2 * PAD - 24) / 2
        for k, (q, it) in enumerate(r["ins"]):
            cx = PAD + 12 + (k % 2) * colw
            cy = y + 86 + (k // 2) * 40
            ic = icon(it, 32)
            im.paste(ic, (int(cx), cy), ic)
            label, f = fit_or_wrap(d, "%d× %s" % (q, names.item(it)), lang, 16, colw - 48, 14)
            text(d, (cx + 40, cy + 16), label, f, INK, anchor="lm", spacing=1)
        y += ch + 10
    # Dismantling: one row per part: part icon and name, what comes back, tools on the right.
    d.rounded_rectangle((PAD, y, W - PAD, y + dis_h), 12, fill=CARD, outline=LINE, width=2)
    text(d, (PAD + 12, y + 12), t["dis_title"], font(lang, 20, True), ACCENT)
    text(d, (W - PAD - 12, y + 16), t["no_level"], fS, MUTED, anchor="ra")
    fN, fQ = font(lang, 15), font(lang, 13, True)
    name_w = 250
    for k, r in enumerate(DISMANTLES):
        yy = y + 46 + ROW * k
        part = r["ins"][0][1]
        ic = icon(part, 26)
        im.paste(ic, (PAD + 12, yy), ic)
        nm, f = fit_or_wrap(d, names.item(part), lang, 15, name_w - 10, 13)
        text(d, (PAD + 46, yy + 13), nm, f, INK, anchor="lm", spacing=0)
        x = PAD + 46 + name_w
        arrow(d, x - 4, yy + 13, x + 18, yy + 13, w=3, head=8)
        x += 28
        for q, o in r["outs"]:
            if q > 1:
                text(d, (x, yy + 13), "%d×" % q, fQ, ACCENT, anchor="lm")
                x += tsize(d, "%d×" % q, fQ)[0] + 3
            ic = icon(o, 24)
            im.paste(ic, (x, yy + 1), ic)
            x += 32
        tool_icons(im, d, r["tools"], W - PAD - 12, yy + 1, 24, 6)
        if k:
            d.line((PAD + 12, yy - 4, W - PAD - 12, yy - 4), fill=(238, 234, 226), width=1)
    note = t["dis_note"]
    text(d, (PAD + 12, y + dis_h - 14), note, fit(d, note, lang, 14, W - 2 * PAD - 24), MUTED, anchor="ld")
    save(im, "recipe_book", lang)


# --- 2. Equipment board -------------------------------------------------------------------------

# Board order: the parts as they are met along a network (wiki, Getting started). Each shows its fig_<key> line.
EQUIP = ["Pipe", "PondPump", "Valve", "FlowMeter", "HouseInlet",
         "WaterFilter", "Sprinkler", "SprinklerAuto", "DripLine", "BarrelFitting"]
PER_ROW = 5


def part_full(key):
    for r in CRAFTS:
        for _, full in r["outs"]:
            if short(full) == key:
                return full, r
    raise KeyError("no craft recipe makes %s" % key)


def wrap2(d, s, lang, size, width):
    """Name on one line, or on two lines at the most balanced break when one line is too wide."""
    f = font(lang, size, True)
    if tsize(d, s, f)[0] <= width:
        return s, f
    units = list(s) if lang in NO_SPACE else s.split(" ")
    sep = "" if lang in NO_SPACE else " "
    best = None
    for k in range(1, len(units)):
        a, b = sep.join(units[:k]), sep.join(units[k:])
        w = max(tsize(d, a, f)[0], tsize(d, b, f)[0])
        if best is None or w < best[0]:
            best = (w, a + "\n" + b)
    if best is None:
        return s, fit(d, s, lang, size, width, True)
    return best[1], fit(d, best[1], lang, size, width, True)


def equipment(lang):
    """Board of the parts: picture, name, role line with its key figure, level badge when the craft needs one."""
    t, names = STRINGS[lang], Names(lang)
    rows = (len(EQUIP) + PER_ROW - 1) // PER_ROW
    W, RH = 1200, 340
    H = 20 + rows * RH + 10
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, W - 10, H - 10), 14, fill=CARD, outline=LINE, width=2)
    cw = (W - 40) / PER_ROW
    PIC_W, PIC_H = 150, 150
    # Common scale, enlarged up to 2.5x for the small parts so they stay readable.
    base = min(min(PIC_W / sprite(k).width, PIC_H / sprite(k).height) for k in EQUIP)
    fF = font(lang, 15)
    for i, key in enumerate(EQUIP):
        full, recipe = part_full(key)
        cx = 20 + cw * (i % PER_ROW) + cw / 2
        top = 20 + RH * (i // PER_ROW)
        if i % PER_ROW == 0 and i:
            d.line((30, top - 4, W - 30, top - 4), fill=(238, 234, 226), width=1)
        sp = sprite(key)
        k = min(2.5 * base, PIC_W / sp.width, PIC_H / sp.height)
        sp = sp.resize((max(1, int(sp.width * k)), max(1, int(sp.height * k))), Image.LANCZOS)
        im.paste(sp, (int(cx - sp.width / 2), top + 20 + PIC_H - sp.height), sp)
        nm, f = wrap2(d, names.item(full), lang, 18, cw - 16)
        text(d, (cx, top + 184), nm, f, INK, anchor="ma", align="center")
        name_h = tsize(d, nm, f)[1]
        fig = "\n".join(wrap(d, part, fF, cw - 24, lang) for part in t["fig_" + key].split("\n"))
        fy = top + 184 + name_h + 12
        text(d, (cx, fy), fig, fF, ACCENT, anchor="ma", align="center", spacing=3)
        if recipe["skill"]:
            lv = level_label(lang, names, recipe["skill"])
            fy += tsize(d, fig, fF, 3)[1] + 10
            bw = tsize(d, lv, fF)[0]
            d.rounded_rectangle((cx - bw / 2 - 9, fy, cx + bw / 2 + 9, fy + 24), 9, fill=ACCENT_BG)
            text(d, (cx, fy + 12), lv, fF, ACCENT, anchor="mm")
    save(im, "equipment", lang)


# --- 3. Diagram ---------------------------------------------------------------------------------


def box(d, xy, fill, outline, width=2):
    d.rounded_rectangle(xy, 12, fill=fill, outline=outline, width=width)


def paste_icon(im, key, x, y, size):
    ic = icon(key, size)
    im.paste(ic, (x, y), ic)


def paste_sprite(im, key, cx, bottom_y, max_w, max_h):
    sp = sprite(key)
    k = min(max_w / sp.width, max_h / sp.height)
    sp = sp.resize((max(1, int(sp.width * k)), max(1, int(sp.height * k))), Image.LANCZOS)
    im.paste(sp, (int(cx - sp.width / 2), int(bottom_y - sp.height)), sp)


def diagram(lang):
    """How it works: source -> water pump -> pipes (+ valve) -> outlets (house inlet, sprinklers, fill fitting)."""
    t, names = STRINGS[lang], Names(lang)
    item = lambda key: names.item(part_full(key)[0])  # noqa: E731
    W, H = 1200, 500
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, W - 10, H - 10), 14, fill=CARD, outline=LINE, width=2)
    text(d, (30, 26), t["d_title"], font(lang, 24, True))
    fT = font(lang, 22, True)
    # Source
    box(d, (30, 80, 250, 380), BLUE_BG, BLUE)
    text(d, (48, 96), t["d_source"], fit(d, t["d_source"], lang, 22, 185, True))
    src = "\n".join((t["d_natural"], names.term("well"), t["d_barrel"], names.term("collector"),
                     names.term("gaspump")))
    src = "\n".join(wrap(d, line, font(lang, 18), 180, lang) for line in src.split("\n"))
    text(d, (48, 142), src, fit(d, src, lang, 18, 185), spacing=12)
    arrow(d, 255, 200, 285, 200, head=12)
    # Water pump
    box(d, (290, 80, 520, 380), ACCENT_BG, ACCENT, 3)
    pump = caps(item("PondPump"), lang)
    pump = wrap(d, pump, fT, 195, lang)
    text(d, (308, 96), pump, fit(d, pump, lang, 22, 195, True))
    paste_sprite(im, "PondPump", 405, 250, 150, 100)
    text(d, (308, 266), t["d_pump_fig"], fit(d, t["d_pump_fig"], lang, 18, 195, True))
    text(d, (308, 304), t["d_power"], fit(d, t["d_power"], lang, 15, 195), MUTED)
    arrow(d, 525, 200, 555, 200, head=12)
    # Pipes and valve
    box(d, (560, 80, 780, 380), CARD, LINE)
    text(d, (578, 96), t["d_pipes"], fit(d, t["d_pipes"], lang, 22, 185, True))
    paste_icon(im, "Pipe", 578, 140, 44)
    text(d, (632, 162), t["d_pipes_note"], fit(d, t["d_pipes_note"], lang, 14, 140), MUTED, anchor="lm")
    paste_icon(im, "Valve", 578, 220, 44)
    valve = t["d_valve"] % item("Valve")
    valve = "\n".join(wrap(d, line, font(lang, 15), 185, lang) for line in valve.split("\n"))
    text(d, (578, 274), valve, fit(d, valve, lang, 15, 185), INK)
    # Outlets: three rows, each part -> what it serves.
    box(d, (820, 60, 1170, 470), GREEN_BG, GREEN)
    text(d, (838, 72), t["d_outlets"], fit(d, t["d_outlets"], lang, 22, 310, True), GREEN)
    d.line((790, 200, 805, 200), fill=ACCENT, width=5)
    d.line((805, 158, 805, 402), fill=ACCENT, width=5)
    rows = [
        (["HouseInlet"], item("HouseInlet"), t["d_with"] % item("WaterFilter"), t["d_house"], "WaterFilter"),
        (["Sprinkler", "DripLine"], "%s / %s" % (item("Sprinkler"), item("DripLine")), None, t["d_crops"], None),
        (["BarrelFitting"], item("BarrelFitting"), None,
         t["d_fill"] % (t["d_barrel"], mid_list(lang, names.term("collector")),
                        mid_list(lang, names.term("trough"))), None),
    ]
    for k, (keys, label, extra, serves, extra_icon) in enumerate(rows):
        y = 110 + k * 122
        arrow(d, 805, y + 48, 836, y + 48, head=10)
        x = 840
        for key in keys:
            paste_icon(im, key, x, y + 26, 44)
            x += 46
        tx = 840 + 46 * len(keys) + 6
        tw = 1160 - tx
        lab = label
        if tsize(d, lab, font(lang, 17, True))[0] > tw:
            # Too wide: one part per line ("Sprinkler /" then "Drip Line"), each wrapped if still too wide.
            lab = " /\n".join(wrap(d, part, font(lang, 17, True), tw, lang) for part in label.split(" / "))
        text(d, (tx, y + 14), lab, fit(d, lab, lang, 17, tw, True))
        ly = bottom(d, (tx, y + 14), lab, fit(d, lab, lang, 17, tw, True)) + 6
        if extra:
            paste_icon(im, extra_icon, tx, ly, 20)
            text(d, (tx + 24, ly + 10), extra, fit(d, extra, lang, 14, tw - 24), ACCENT, anchor="lm")
            ly += 26
        serves = "\n".join(wrap(d, line, font(lang, 15), tw - 22, lang) for line in serves.split("\n"))
        fS = fit(d, serves, lang, 15, tw - 22)
        text(d, (tx, ly + 2), "\u2192", fS, GREEN)
        text(d, (tx + 22, ly + 2), serves, fS, INK, spacing=3)
    # Rule: one liquid per network.
    rule = t["d_rule"]
    rule_f = fit(d, rule, lang, 16, 760)
    rw = tsize(d, rule, rule_f)[0]
    d.rounded_rectangle((30, 410, 30 + rw + 30, 450), 10, fill=BG, outline=GREY, width=2)
    text(d, (45, 430), rule, rule_f, INK, anchor="lm")
    save(im, "diagram", lang)


def main():
    langs = [a.upper() for a in sys.argv[1:]] or LANGS
    collect_icons()
    for lang in langs:
        recipe_book(lang)
        equipment(lang)
        diagram(lang)


if __name__ == "__main__":
    main()

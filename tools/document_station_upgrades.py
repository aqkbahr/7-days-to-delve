from pathlib import Path
import csv,json
from station_upgrade_design import BASES,UPGRADES,COLLECTOR,tool
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts/station-upgrades'
base=Path((ART/'base.txt').read_text(encoding='utf-8-sig').strip())
catalog=json.loads((ART/'catalogue.json').read_text());labels={}
files=[Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config/Localization.csv')]+sorted((base/'Mods').glob('*/Config/Localization.csv'))+[ROOT/'src/ZZZZZZZZZZDelveStations/Config/Localization.csv']
for p in files:
    for r in csv.DictReader(p.open(encoding='utf-8-sig')):
        if r.get('english'):labels[r['Key']]=r['english']
label=lambda n:labels.get(n,n)
ingredients=lambda cost:', '.join(str(c)+' '+label(n) for n,c in cost.items())
aliasbase={a:n for n,(_,_,aliases,_,_) in BASES.items() for a in aliases}
lines=['STATION ADD-ONS — v0.12.0','',
 'Nine crafting benches plus the Rain Collector: one or two bases per craft.',
 'Build bases at crafting proficiency 1. Craft add-ons in inventory at the listed proficiency, then install them in the matching ADD-ONS slots. Carrying them in a backpack is not enough. They are removable and reusable; recipes still require the proficiency and ingredients shown.',
 'Only the required add-on must be installed for an individual recipe. Keeping all matching add-ons installed gives the station its full range. Add-ons expand recipes; collector tools retain native collection/yield/filter effects.',
 'Field supplies, basic runes, first aid and prepared repairs remain portable. Finished equipment and refined work retain the combined-build station requirements.',
 'Optional Crafting Tomes remain optional vendor lessons (500 gold; at least three different types per restock). They do not unlock stations or recipes.',
 'Existing standalone and tiered stations remain usable as legacy variants with the corresponding new add-on slots. Their new construction recipes are retired. Finish queued construction of retired stations before changing versions. Existing ordinary recipe signatures are retained.',
 'This update does not require a fresh save. If you have not yet started a new save for the included POI elevation correction, that terrain correction still requires one. The launcher retains the currently selected save-data folder.',
 '', 'BASE STATIONS AND ADD-ONS', '']
for name,(title,skill,aliases,tools,cost) in BASES.items():
    lines += [f'{skill}: {title} — proficiency 1', '  Build: '+ingredients(cost)]
    for k in tools:
        title2,skill2,rank,cost2,icon,function=UPGRADES[k]
        lines += [f'  {rank}: {title2} — {function}.', '      Craft: '+ingredients(cost2)]
    lines.append('')
lines+=['Farming: Forest Rain Collector — proficiency 1', '  Build: '+ingredients(next(r['ingredients'] for r in catalog['recipes'] if r['name']=='delveRainCollector'))]
for n,(title,rank,cost,function) in COLLECTOR.items():lines += [f'  {rank}: {title} — {function}.','      Craft: '+ingredients(cost)]
lines += ['', 'FOREST PROGRESSION AND FIRST HORDE', '',
 '1: Gather wood, stone, fiber, clay and ores. Build the bases you need, a rain collector and clay jars. Make charcoal and clean water; prepare field supplies, basic weapons and armor. Collect herbs/crops from Forest plants and gardens, and meat/hides/bone from wildlife. Forest iron deposits also supply lead for wand runes.',
 '10: Install composting, milling, pot, anvil, timber/leather processing, herb preparation, rune engraving and stone-cutting add-ons as the relevant crafts advance. Make processed components and medicine. Rain collection can gain its funnel and canopy.',
 '20: Install seed sorting, preserving, grill, bellows, precision joinery, armor fitting, fermentation, rune etching and ore sorting upgrades. Prepare Forged equipment, advanced meals, medicine, runes and charges; add charcoal water filtration.',
 'For the first horde: build your refuge and spikes, carry food/water/medicine, bring ammunition or runes, and pack the matching Focus/Hide/Metal repair supplies. Crafting branches at proficiency 20 still use character-level perk points.',
 '', 'VALIDATED EXACT RECIPE VARIANTS', 'Proficiency is the required crafting skill, not character level. The Alchemy-40 excavation charge is retained outside the first-playtest scope.', '']
for r in sorted(catalog['recipes'],key=lambda r:(r['rank'],r['skill'] or '',label(r['name']),r.get('station',''),r['count'])):
    station=label(aliasbase.get(r.get('station'),r.get('station'))) if r.get('station') else 'Inventory'
    addon=' + '+label(r['tool']) if r.get('tool') else ''
    lines.append(f"P{r['rank']} {r['skill'] or 'Supplies'}: {r['count']} {label(r['name'])} | {station}{addon} | {ingredients(r['ingredients'])}")
(ART/'STATION-UPGRADES.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Wrote station and recipe guide:',len(catalog['recipes']),'variants')

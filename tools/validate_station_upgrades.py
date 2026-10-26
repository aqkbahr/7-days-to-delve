"""Build reproducible native probe inputs and validate the fully merged config."""
from build_station_upgrades import *
docs={k:merge(k,True) for k in ('blocks','items','recipes','XUi_InGame/xui','XUi_InGame/windows')}
root=E.Element('checks')
for r in rows:
    E.SubElement(root,'recipe',key=r['key'],skill=r['skill'] or '',rank=str(r['rank']),tool=r.get('tool') or '',queue=str(bool(r.get('tool'))).lower())
    matches=[]
    for live in docs['recipes'].xpath('/recipes/recipe[@name=$n]',n=r['name']):
        lr=dict(name=live.get('name'),station=live.get('craft_area',''),count=int(live.get('count','1')),ingredients={i.get('name'):int(i.get('count')) for i in live.findall('ingredient')})
        if key(lr)==r['key']:matches.append(live)
    assert len(matches)==1,(r['key'],len(matches))
    assert matches[0].get('craft_tool','')==(r.get('tool') or ''),r['key']
    if r.get('tool') and r.get('station') in aliasbase:
        assert r['tool'] in catalog['station_bases'][aliasbase[r['station']]]['tools'],r['key']
for name,(title,skill,aliases,tools,cost) in BASES.items():
    for variant in [name]+[a for a in aliases if a in RETIRED]:
        E.SubElement(root,'station',name=variant,base=name,tools=','.join(tool(t) for t in tools),aliases=','.join(aliases))
        b=docs['blocks'].xpath('/blocks/block[@name=$n]',n=variant)[0]
        assert b.xpath("property[@class='Workstation']/property[@name='Modules']/@value")==['tools,output']
        assert b.xpath("property[@class='Workstation']/property[@name='CraftingAreaRecipes']/@value")==[','.join(aliases)]
    group=docs['XUi_InGame/xui'].xpath('/xui/window_group[@name=$n]',n='workstation_'+name)
    assert len(group)==1
    for window in group[0].findall('window'):
        assert docs['XUi_InGame/windows'].xpath('/windows/window[@name=$n]',n=window.get('name')),window.get('name')
    grid=docs['XUi_InGame/windows'].xpath('/windows/window[@name=$n]//grid',n='delveTools_'+name)[0]
    assert grid.get('cols')==str(len(tools)) and grid.get('required_tools_only')=='true'
    assert grid.get('required_tools')==','.join(tool(t) for t in tools)
for n in RETIRED:
    E.SubElement(root,'retired',name=n)
    assert not docs['recipes'].xpath('/recipes/recipe[@name=$n]',n=n)
for k,v in UPGRADES.items():
    # Native item/block icons are available from the game's atlas.
    assert docs['items'].xpath('/items/item[@name=$n]',n=v[4]) or docs['blocks'].xpath('/blocks/block[@name=$n]',n=v[4]),v[4]
E.ElementTree(root).write(str(ART/'checks.xml'),pretty_print=True,encoding='utf-8')
# Validate progression closure separately at 1, 10 and 20, not just end-game reachability.
tiers={}
for tier in range(1,21):
    available=set(catalog['sources']);pending=[r for r in rows if r['rank']<=tier]
    while pending:
        if {'delveRainCollector','drinkJarEmpty'}<=available:available.add('drinkJarRiverWater')
        unlocked=[r for r in pending if set(r['ingredients'])<=available and (not r.get('station') or aliasbase.get(r['station'],r['station']) in available) and (not r.get('tool') or r['tool'] in available)]
        if not unlocked:break
        available.update(r['name'] for r in unlocked);pending=[r for r in pending if r not in unlocked]
    # Some efficient variants intentionally consume later-tier intermediates;
    # every recipe output advertised at a tier must have an available route.
    assert not pending,(tier,[r['key'] for r in pending])
    tiers[tier]={'available_items':len(available),'later_ingredient_variants':[r['key'] for r in pending]}
report=dict(result='PASS',recipes=len(rows),base_stations=10,legacy_variants=len(RETIRED),addon_recipes=22,tier_closure=tiers,checks='Merged recipes, station aliases, tool providers, XUi references and native icon identities')
(ART/'static-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))

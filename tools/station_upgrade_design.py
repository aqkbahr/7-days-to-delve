"""Compact station progression; tool slots expand native crafting capabilities."""
BASES={
 'delveFarmDispatch':('Farm Workbench','Farming',['delveFarmDispatch','delveCompostBin'],['CompostBasket','SeedPress'],{'resourceWood':20,'resourceYuccaFibers':10}),
 'delveFieldHearth':('Field Hearth','Cooking',['delveFieldHearth','campfire'],['CookingPot','CookingGrill'],{'resourceRockSmall':20,'resourceClayLump':10}),
 'delveGrainMill':('Pantry Bench','Cooking',['delveGrainMill','delvePreservingCrock'],['GrainMill','PreservingCrock'],{'resourceWood':20,'resourceClayLump':10}),
 'delveForgeAnvil':('Forest Forge','Smithing',['delveForgeAnvil'],['Anvil','Bellows'],{'resourceRockSmall':40,'resourceClayLump':30,'resourceWood':20}),
 'delveSawKit':("Carpenter's Bench",'Carpentry',['delveSawKit'],['SeasoningRack','PrecisionJig'],{'resourceWood':25,'resourceRockSmall':10}),
 'delveOutfittingKit':('Outfitting Bench','Carpentry',['delveOutfittingKit'],['DressingFrame','ArmorForm'],{'resourceWood':20,'resourceCloth':8,'resourceBone':4}),
 'delveMortarKit':('Apothecary Bench','Alchemy',['delveMortarKit','delveDryingRack','delveFermentingBarrel'],['Mortar','DryingRack','Fermenter'],{'resourceRockSmall':20,'resourceClayLump':10,'resourceWood':5}),
 'delveInscriptionKit':('Rune Bench','Alchemy',['delveInscriptionKit'],['EngravingTools','EtchingTools'],{'resourceRockSmall':10,'resourceCloth':4,'resourceWood':10}),
 'delveSortingTable':('Ore Processing Table','Mining',['delveSortingTable'],['StoneCutter','OreSieve'],{'resourceWood':20,'resourceRockSmall':20}),
}
# key: name, owning skill, proficiency, ingredients, native icon, function
UPGRADES={
 'CompostBasket':('Compost Basket','Farming',10,{'resourceWood':15,'resourceYuccaFibers':10,'resourceClayLump':5},'resourceYuccaFibers','Compost production at the Farm Workbench'),
 'SeedPress':('Seed Sorting Press','Farming',20,{'resourceWood':20,'resourceForgedIron':4,'resourceCloth':4},'plantedCorn1','Efficient seed batches: three crop ingredients produce two seeds'),
 'CookingPot':('Hearth Cooking Pot','Cooking',10,{'resourceForgedIron':3,'resourceClayLump':5},'toolCookingPot','Cooked meals and hot drinks beyond basic water and roast food'),
 'CookingGrill':('Hearth Roasting Grill','Cooking',20,{'resourceForgedIron':5,'resourceRockSmall':5},'toolCookingGrill','Advanced hearth meals'),
 'GrainMill':('Hand-Mill Attachment','Cooking',10,{'resourceWood':15,'resourceRockSmall':30},'foodCornMeal','Milled grain and travel bread at the Pantry Bench'),
 'PreservingCrock':('Preserving Crock Insert','Cooking',20,{'resourceClayLump':30,'delveCharcoal':3,'resourceCloth':2},'drinkJarEmpty','Preserves at the Pantry Bench'),
 'Anvil':('Forge Anvil','Smithing',10,{'resourceForgedIron':6,'resourceWood':5},'toolAnvil','Iron fittings and intermediate smithing'),
 'Bellows':('Forge Bellows','Smithing',20,{'resourceLeather':6,'resourceWood':15,'delveIronFittings':4},'toolBellows','Forged equipment and concentrate smelting'),
 'SeasoningRack':('Seasoning-Rack Attachment','Carpentry',10,{'resourceWood':20,'resourceForgedIron':2},'resourceWood','Seasoned timber and improved focus repair supplies'),
 'PrecisionJig':('Precision Joinery Jig','Carpentry',20,{'delveSeasonedTimber':6,'resourceForgedIron':4,'resourceLeather':2},'meleeToolRepairT1ClawHammer','Forged bows and casting focuses'),
 'DressingFrame':('Leather and Weaving Frame','Carpentry',10,{'resourceWood':20,'resourceCloth':6,'resourceBone':4},'resourceCloth','Cured leather, woven cloth and batch repair/medical supplies'),
 'ArmorForm':('Armor-Fitting Form','Carpentry',20,{'delveSeasonedTimber':4,'delveCuredLeather':2,'delveWovenCloth':2},'resourceLeather','Forged light and medium armor'),
 'Mortar':('Mortar and Pestle','Alchemy',10,{'resourceRockSmall':15,'resourceClayLump':5},'resourceRockSmall','Herbal extracts, Ember Salts and prepared reagents'),
 'DryingRack':('Herb-Drying Attachment','Alchemy',10,{'resourceWood':15,'resourceYuccaFibers':10},'resourceCropGoldenrodPlant','Dried thyme and yarrow'),
 'Fermenter':('Fermentation Vessel','Alchemy',20,{'resourceWood':20,'resourceClayLump':15,'resourceForgedIron':2},'drinkJarBeer','Herbal spirits, tinctures and advanced alchemical charges'),
 'EngravingTools':('Rune Engraving Tools','Alchemy',10,{'resourceForgedIron':2,'resourceBone':3,'resourceCloth':2},'resourceScrapIron','Efficient batches of basic runes and Mooncap runes'),
 'EtchingTools':('Rune Etching Set','Alchemy',20,{'resourceForgedIron':4,'delveHerbalExtract':2,'delveRuneBlank':4},'toolBeaker','Etched runes'),
 'StoneCutter':('Stone-Cutting Set','Mining',10,{'resourceForgedIron':2,'resourceWood':8,'resourceRockSmall':5},'meleeToolPickT1IronPickaxe','Dressed stone, rune blanks and efficient masonry'),
 'OreSieve':('Ore-Sorting Sieve','Mining',20,{'resourceForgedIron':4,'resourceWood':12,'resourceCloth':4},'resourceScrapIron','Iron concentrate'),
}
COLLECTOR={
 'toolDewGatherer':('Catchment Funnel',10,{'resourceForgedIron':2,'resourceClayLump':10},'Native faster rain collection'),
 'toolDewTarp':('Raincloth Canopy',10,{'resourceCloth':10,'resourceWood':10},'Native increased water yield'),
 'toolDewFilter':('Charcoal Water Filter',20,{'delveCharcoal':5,'resourceCloth':4,'resourceRockSmall':10},'Native clean-water filtering'),
}
for base in ('delveFieldHearth','delveForgeAnvil','delveSawKit','delveOutfittingKit','delveMortarKit','delveSortingTable','delveInscriptionKit'):
    BASES[base][2].extend([base+'Tier2',base+'Tier3'])
RETIRED={alias:base for base,(_,_,aliases,_,_) in BASES.items() for alias in aliases if alias not in BASES and alias!='campfire'}
def tool(key):return {'CookingPot':'toolCookingPot','CookingGrill':'toolCookingGrill'}.get(key,'delveUpgrade'+key)
def requirement(row):
    area=row.get('station','').replace('Tier2','').replace('Tier3','');rank=row['rank'];name=row['name']
    # Base recipes must remain usable before players can make tier-10 tools.
    if rank<10:return row.get('tool','')
    if area=='delveCompostBin':return tool('CompostBasket')
    if area=='delveDryingRack':return tool('DryingRack')
    if area=='delveFermentingBarrel':return tool('Fermenter')
    if area=='delveGrainMill':return tool('GrainMill')
    if area=='delvePreservingCrock':return tool('GrainMill' if rank<=10 else 'PreservingCrock')
    if area=='delveMortarKit':return tool('Fermenter' if rank>=20 else 'Mortar')
    if area=='delveInscriptionKit':return tool('EtchingTools' if rank>=20 else 'EngravingTools')
    if area=='delveSortingTable':return tool('OreSieve' if name=='delveIronConcentrate' else 'StoneCutter')
    if area=='delveSawKit':return tool('PrecisionJig' if rank>=20 else 'SeasoningRack')
    if area=='delveOutfittingKit':return tool('ArmorForm' if rank>=20 else 'DressingFrame')
    if area=='delveForgeAnvil':
        if rank>=20 or 'delveIronConcentrate' in row['ingredients']:return tool('Bellows')
        if rank>=10:return tool('Anvil')
    if area in ('delveFieldHearth','campfire') and rank>=10:return tool('CookingGrill' if rank>=20 and row['skill']=='Cooking' else 'CookingPot')
    return row.get('tool','')

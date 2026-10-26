"""Farm plot additions shared by the content generator and focused rebuilds."""
from xml.etree import ElementTree as E


def add_farming(recipes, loc):
    blocks = E.Element('configs')
    append = E.SubElement(blocks, 'append', xpath='/blocks')
    block = E.SubElement(append, 'block', name='delveFarmPlotPlate')
    for name, value in {
        'Extends': 'farmPlotBlockPlayer',
        'CustomIcon': 'farmPlotBlock',
        'DescriptionKey': 'delveFarmPlotPlateDesc',
        'Shape': 'New',
        'Model': '@:Shapes/plate.fbx',
        'Texture': '47,47,47,47,47,47',
        'UseGlobalUV': 'G,G,G,G,G,G',
        'OnlySimpleRotations': 'false',
        'ImposterExclude': 'true',
        'SortOrder2': '0006',
    }.items():
        E.SubElement(block, 'property', name=name, value=value)
    # Explicit drops avoid inherited terrain salvage and return the shared item.
    E.SubElement(block, 'dropextendsoff')
    E.SubElement(block, 'drop', event='Destroy', name='farmPlotBlockVariantHelper', count='1')
    E.SubElement(blocks, 'set', xpath="/blocks/block[@name='farmPlotBlockVariantHelper']/property[@name='PlaceAltBlockValue']/@value").text = (
        'farmPlotBlockPlayer,farmPlotBlockPlayerCornerRound,farmPlotBlockPlayerRaised,delveFarmPlotPlate')
    for ingredient, count in {
        'resourceWood': 2, 'foodRottingFlesh': 2,
        'resourcePotassiumNitratePowder': 5, 'resourceClayLump': 20,
    }.items():
        E.SubElement(recipes, 'set', xpath=f"/recipes/recipe[@name='farmPlotBlockVariantHelper']/ingredient[@name='{ingredient}']/@count").text = str(count)
    loc('delveFarmPlotPlate', 'Farm Plot (Borderless Plate)')
    loc('delveFarmPlotPlateDesc', 'A thin soil plate without a wooden border. Select from Farm Plot shapes and rotate flat onto the ground. Plant seeds as with a normal farm plot.')
    return blocks

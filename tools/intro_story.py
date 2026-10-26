"""Shared player-facing introduction, applied after content generation."""
from pathlib import Path
import csv
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CORE = {
    'delveFieldGuideDesc': 'READ to begin three preparation quests. Allium has fallen beneath the Demon Queen\'s war, but its people endure. Seek the Steward in Wayrest on the Living Border; choose Tell me about Wayrest, take Reclaim Wayrest, then ask for jobs. Two struggles lie ahead: recover the frontier through settlement contracts, and defeat the champions of the Queen\'s incursions. Their progress is shared, but independent. First gather supplies, craft a weapon and healing, and establish a refuge outside Wayrest. Settlements close on incursion nights. Prepare food, clean water, ammunition, repairs and defenses. The Ashbound Warden is the first champion available in this chapter. Choose a heritage by crafting one Heritage Seal; use Skills to develop your character. The Forest crafting guides explain equipment and processing.',
    'delveArrivalDesc': 'Allium has fallen beneath the Demon Queen\'s war, but the Living Border still holds. Seek the Steward in Wayrest for work and the reclamation journal. First gather 20 wood, 10 small stones and 20 plant fibers, then craft a Wayfarer Dagger and Greenleaf Poultice. These personal preparation quests help you survive; settlement contracts and incursion champion victories advance the two shared campaigns separately.',
    'delveHearthDesc': 'Wayrest needs adventurers who can endure beyond its walls. Craft a Settlement Stone, bedroll and campfire, then place them at a defensible refuge outside the settlement. This journal tracks crafting; placing and defending your refuge is your next practical step. You may maintain two active Settlement Stones per player. Secure food and clean water, improve your equipment, and prepare defenses: Wayrest closes on incursion nights.',
    'delveEmbersDesc': 'Even corruption can supply the resistance. Gather three Ember Salts by harvesting defeated corrupted enemies, then craft an Ember Ward Draught. Keep taking and returning Wayrest contracts while preparing your refuge. On an incursion night, survive the assault outside the settlement; the undefeated Ashbound Warden arrives two game-hours before dawn. Defeat it before dawn to earn a shared champion victory. Surviving the night alone does not defeat the champion.',
    'delveWorldJournalDesc': 'Allium has two shared struggles: settlement contracts reclaim the frontier, while champion victories resist the Demon Queen. They advance independently. Reclaim Wayrest tracks ten returned contracts. The number beside this entry counts corrupted enemies defeated, not contracts or champion victories. Warden Defeated records the first champion victory for everyone and survives restarts.',
    'delveWardenVictoryDesc': 'The Ashbound Warden has fallen. This shared victory endures even if adventurers later fall in battle. Continue reclaiming the frontier and defending your refuge: incursions continue. The remaining champions and the Demon Queen belong to later campaign chapters.',
}
WAYREST = {
    'delveWayrestGreeting': 'Welcome to Wayrest, a foothold on the Living Border. We endure by helping one another. Speak with me about our work, the Queen\'s incursions, or preparing your refuge.',
    'delveWayrestWelcome': 'We cannot take back Allium in a single battle. First we recover our stores and clear the woodland ruins. Take Reclaim Wayrest here, then return to my main choices and ask for jobs. Follow your contract marker, activate its rally point, finish the objectives, and return to me for your reward. Ten returned contracts advance our shared foothold; a shared job counts once at its owner\'s hand-in. The supply exercise is optional preparation and does not count. Champion victories are a separate struggle.',
    'delveWayrestAskIncursions': 'Tell me about the Queen\'s incursions.',
    'delveWayrestIncursions': 'The Queen sends more than wandering creatures. When the blood moon rises, her forces come in strength and our gates close. Build your own defenses outside Wayrest. Scouts will warn you on the day of an incursion. The undefeated Ashbound Warden comes two game-hours before dawn: defeat it before daylight. If it withdraws, it remains undefeated and returns on a later incursion. A victory belongs to everyone and cannot be undone by later deaths. Reclaiming settlements and defeating champions advance separately. This chapter begins with the Warden; the other champions and the Queen await later chapters.',
    'delveWayrestAskRefuge': 'How should we prepare?',
    'delveWayrestRefuge': 'Read your Field Guide and complete its three preparation quests. Establish a Settlement Stone, bedroll and campfire outside Wayrest. Secure food and clean water, then stock healing, ammunition and repair supplies. Use the Forest crafting guides to build your hearth and forge and improve your equipment. Take a woodland contract, follow its journal objectives, and return here for payment. Each journey should leave your refuge better prepared for the next incursion.',
    'delveWayrestSuppliesDesc': 'Before you venture into the ruins, prepare supplies and healing. Gather 30 wood and 20 small stones, then craft two Greenleaf Poultices. You keep your supplies. This optional personal exercise does not count toward Reclaim Wayrest. Ask the Steward for woodland contracts to advance reclamation.',
}

def localize(module, strings):
    path = ROOT / 'src' / module / 'Config/Localization.csv'
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.reader(stream))
    column = rows[0].index('english')
    remaining = dict(strings)
    for row in rows[1:]:
        if row and row[0] in strings:
            row[column] = strings[row[0]]
            remaining.pop(row[0], None)
    for key, value in remaining.items():
        row = [''] * len(rows[0]); row[0] = key; row[1] = module; row[column] = value
        rows.append(row)
    with path.open('w', encoding='utf-8', newline='') as stream:
        csv.writer(stream).writerows(rows)

def apply_core():
    localize('Delve', CORE)

def apply_wayrest():
    localize('DelveWayrest', WAYREST)
    path = ROOT / 'src/DelveWayrest/Config/dialogs.xml'
    tree = ET.parse(path); dialog = tree.find('.//dialog'); start = dialog.find("statement[@id='start']")
    for suffix in ('Incursions', 'Refuge'):
        ident = 'wayrest' + suffix
        if dialog.find(f"response[@id='{ident}']") is None:
            start.insert(1, ET.Element('response_entry', id=ident))
            ET.SubElement(dialog, 'response', id=ident, text='delveWayrestAsk'+suffix, nextstatementid=ident)
            statement = ET.SubElement(dialog, 'statement', id=ident, text='delveWayrest'+suffix)
            ET.SubElement(statement, 'response_entry', id='nevermind')
    ET.indent(tree); tree.write(path, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    apply_core()
    apply_wayrest()

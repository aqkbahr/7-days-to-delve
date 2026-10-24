"""Reusable first-incursion content, called by build_content.py."""
from copy import deepcopy
from xml.etree import ElementTree as E


def extend(base, groups, buffs, node, effect, loc):
    # Clone the native early horde pools: preserve native zombie variety and all
    # stage counts/durations/concurrency. Other spawners never get redirected.
    vanilla_groups = E.parse(base / 'entitygroups.xml')
    native_stages = E.parse(base / 'gamestages.xml')
    patches = E.Element('configs')
    append = node(groups, 'append', xpath='/entitygroups')
    created = set()
    mix = [('delveCorruptedWalker', .09), ('delveDemonSpawn', .05),
           ('delveImp', .03), ('delveHellhound', .014),
           ('delvePossessedSoldier', .01), ('delveWarpedBrute', .006)]
    for stage in native_stages.findall("./spawner[@name='BloodMoonHorde']/gamestage"):
        if int(stage.get('stage')) > 40:
            continue
        for spawn in stage.findall('spawn'):
            original = spawn.get('group')
            name = 'delveIncursion_' + original
            if name not in created:
                source = vanilla_groups.find(f"./entitygroup[@name='{original}']")
                assert source is not None
                group = deepcopy(source)
                group.set('name', name)
                total = sum(float(e.get('p', '1')) for e in group.findall('e'))
                for entry in group.findall('e'):
                    entry.set('p', str(float(entry.get('p', '1')) / total * .8))
                for enemy, weight in mix:
                    node(group, 'e', n=enemy, p=weight)
                append.append(group)
                created.add(name)
            # One set for every matching source pool within the selected stage.
            xpath = f"/gamestages/spawner[@name='BloodMoonHorde']/gamestage[@stage='{stage.get('stage')}']/spawn[@group='{original}']/@group"
            if not any(p.get('xpath') == xpath for p in patches):
                node(patches, 'set', xpath=xpath).text = name

    for name, roster in [
        ('delveBorderSkirmish', [('delveCorruptedWalker', 6), ('delveDemonSpawn', 3), ('delveImp', 1)]),
        ('delveBorderHeavy', [('delvePossessedSoldier', 3), ('delveWarpedBrute', 1)]),
        ('delveBorderHunters', [('delveHellhound', 1)])]:
        group = node(append, 'entitygroup', name=name)
        for enemy, weight in roster:
            node(group, 'e', n=enemy, p=weight)

    for name, title, description, duration, effects in [
        ('delveWardenScaling', 'Incursion Champion', 'Health scales with the initial nearby participants.', 0,
         [('HealthMax', 'base_set', '@$delveBossHealth')]),
        ('delveWardenWindup', 'Bracing', 'The Warden slows before a powerful assault.', 5,
         [('WalkSpeed', 'perc_add', -.75), ('RunSpeed', 'perc_add', -.75), ('EntityDamage', 'perc_add', -.5)]),
        ('delveWardenAssault', 'Ashbound Assault', 'A short burst of speed and melee damage. Keep your distance.', 7,
         [('WalkSpeed', 'perc_add', .25), ('RunSpeed', 'perc_add', .25), ('EntityDamage', 'perc_add', .35)]),
        ('delveWardenRecovery', 'Spent', 'The Warden slows and strikes weakly. Counterattack now.', 7,
         [('WalkSpeed', 'perc_add', -.6), ('RunSpeed', 'perc_add', -.6), ('EntityDamage', 'perc_add', -.5)])]:
        buff = node(buffs, 'buff', name=name, name_key=loc(name, title),
                    description_key=loc(name+'Desc', description), icon='ui_game_symbol_skull')
        node(buff, 'stack_type', value='replace')
        node(buff, 'duration', value=duration)
        eg = node(buff, 'effect_group')
        for stat, operation, value in effects:
            effect(eg, stat, value, operation)
    return patches

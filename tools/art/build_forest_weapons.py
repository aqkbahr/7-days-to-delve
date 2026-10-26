"""Field/Forged original weapon, focus and ammunition assets. Blender 5.2."""
import bpy,math,random,json,os,sys,ast,xml.etree.ElementTree as ET
import numpy as np
from mathutils import Vector
sys.path.insert(0,os.path.dirname(__file__))
from weapon_surfaces import weapon_surfaces
from weapon_detail import detail
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
OUT=os.path.join(ROOT,'src/Art/ForestWeapons');os.makedirs(OUT,exist_ok=True)
existing_catalogue=os.path.join(OUT,'catalogue.json')
if os.path.exists(existing_catalogue) and any(a.get('art_revision','').startswith('WeaponRebuild') for a in json.load(open(existing_catalogue))['weapons']):
 print('Preserving reconstructed weapon sources and material maps; use rebuild_weapon_models.py for this art revision.',flush=True);sys.exit(0)
tree=ast.parse(open(os.path.join(ROOT,'tools/art/build_thornback.py')).read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','ell','tube')],type_ignores=[]),'original_geometry_helpers','exec'))
base_tube=tube
def tube(name,points,radii,tile,bone,sides=10):
 o=base_tube(name,points,radii,tile,bone,sides)
 # Longitudinal grain follows the shaft instead of restarting on every smart-UV island.
 if tile in (0,4,11):
  row,col=divmod(tile,4);uv=o.data.uv_layers.active
  for face in o.data.polygons:
   if len(face.vertices)!=4:continue
   ids=[o.data.loops[k].vertex_index for k in face.loop_indices];seam=any(i%sides==sides-1 for i in ids) and any(i%sides==0 for i in ids)
   for k in face.loop_indices:
    vi=o.data.loops[k].vertex_index;u=(vi%sides)/sides
    if seam and vi%sides==0:u=1
    v=(vi//sides)/(len(points)-1);uv.data[k].uv=((col+.03+u*.94)/4,(row+.03+v*.94)/4)
 return o
entries=[
 ('delveBoneDagger','Wayfarer Dagger','dagger',0),('delveOakCudgel','Oak Cudgel','mace',0),('delveAshSpear','Ashwood Spear','spear',0),('delveLeatherKnuckles','Wayfarer Handwraps','wraps',0),('delveBorderBow','Border Scout Bow','bow',0),('delveStarterWand','Spark Wand','wand',0),('delveStarterStaff','Ember Staff','staff',0),('delveStarterTotem','Withering Totem','hex',0),('delveMendingTotem','Mending Totem','heal',0),
 ('delveForgedDagger','Balanced Iron Dagger','dagger',1),('delveForgedMace','Balanced Iron Mace','mace',1),('delveForgedSpear','Balanced Iron Spear','spear',1),('delveForgedKnuckles','Reinforced Handwraps','wraps',1),('delveForgedBow','Seasoned Longbow','bow',1),('delveForgedCrossbow','Border Crossbow','crossbow',1),('delveForgedWand','Carved Spark Wand','wand',1),('delveForgedStaff','Carved Ember Staff','staff',1),('delveForgedTotem','Carved Hex Totem','hex',1),('delveForgedMendingTotem','Carved Mending Totem','heal',1),('delveWardTotem','Protective Totem','ward',1)]
aliases={'delveIronDagger':'delveForgedDagger','delveIronMace':'delveForgedMace','delveIronSpear':'delveForgedSpear','delveHuntingBow':'delveForgedBow'}
runes=['delveWandRune','delveStaffRune','delveTotemRune','delveHealingRune','delveMooncapWandRune','delveMooncapStaffRune','delveMooncapTotemRune','delveMooncapHealingRune','delveEtchedWandRune','delveEtchedStaffRune','delveEtchedHexRune','delveEtchedHealingRune','delveEtchedWardRune']
items={e.attrib['name']:e for e in ET.parse(os.path.join(ROOT,'src/Delve/Config/items.xml')).findall('.//item')}
for id,_,_,_ in entries:
 if id not in items:raise ValueError('Missing gameplay item '+id)
for id in runes:entries.append((id,id,'rune',1 if 'Etched' in id else 0))
for id in ['ammoArrowStone','ammoArrowIron','ammoCrossbowBoltStone','ammoCrossbowBoltIron']:entries.append((id,id,'bolt' if 'Bolt' in id else 'arrow',1 if 'Iron' in id else 0))
random.seed(19)
surfaces=weapon_surfaces(bpy,np,OUT);image=surfaces['Atlas']
manifest=[]
def build(id,label,family,tier):
 global mat,parts
 for old in list(bpy.data.objects):bpy.data.objects.remove(old,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 scene=bpy.context.scene;scene.render.fps=30;scene.unit_settings.system='METRIC'
 out=os.path.join(OUT,id);os.makedirs(out,exist_ok=True)
 mat=bpy.data.materials.new(id+'_Surface');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);parts=[]
 for channel in ('Normal','Metallic','Emission'):
  tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=surfaces[channel]
  if channel=='Normal':
   nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tx.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
  elif channel=='Metallic':
   mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Metallic']);inv=mat.node_tree.nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;mat.node_tree.links.new(tx.outputs['Alpha'],inv.inputs[1]);mat.node_tree.links.new(inv.outputs[0],bs.inputs['Roughness'])
  else:mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.3
 magic=family in ('wand','staff','hex','heal','ward');small=family in ('rune','arrow','bolt')
 tip=1.27 if family=='spear' else 1.18 if family=='staff' else .50 if family=='wand' else (.48 if tier else .40) if family=='dagger' else .60 if family=='mace' else .34
 bones={'Root':((0,0,0),None),'Weapon':((0,0,0),'Root'),'GripRight':((0,0,0),'Weapon'),'GripLeft':((0,0,-.28 if family in ('staff','spear') else .08),'Weapon'),'Muzzle':((0,0,tip),'Weapon'),'EffectOrigin':((0,0,tip),'Weapon'),'EdgeBase':((0,0,.12),'Weapon'),'EdgeTip':((0,0,tip),'Weapon'),'Focus':((0,0,tip),'Weapon'),'LeftWrap':((-.20,0,0),'Root'),'BowUpper':((0,0,.1),'Weapon'),'BowLower':((0,0,-.1),'Weapon'),'String':((0,0,0),'Weapon'),'Ammo':((0,0,0),'Weapon')}
 if family in ('bow','crossbow'):
  bones['Muzzle']=((0,-.68,0) if family=='bow' else (0,-.57,.045),'Weapon');bones['EffectOrigin']=bones['Muzzle']
 if family=='crossbow':
  bones['BowUpper']=((0,-.36,0),'Weapon');bones['BowLower']=((0,-.36,0),'Weapon')
 bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name=id+'_Rig';rig.data.edit_bones.remove(rig.data.edit_bones[0])
 for n,(p,parent) in bones.items():
  b=rig.data.edit_bones.new(n);b.head=p;b.tail=Vector(p)+Vector((0,.08,0))
  if parent:b.parent=rig.data.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
 def rod(name,a,b,r,tile=0,bone='Weapon',r2=None):return tube(name,[a,b],[r,r if r2 is None else r2],tile,bone,12)
 def ring(name,p,r,width,tile=2,bone='Weapon'):
  bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=width,major_segments=24,minor_segments=6,location=p);return finish(bpy.context.object,tile,bone)
 def box(name,p,scale,tile=0,bone='Weapon'):
  bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=scale;bev=o.modifiers.new('Edge wear','BEVEL');bev.width=min(scale)*.12;bev.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bev.name);return finish(o,tile,bone)
 def blade(name,start,end,width,tile=2,bone='Weapon'):
  z=start;h=end-start;verts=[];faces=[]
  for t,w in [(0,1),(.09,1),(.55,.91),(.78,.75),(.93,.32),(1,.004)]:
   d=.010*(1-t*.85)
   for x,y in [(-w*width,0),(-w*width*.65,-d),(w*width*.65,-d),(w*width,0),(w*width*.65,d),(-w*width*.65,d)]:verts.append((x,y,z+h*t))
  for j in range(5):
   for k in range(6):faces.append((j*6+k,j*6+(k+1)%6,(j+1)*6+(k+1)%6,(j+1)*6+k))
  faces.extend([tuple(reversed(range(6))),tuple(range(30,36))])
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);return finish(o,tile,bone)
 def grip(z0,z1,r=.022,bone='Weapon'):
  rod('Leather grip',(0,0,z0),(0,0,z1),r,1,bone)
  wrap_band('Overlapped leather grip',0,z0+.01,z1-.01,r+.001,r+.001,.022,1,bone,8)
 def wrap_band(name,x,z0,z1,rx,ry,width,tile,bone,turns):
  vs=[];fs=[];steps=turns*32
  for j in range(steps+1):
   q=j/steps;a=q*math.tau*turns;z=z0+(z1-z0)*q
   # Subtle hand contour, with squared leather edges rather than rounded rope.
   contour=1+.055*math.sin(q*math.pi)
   for dr,dz in ((0,-width/2),(0,width/2),(.0015,-width/2),(.0015,width/2)):
    vs.append((x+(rx*contour+dr)*math.cos(a),(ry*contour+dr)*math.sin(a),z+dz))
  for j in range(steps):
   a=j*4;b=a+4
   fs.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
  fs.extend([(0,1,3,2),(steps*4,steps*4+2,steps*4+3,steps*4+1)])
  me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,tile,bone)
 def totem_body():
  outline=[(-.038,.035),(-.065,.075),(-.062,.17),(-.043,.218),(0,.232),(.043,.218),(.062,.17),(.065,.075),(.038,.035)]
  verts=[(x,y,z) for y in (-.029,.029) for x,z in outline];n=len(outline)
  faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  me=bpy.data.meshes.new('Carved focus stock');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Carved focus stock',me);bpy.context.collection.objects.link(o)
  bpy.context.view_layer.objects.active=o;bev=o.modifiers.new('Hand carved chamfer','BEVEL');bev.width=.008;bev.segments=3;bpy.ops.object.modifier_apply(modifier=bev.name);return finish(o,0,'Weapon')
 if family=='dagger':
  grip(-.12,.08);ell('Pommel',(0,0,-.14),(.03,.025,.025),2 if tier else 11,'Weapon',12,8);box('Crossguard',(0,0,.09),(.15 if tier else .10,.035,.025),2 if tier else 0)
  blade('Leaf blade',.10,.48 if tier else .40,.045 if tier else .035,2 if tier else 11)
  if tier:rod('Fuller',(0,-.013,.13),(0,-.01,.37),.003,3)
 elif family=='mace':
  rod('Oak haft',(0,0,-.16),(0,0,.46),.028,0,r2=.045 if not tier else .028);grip(-.15,.08,.03)
  if tier:
   ell('Iron mace core',(0,0,.45),(.065,.065,.13),3,'Weapon')
   for j in range(6):
    a=j*math.tau/6;outline=[(.035,.34),(.060,.35),(.092,.40),(.097,.47),(.075,.55),(.035,.57)]
    vs=[(r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a),z) for t in (-.008,.008) for r,z in outline];n=len(outline);fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    me=bpy.data.meshes.new('Forged petal flange');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Forged petal flange',me);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Hammered bevel','BEVEL');be.width=.002;be.segments=2;bpy.ops.object.modifier_apply(modifier=be.name);finish(o,2,'Weapon')
   ring('Head binding',(0,0,.35),.06,.009,2);ring('Pommel',(0,0,-.17),.035,.009,2)
  else:
   ell('Knotted cudgel head',(0,0,.42),(.065,.06,.16),0,'Weapon');ring('Leather reinforcement',(0,0,.34),.056,.006,1)
 elif family=='spear':
  rod('Ash shaft',(0,0,-.65),(0,0,.96),.02,0);grip(-.1,.16,.022);rod('Head socket',(0,0,.88),(0,0,1.0),.028,2 if tier else 1)
  blade('Spearhead',.98,1.27,.055,2 if tier else 13);rod('Butt cap',(0,0,-.68),(0,0,-.62),.024,2 if tier else 1)
 elif family=='wraps':
  for x,bone in [(0,'Weapon'),(-.20,'LeftWrap')]:
   wrap_band('Woven hand binding',x,-.058,.047,.047,.040,.023,1 if tier else 14,bone,6)
   for j in range(4):box('Knuckle pad',(x+(j-1.5)*.022,-.043,.055),(.022,.018,.032),2 if tier else 5,bone)
   box('Palm binding',(x,.039,.015),(.085,.016,.08),1,bone)
 elif family=='bow':
  length=.65 if tier else .52;grip(-.09,.09,.022)
  for sign,bone in [(1,'BowUpper'),(-1,'BowLower')]:
   pts=[(0,0,sign*.08),(0,-.10,sign*length*.5),(0,-.09,sign*length*.82),(0,.025,sign*length)]
   tube('Recurved bow limb',pts,[.026,.022,.017,.009],0,bone,12)
   if tier:tube('Laminated backing',[(.012,y,z) for _,y,z in pts],[.008,.007,.005,.002],4,bone,8)
   string=rod('Bowstring',(0,.025,sign*length),(0,.025,0),.002,11,'String');string.vertex_groups.clear()
   string.vertex_groups.new(name=bone).add(list(range(12)),1,'REPLACE');string.vertex_groups.new(name='String').add(list(range(12,24)),1,'REPLACE')
  rod('Nocked shaft',(0,-.65,0),(0,.06,0),.006,0,'Ammo');ell('Arrowhead',(0,-.68,0),(.012,.035,.008),2 if tier else 13,'Ammo',8,4)
 elif family=='crossbow':
  # Shaped stock: slender forward rail, narrow wrist and broad angled butt.
  verts=[]
  for y,w,top,bottom in [(-.47,.024,.033,-.028),(-.32,.034,.037,-.035),(-.04,.030,.037,-.038),(.10,.026,.030,-.045),(.19,.040,.035,-.075),(.30,.043,.018,-.085)]:
   verts.extend([(-w,y,top),(w,y,top),(w,y,bottom),(-w,y,bottom)])
  faces=[(3,2,1,0),(20,21,22,23)]+[(j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k) for j in range(5) for k in range(4)]
  me=bpy.data.meshes.new('Shaped crossbow stock');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Shaped crossbow stock',me);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Rounded stock edges','BEVEL');be.width=.005;be.segments=3;bpy.ops.object.modifier_apply(modifier=be.name);finish(o,0,'Weapon');grip(-.12,.04,.024)
  for sign,bone in [(1,'BowUpper'),(-1,'BowLower')]:
   prod=tube('Steel prod',[(0,-.36,0),(sign*.18,-.40,0),(sign*.36,-.30,0)],[.024,.018,.011],2,bone,10)
   for vert in prod.data.vertices:vert.co.z*=.38
   string=rod('Crossbow string',(sign*.36,-.30,0),(0,.02,0),.003,11,'String');string.vertex_groups.clear()
   string.vertex_groups.new(name=bone).add(list(range(12)),1,'REPLACE');string.vertex_groups.new(name='String').add(list(range(12,24)),1,'REPLACE')
  box('Trigger housing',(0,.04,-.065),(.035,.08,.045),2);rod('Loaded bolt',(0,-.57,.045),(0,.015,.045),.006,0,'Ammo')
  ring('Stirrup',(0,-.45,0),.055,.008,2)
 elif magic:
  color={'wand':6,'staff':7,'hex':8,'heal':9,'ward':10}[family]
  if family in ('wand','staff'):
   start=-.52 if family=='staff' else -.12;end=1.0 if family=='staff' else .32;rod('Carved wooden shaft',(0,0,start),(0,0,end),.021 if family=='wand' else .026,0,r2=.031);grip(-.10,.08,.026)
   if tier:
    for z in [start+.04,end-.05]:ring('Forged collar',(0,0,z),.03,.007,2)
   core=end+.08
   for sign in (-1,1):tube('Forked focus crown',[(0,0,end-.05),(sign*.065,0,end+.05),(sign*.04,0,end+.18)],[.022,.015,.006],0 if not tier else 2,'Weapon',9)
   ell('Faceted focus',(0,0,core),(.039,.034,.075),color,'Focus',8,4)
  else:
   grip(-.14,.04,.026);totem_body()
   if family=='hex':
    for sign in (-1,1):tube('Hex horns',[(sign*.045,0,.19),(sign*.095,0,.28),(sign*.065,0,.35)],[.022,.016,.001],11,'Weapon',8)
    ell('Hex eye',(0,-.04,.15),(.03,.02,.035),color,'Focus',8,4)
   elif family=='heal':
    for sign in (-1,1):ell('Leaf crown',(sign*.045,0,.25),(.035,.018,.08),color,'Focus',12,6)
    ring('Healing circle',(0,0,.23),.062,.012,11)
   else:
    o=blade('Ward shield',.08,.31,.10,2);o.rotation_euler.y=0;ell('Ward stone',(0,-.025,.20),(.035,.022,.05),color,'Focus',8,4)
   if tier:
    for z in (.055,.20):box('Metal totem band',(0,-.037,z),(.13,.009,.012),2)
  # Distinct physical rune marks, visible without glow.
  z=.09 if family not in ('staff','wand') else .19 if family=='wand' else .72
  mark_y=.031 if family not in ('staff','wand') else -.032
  for j in range(3):rod('Inscribed mark',(-.014,mark_y,z+j*.035),(.014,mark_y,z+.022+j*.035),.002,color)
 elif family=='rune':
  color=6 if 'Wand' in id else 7 if 'Staff' in id else 9 if 'Healing' in id else 10 if 'Ward' in id else 8
  bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.065,depth=.018);o=bpy.context.object;finish(o,13 if not tier else 2,'Weapon')
  # Top-face symbols distinguish functions through geometry as well as color.
  shape=[(-.03,0),(.0,.035),(.03,0),(0,-.035),(-.03,0)] if color==6 else [(-.03,-.025),(0,.035),(.03,-.025)] if color==7 else [(-.035,.02),(.035,-.02),(-.035,-.02),(.035,.02)] if color==8 else [(-.035,0),(.035,0),(0,0),(0,.035),(0,-.035)] if color==9 else [(-.03,.03),(.03,.03),(.025,-.02),(0,-.04),(-.025,-.02),(-.03,.03)]
  # Separate capped strokes remain valid across 90-degree and reversing turns.
  for a,b in zip(shape,shape[1:]):rod('Raised rune',(a[0],a[1],.012),(b[0],b[1],.012),.003,color)
  if 'Mooncap' in id:ring('Mooncap ring',(0,0,.013),.052,.002,11)
  if tier:
   for j in range(3):ell('Tier stud',(.05*math.cos(j*math.tau/3),.05*math.sin(j*math.tau/3),.014),(.005,.005,.003),11,'Weapon',8,4)
 elif family in ('arrow','bolt'):
  length=.72 if family=='arrow' else .43;rod('Shaft',(0,0,-length/2),(0,0,length/2),.005,0);blade('Ammunition head',length/2,length/2+.055,.016,2 if tier else 13)
  for j in range(3):
   a=j*math.tau/3;o=box('Fletching',(.012*math.cos(a),.012*math.sin(a),-length/2+.06),(.025,.002,.085),11);o.rotation_euler.z=a
 detail(dict(globals(),**locals()))
 # Harden planar bevels while retaining smooth rounded handles and fittings.
 for o in parts:
  if any(s in o.name.lower() for s in ('blade','head','shield','flange','stock','tiller','housing','pad','body','plate','ricasso','focus')):
   for p in o.data.polygons:p.use_smooth=False
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();mesh=bpy.context.object;mesh.name='Weapon_LOD0';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 mod=mesh.modifiers.new('Skin','ARMATURE');mod.object=rig;mesh.parent=rig;lods=[mesh]
 for level,ratio in [(1,.5),(2,.22)]:
  o=mesh.copy();o.data=mesh.data.copy();bpy.context.collection.objects.link(o);o.name='Weapon_LOD'+str(level)
  for m in list(o.modifiers):o.modifiers.remove(m)
  bpy.context.view_layer.objects.active=o;m=o.modifiers.new('LOD','DECIMATE');m.ratio=ratio;bpy.ops.object.modifier_apply(modifier=m.name);m=o.modifiers.new('Skin','ARMATURE');m.object=rig;lods.append(o)
 clips={'Idle':(2,True)} if small else {'Idle':(3,True),'Equip':(.6,False),'Unequip':(.5,False),'Aim':(1,True),'Recover':(.6,False)}
 if not small:
  clips.update({'Cast':(.65,False),'Channel':(2,True),'Recharge':(1.8,False),'EmptyCast':(.35,False)} if magic else {'Draw':(.9,False),'Hold':(1,True),'Release':(.35,False),'Reload':(1.4,False)} if family in ('bow','crossbow') else {'LightAttack':(.6,False),'HeavyAttack':(.95,False),'Block':(1,True)})
 def rot(n,x=0,y=0,z=0):rig.pose.bones[n].rotation_euler=tuple(math.radians(a) for a in (x,y,z))
 for name,(duration,loop) in clips.items():
  action=bpy.data.actions.new(name);action.use_fake_user=True;action['loop']=loop;rig.animation_data_create();rig.animation_data.action=action;last=round(duration*30)
  for f in range(last+1):
   scene.frame_set(f+1);q=f/last;wave=math.sin(math.tau*q);pulse=math.sin(math.pi*q)
   for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
   if not small:
    if name=='Idle':rot('Weapon',0,.7*wave,.3*wave)
    if name in ('Equip','Unequip'):
     t=(1-q) if name=='Equip' else q;rot('Weapon',-35*t,0,15*t);rig.pose.bones['Weapon'].location.z=-.2*t
    if name=='Aim':rot('Weapon',-8+.2*wave);rig.pose.bones['Weapon'].location.y=-.06
    if name=='Recover':rot('Weapon',-10*(1-q));rig.pose.bones['Weapon'].location.y=.03*pulse
    if name in ('LightAttack','HeavyAttack'):
     strength=1 if name=='LightAttack' else 1.45;t=math.sin(math.pi*q)
     if family=='spear':rig.pose.bones['Weapon'].location.y=-.40*t*strength;rot('Weapon',-70)
     elif family=='wraps':rig.pose.bones['Weapon'].location.y=-.24*t*strength;rig.pose.bones['LeftWrap'].location.y=-.18*math.sin(math.pi*max(0,q-.25))
     else:rot('Weapon',-45*t*strength,15*t,55*math.sin(math.tau*q)*strength)
    if name=='Block':rot('Weapon',0,0,55+.3*wave)
    if name in ('Draw','Hold','Release','Reload'):
     t=q if name=='Draw' else 1 if name=='Hold' else max(0,1-q*5) if name=='Release' else math.sin(math.pi*q)
     rig.pose.bones['String'].location.y=.18*t
     if family=='crossbow':rot('BowUpper',0,0,8*t);rot('BowLower',0,0,-8*t)
     else:rot('BowUpper',-8*t);rot('BowLower',8*t)
     rig.pose.bones['Ammo'].location.y=.18*t
     if name=='Release':rig.pose.bones['Ammo'].scale=(max(.001,1-q*12),)*3
    if name=='Cast':rot('Weapon',-18*pulse,0,4*pulse);rig.pose.bones['Focus'].scale=(1+.1*pulse,)*3
    if name=='Channel':rot('Weapon',-8+2*wave);rot('Focus',0,0,12*wave)
    if name=='Recharge':rot('Weapon',15*pulse,0,20*pulse);rot('Focus',0,0,180*q);rig.pose.bones['Focus'].location.z=.03*pulse
    if name=='EmptyCast':rot('Weapon',-5*pulse,0,4*wave)
   for b in rig.pose.bones:
    b.keyframe_insert('rotation_euler',frame=f+1,group=b.name);b.keyframe_insert('location',frame=f+1,group=b.name);b.keyframe_insert('scale',frame=f+1,group=b.name)
 rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_start=1;scene.frame_end=round(clips['Idle'][0]*30)+1;scene.frame_set(1)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in lods:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.fbx(filepath=os.path.join(out,id+'.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
 counts={}
 for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
 for o in lods[1:]:o.hide_render=True;o.hide_set(True)
 # Editable scene opens in the idle pose; preview helpers stay out of FBX.
 d=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',d);bpy.context.collection.objects.link(cam);scene.camera=cam;cam.location=(2,-3,1.4);cam.rotation_euler=(Vector((0,0,.25))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=2.6 if family in ('staff','spear','bow') else 1.2
 for name,power,loc in [('Key',650,(2,-3,4)),('Fill',350,(-2,-1,2))]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=3;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,id+'.blend'))
 data={'id':id,'name':label,'family':family,'tier':'Forged' if tier else 'Field','bones':list(bones),'triangles':counts,'animations':{n:{'seconds':d,'loop':l} for n,(d,l) in clips.items()},'gameplay_events':False,'status':'quality revision 2; preserved integrated rig/socket contract; see artifacts/weapon-quality-v2/ACCEPTANCE.txt'}
 json.dump(data,open(os.path.join(out,'asset-manifest.json'),'w'),indent=2);manifest.append(data);print('WEAPON_BUILD_PASS',id,flush=True)
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
prior={}
if requested:
 old=json.load(open(os.path.join(OUT,'catalogue.json')));prior={a['id']:a for a in old['weapons']}
for e in entries:
 if not requested or e[0] in requested or ('runes' in requested and e[2]=='rune'):build(*e)
if requested:
 prior.update({a['id']:a for a in manifest});manifest=[prior[e[0]] for e in entries]
json.dump({'weapons':manifest,'aliases':aliases,'scope':'20 weapon/focus variants, 13 rune tokens, 4 ammunition variants','axes':'Blender Z-up; bow/bolt aim -Y -> Unity +Z; grip pivot at origin; lengths in metres','integration':'Preserves the integrated held presentation contract. Revised bundle is staged for combined-package integration; see quality acceptance report.'},open(os.path.join(OUT,'catalogue.json'),'w'),indent=2)
open(os.path.join(OUT,'PROVENANCE.txt'),'w').write('Original project-authored geometry, five procedural PBR maps, rigs and prop animations. No native meshes, textures or motion clips copied. Original helper functions reused from build_thornback.py. Generators: build_forest_weapons.py, weapon_detail.py, weapon_surfaces.py. Native gameplay definitions only supply stable IDs and coverage.\n')
print('WEAPON_BATCH_PASS',len(manifest),flush=True)

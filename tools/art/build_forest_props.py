"""Original Forest station, crop, supply and gathering-tool review assets. Blender 5.2."""
import bpy,math,random,json,os,sys,ast,csv,traceback,xml.etree.ElementTree as ET
import numpy as np
from mathutils import Vector,Matrix
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));OUT=os.path.join(ROOT,'src/Art/ForestProps');os.makedirs(OUT,exist_ok=True)
tree=ast.parse(open(os.path.join(ROOT,'tools/art/build_thornback.py')).read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','ell','tube')],type_ignores=[]),'original_helpers','exec'))
old_finish=finish
def finish(o,tile=0,bone='Root'):
 bpy.ops.object.select_all(action='DESELECT');o=old_finish(o,tile,bone);tag=o.data.attributes.new('atlas_tile','INT','FACE')
 for d in tag.data:d.value=tile
 return o
input_paths=['src/Delve/Config/Localization.csv','src/ZDelveForest/Config/Localization.csv','src/Delve/Config/items.xml','src/Art/ForestWeapons/catalogue.json']
if all(os.path.exists(os.path.join(ROOT,p)) for p in input_paths):
 labels={}
 for file in input_paths[:2]:
  for row in csv.DictReader(open(os.path.join(ROOT,file),encoding='utf-8-sig')):labels[row['Key']]=row.get('english') or row['Key']
 done=json.load(open(os.path.join(ROOT,input_paths[3])));doneids={x['id'] for x in done['weapons']}|set(done['aliases'])
 items=[x.attrib['name'] for x in ET.parse(os.path.join(ROOT,input_paths[2])).findall('.//item')]
 json.dump({'labels':labels,'item_ids':items,'already_authored_ids':sorted(doneids)},open(os.path.join(OUT,'generation-input.json'),'w'),indent=2)
else:
 # Portable review kit uses a snapshot of project-authored identity/label inputs.
 source=json.load(open(os.path.join(OUT,'generation-input.json')));labels=source['labels'];items=source['item_ids'];doneids=set(source['already_authored_ids'])
stations=[('delveFieldHearth','hearth'),('delveForgeAnvil','forge'),('delveSawKit','saw'),('delveOutfittingKit','outfitter'),('delveMortarKit','apothecary'),('delveSortingTable','sorter'),('delveInscriptionKit','inscription'),('delveFarmDispatch','desk'),('delveCompostBin','composter'),('delveDryingRack','dryrack'),('delveGrainMill','mill'),('delvePreservingCrock','crock'),('delveFermentingBarrel','barrel'),('delveRainCollector','collector')]
entries=[{'id':i,'kind':'station','family':f} for i,f in stations];aliases={}
for family in ('Bramble','Yarrow','Thyme','Mooncap'):
 for stage,suffix in [(1,'1'),(2,'2'),(3,'3Harvest'),(4,'HarvestedVisual')]:entries.append({'id':'plantedDelve'+family+suffix,'kind':'plant','family':family,'stage':stage,'visual_only':stage==4})
 aliases['plantedDelve'+family+'3HarvestPlayer']='plantedDelve'+family+'3Harvest'
 entries.append({'id':'plantedDelve'+family+'1_Seed','kind':'item','family':'seed','plant':family,'visual_only':True})
for id in items+['delveThornhide','delveGloomPelt','delveForestCrystal','drinkJarEmpty','drinkJarRiverWater','drinkJarBoiledWater']:
 if id.startswith('armor') or id in doneids:continue
 entries.append({'id':id,'kind':'tool' if id in ('delveForgedAxe','delveForgedPickaxe','delveForgedShovel') else 'item','family':id})
assert len({e['id'] for e in entries})==len(entries)
N=1024;cell=256;px=np.ones((N,N,4),np.float32);yy,xx=np.mgrid[0:cell,0:cell];u=xx/cell;v=yy/cell;rng=np.random.default_rng(91)
# oak, dark wood, iron, stone, pottery, cloth, leaves, ripe berries, ivory flower,
# gold, mooncap/crystal, purple, charcoal/soil, water, food/bread, parchment.
colors=[(.30,.18,.085),(.14,.075,.035),(.34,.38,.40),(.28,.29,.25),(.40,.20,.10),(.42,.35,.23),(.15,.30,.105),(.55,.055,.15),(.75,.71,.51),(.48,.34,.12),(.18,.56,.65),(.34,.19,.43),(.055,.05,.035),(.12,.30,.39),(.52,.34,.12),(.70,.60,.39)]
for i,c in enumerate(colors):
 noise=rng.normal(0,.009,(cell,cell));grain=.02*np.sin(u*135+2*np.sin(v*16)) if i in (0,1) else .008*np.sin(u*200)*np.sin(v*200)
 row,col=divmod(i,4);px[row*cell:(row+1)*cell,col*cell:(col+1)*cell,:3]=np.clip(np.array(c)+(noise+grain)[:,:,None],.008,.95)
image=bpy.data.images.new('ForestPropAtlas',width=N,height=N);image.pixels.foreach_set(px.ravel());image.filepath_raw=os.path.join(OUT,'ForestPropAtlas.png');image.file_format='PNG';image.save();image.pack()
catalogue=[]
def build(spec):
 global parts,mat
 id=spec['id'];kind=spec['kind'];family=spec['family'];random.seed(id)
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 scene=bpy.context.scene;scene.render.fps=24;scene.unit_settings.system='METRIC'
 mat=bpy.data.materials.new(id+'_Surface');mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.75;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);parts=[]
 bones={'Root':(0,0,0),'Wind':(0,0,.025),'Tool':(0,0,.85),'Wheel':(0,0,.92),'Water':(0,0,.25),'Lid':(0,.25,.75)}
 bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='ForestPropRig';rig.data.edit_bones.remove(rig.data.edit_bones[0])
 for n,p in bones.items():
  b=rig.data.edit_bones.new(n);b.head=p;b.tail=Vector(p)+Vector((0,.08,0))
  if n!='Root':b.parent=rig.data.edit_bones['Root']
 bpy.ops.object.mode_set(mode='OBJECT')
 def box(name,p,s,tile=0,bone='Root'):
  bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);m=o.modifiers.new('Worn edges','BEVEL');m.width=min(s)*.1;m.segments=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);return finish(o,tile,bone)
 def rod(name,a,b,r,tile=0,bone='Root',r2=None):return tube(name,[a,b],[r,r if r2 is None else r2],tile,bone,10)
 def ring(name,p,r,minor,tile=2,bone='Root'):
  bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=minor,major_segments=24,minor_segments=6,location=p);o=bpy.context.object;o.name=name;return finish(o,tile,bone)
 def lathe(name,profile,p,tile,bone='Root',sides=24):
  vs=[];fs=[]
  for r,z in profile:
   for j in range(sides):a=math.tau*j/sides;vs.append((p[0]+r*math.cos(a),p[1]+r*math.sin(a),p[2]+z))
  for i in range(len(profile)-1):
   for j in range(sides):k=(j+1)%sides;fs.append((i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j))
  fs.extend([tuple(reversed(range(sides))),tuple((len(profile)-1)*sides+j for j in range(sides))]);return mesh(name,vs,fs,tile,bone)
 def mesh(name,vs,fs,tile,bone='Root'):
  d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return finish(o,tile,bone)
 def leaf(a,b,width,tile=6,bone='Root'):
  a=Vector(a);b=Vector(b);mid=a.lerp(b,.5);side=(b-a).cross(Vector((0,0,1)))
  if side.length<.001:side=Vector((1,0,0))
  side.normalize();vs=[a,mid+side*width,b,mid-side*width,mid+Vector((0,0,width*.25))];o=mesh('Veined leaf',vs,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],tile,bone);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Leaf thickness','SOLIDIFY');m.thickness=.002;bpy.ops.object.modifier_apply(modifier=m.name);return o
 def bowl(p=(0,0,0),r=.17,tile=4):
  lathe('Open bowl',[(r*.4,0),(r*.7,.025),(r,.10),(r*.98,.12),(r*.87,.115),(r*.61,.03),(r*.1,.024)],p,tile)
 def bottle(p=(0,0,0),color=10,scale=1):
  x,y,z=p;s=scale;lathe('Glazed bottle',[(.065*s,0),(.075*s,.02*s),(.075*s,.16*s),(.034*s,.21*s),(.029*s,.27*s)],p,color)
  rod('Cork',(x,y,z+.265*s),(x,y,z+.29*s),.031*s,0);ring('Bottle rim',(x,y,z+.255*s),.033*s,.006*s,9);box('Bottle label',(x,y-.075*s,z+.105*s),(.07*s,.008*s,.065*s),15)
 def herb(p=(0,0,0),family='Thyme',scale=1,bone='Root',ripe=True,dry=False,compact=False):
  p=Vector(p);s=scale
  for j in range(3 if compact else 5 if family!='Bramble' else 7):
   a=j*2.399;top=p+Vector((math.cos(a)*.12*s,math.sin(a)*.12*s,(.30+.08*(j%3))*s*(.65 if family=='Thyme' else 1)));rod('Herb stem',p,top,.005*s,0 if family=='Bramble' or dry else 6,bone)
   for k in range(1,3 if compact else 4):
    pos=p.lerp(top,k/4)
    for sign in (-1,1):
     end=pos+Vector((math.cos(a+sign)*(.05 if family=='Thyme' else .10)*s,math.sin(a+sign)*(.05 if family=='Thyme' else .10)*s,(.02 if family=='Thyme' else .045)*s));tile=5 if dry else 6
     if family=='Yarrow':
      rod('Yarrow leaf midrib',pos,end,.0018*s,tile,bone)
      tangent=end-pos;side=Vector((-tangent.y,tangent.x,0)).normalized()
      for k in range(1,4 if compact else 5):
       point=pos.lerp(end,k/5)
       for direction in (-1,1):leaf(point,point+side*(direction*.025*s)+tangent*.14,.006*s,tile,bone)
     else:leaf(pos,end,(.034 if family=='Bramble' else .018)*s,tile,bone)
   if ripe and family=='Yarrow':
    for k in range(4 if compact else 7):b=k*2.399;ell('Yarrow flower',top+Vector((.035*s*math.cos(b),.035*s*math.sin(b),.008*s*(k%2))),(.017*s,.017*s,.009*s),8,bone,8,4)
   if ripe and family=='Bramble':
    for k in range(3):ell('Brambleberry',top+Vector((.028*s*math.cos(k*2.1),.028*s*math.sin(k*2.1),-.02*s)),(.025*s,.025*s,.028*s),7,bone,10,6)
   if ripe and family=='Thyme':
    for k in range(3):ell('Thyme blossom',top+Vector((.012*s*math.cos(k*2.1),.012*s*math.sin(k*2.1),0)),(.009*s,.009*s,.007*s),9 if dry else 11,bone,8,4)
 def mushroom(p=(0,0,0),s=1,bone='Root'):
  x,y,z=p;rod('Mooncap stem',p,(x,y,z+.14*s),.025*s,8,bone,r2=.016*s);lathe('Mooncap hood',[(.015*s,.11*s),(.09*s,.12*s),(.10*s,.14*s),(.075*s,.18*s),(.02*s,.205*s)],p,10,bone,20)
  for k in range(6):a=k*math.tau/6;ell('Cap freckle',(x+.055*s*math.cos(a),y+.055*s*math.sin(a),z+.195*s),(.008*s,.008*s,.004*s),8,bone,8,4)
 def book(p=(0,0,0),tile=1,mark=0):
  x,y,z=p;box('Bound pages',(x,y,z+.028),(.25,.18,.045),15)
  for zz in (.004,.054):box('Book cover',(x,y,z+zz),(.27,.19,.012),tile)
  box('Book spine',(x-.129,y,z+.03),(.016,.19,.056),tile);symbol((x,y,z+.066),.04,mark)
 def symbol(p,r,index,tile=9):
  x,y,z=p;shapes=[[(0,-1),(0,1),(-.6,.3),(.6,.3)],[(0,1),(.65,0),(0,-1),(-.65,0),(0,1)],[(-.7,-.6),(.7,.6),(-.7,.6),(.7,-.6)],[(-.8,0),(.8,0),(0,0),(0,-.8),(0,.8)],[(-.8,.8),(0,-.8),(.8,.8)],[(-.8,-.5),(-.6,.7),(0,.1),(.6,.7),(.8,-.5)]]
  pts=shapes[index%len(shapes)]
  for a,b in zip(pts,pts[1:]):rod('Raised identity mark',(x+a[0]*r,y+a[1]*r,z),(x+b[0]*r,y+b[1]*r,z),r*.065,tile)
 def table():
  for x in (-.73,.73):
   for y in (-.32,.32):box('Braced leg',(x,y,.43),(.11,.11,.86),1)
   box('End brace',(x,0,.27),(.085,.75,.085),0)
  for j in range(6):box('Worktop plank',(-.75+j*.30,0,.86),(.294,.88,.09),0)
  box('Lower stretcher',(0,.28,.25),(1.55,.08,.09),1)
 def barrel(p=(0,0,0),s=1,lid=True):
  x,y,z=p;lathe('Coopered staves',[(.27*s,0),(.31*s,.12*s),(.35*s,.42*s),(.31*s,.72*s),(.27*s,.79*s)],p,0)
  for zz,rr in [(.08,.30),(.24,.335),(.57,.335),(.73,.30)]:ring('Iron hoop',(x,y,z+zz*s),rr*s,.018*s,2)
  for j in range(12):a=j*math.tau/12;rod('Stave seam',(x+.30*s*math.cos(a),y+.30*s*math.sin(a),z+.12*s),(x+.30*s*math.cos(a),y+.30*s*math.sin(a),z+.72*s),.003*s,1)
  if lid:lathe('Barrel lid',[(.27*s,.79*s),(.27*s,.82*s)],p,0)
 def sack(p=(0,0,0),tile=5,content=12):
  x,y,z=p;lathe('Gathered sack',[(.10,0),(.15,.04),(.17,.19),(.11,.30),(.085,.32),(.08,.30),(.11,.27)],p,tile);ring('Tied sack rim',(x,y,z+.295),.10,.012,0)
  for j in range(7):a=j*2.399;ell('Sack contents',(x+.06*math.cos(a),y+.06*math.sin(a),z+.29),(.035,.03,.025),content,'Root',8,4)
 def bundle(tile=5):
  for j in range(3):box('Folded material',(0,0,.03+j*.035),(.32,.22,.03),tile)
  for x in (-.10,.10):box('Bundle strap',(x,0,.075),(.018,.23,.13),1)
 def blade(p,scale,shape='axe'):
  x,y,z=p;s=scale
  vs=[(x-.025*s,y-.018*s,z-.12*s),(x-.025*s,y+.018*s,z+.10*s),(x+.18*s,y+.018*s,z+.13*s),(x+.22*s,y,z-.15*s),(x+.02*s,y,z-.09*s)]
  o=mesh('Forged tool head',vs,[(0,1,2,3,4)],2);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Tool thickness','SOLIDIFY');m.thickness=.025*s;bpy.ops.object.modifier_apply(modifier=m.name)
 if kind=='station':
  if family in ('saw','outfitter','apothecary','sorter','inscription','desk','mill'):table()
  if family=='hearth':
   box('Stone hearth slab',(0,0,.09),(1.65,.84,.18),3)
   for j in range(12):a=j*math.tau/12;ell('Hearth stone',(.52*math.cos(a),.27*math.sin(a),.24),(.18,.12,.13),3,'Root',10,6)
   for y in (-.13,.13):rod('Charred log',(-.35,y,.22),(.35,y,.22),.06,12)
   for x in (-.64,.64):rod('Pot support',(x,0,.26),(x,0,1.12),.035,2)
   rod('Pot crossbar',(-.64,0,1.12),(.64,0,1.12),.025,2);rod('Hanging hook',(0,0,1.12),(0,0,.83),.015,2)
   lathe('Cooking cauldron',[(.12,.38),(.28,.48),(.27,.70),(.24,.76),(.21,.74),(.23,.51),(.10,.43)],(0,0,0),2);ring('Cauldron handle',(0,0,.82),.19,.012,2)
  elif family=='forge':
   box('Forge base',(-.35,0,.30),(.95,.85,.60),3)
   for z in (.65,.85,1.05):
    for x in (-.72,.02):box('Forge arch pier',(x,.10,z),(.18,.65,.19),3)
   box('Arch crown',(-.35,.10,1.19),(.95,.65,.19),3);box('Chimney',(-.35,.24,1.52),(.43,.35,.51),3)
   box('Coal bed',(-.35,-.06,.62),(.56,.55,.04),12)
   rod('Anvil stump',(.56,0,0),(.56,0,.62),.27,0);box('Anvil heel',(.56,0,.65),(.45,.28,.08),2);box('Anvil waist',(.56,0,.75),(.20,.17,.18),2);box('Anvil face',(.56,0,.88),(.47,.24,.10),2);rod('Anvil horn',(.70,0,.87),(.91,0,.87),.10,2,r2=.006)
   ell('Bellows leather',(-.35,-.29,.80),(.23,.14,.07),1,'Lid',16,8)
  elif family=='saw':
   for y in (-.16,.12):box('Seasoning timber',(0,y,.95),(1.5,.20,.10),0)
   for x in (-.45,.45):box('Saw handle post',(x,-.30,1.17),(.04,.035,.38),0,'Tool')
   box('Frame saw spine',(0,-.30,1.35),(.94,.04,.035),0,'Tool');box('Steel saw blade',(0,-.30,1.02),(.94,.015,.075),2,'Tool')
   for j in range(18):mesh('Saw tooth',[(-.44+j*.05,-.30,.99),(-.415+j*.05,-.30,.965),(-.39+j*.05,-.30,.99)],[(0,1,2),(2,1,0)],2,'Tool')
   for j in range(3):box('Drying timber',(-.25,.12,.10+j*.07),(1.2,.22,.065),0)
  elif family=='outfitter':
   box('Cutting hide',(-.18,0,.92),(.8,.6,.018),1);rod('Cloth bolt',(.54,-.22,.99),(.54,.25,.99),.11,5)
   for x in (-.65,-.50):rod('Awl handle',(x,.18,.93),(x,.18,1.12),.025,0);rod('Awl point',(x,.18,1.12),(x,.18,1.20),.008,2)
   for y in (-.08,.08):rod('Shears',(-.4,y,.95),(-.05,-y,.95),.013,2)
   for x in (.32,.55):rod('Thread spool',(x,.31,.93),(x,.31,1.04),.045,8)
  elif family=='apothecary':
   bowl((-.40,-.10,.92),.21,3);rod('Mortar pestle',(-.45,-.10,1.0),(-.31,-.10,1.30),.035,3)
   for j in range(4):bottle((.10+j*.18,.21,.92),[10,11,6,4][j],.65)
   herb((.25,-.20,.92),'Yarrow',.45);box('Herb cutting board',(.30,-.12,.925),(.65,.45,.025),1)
  elif family=='sorter':
   for x in (-.52,0,.52):
    box('Sorting tray',(x,0,.94),(.45,.65,.06),1)
    for y in (-.31,.31):box('Tray rim',(x,y,1.0),(.45,.025,.12),0)
    for j in range(7):ell('Ore sample',(x+random.uniform(-.16,.16),random.uniform(-.22,.22),1.02),(.06,.06,.05),3 if x<0 else 2 if x==0 else 12,'Root',8,4)
  elif family=='inscription':
   box('Slate carving bed',(-.15,0,.94),(1.0,.65,.07),3)
   for j in range(3):lathe('Rune blank',[(.10,0),(.10,.025)],(-.43+j*.29,0,.98),8,sides=12);symbol((-.43+j*.29,0,1.01),.065,j)
   rod('Carving chisel',(.57,-.26,.94),(.57,.15,.94),.018,2);book((.55,.25,.92),1,2)
  elif family=='desk':
   book((-.4,-.13,.92),1,0);box('Order parchment',(.16,-.12,.93),(.34,.27,.008),15)
   for j in range(3):box('Wax sealed parcel',(.57,.05,.99+j*.13),(.32,.35,.12),5)
   for x in (-.65,.65):rod('Notice board post',(x,.35,.90),(x,.35,1.75),.035,0)
   box('Notice board',(0,.35,1.48),(1.36,.05,.47),1)
   for x in (-.42,0,.42):box('Posted order',(x,.315,1.48),(.29,.012,.34),15);ell('Order seal',(x,.30,1.38),(.033,.008,.033),7,'Root',10,6)
  elif family=='composter':
   for x in (-.78,.78):
    for y in (-.34,.34):box('Compost corner post',(x,y,.43),(.09,.09,.86),1)
   for z in (.12,.30,.48,.66):
    for y in (-.34,.34):box('Ventilated compost slat',(0,y,z),(1.65,.055,.14),0)
    for x in (-.78,.78):box('Compost end slat',(x,0,z),(.055,.70,.14),0)
   box('Compost fill',(0,0,.50),(1.5,.61,.20),12)
   for j in range(12):leaf((random.uniform(-.6,.6),random.uniform(-.25,.25),.61),(random.uniform(-.6,.6),random.uniform(-.25,.25),.64),.07,6)
  elif family=='dryrack':
   for x in (-.76,.76):
    for y in (-.30,.30):rod('Rack upright',(x,y,0),(x,y,1.66),.04,0)
   for z in (.64,1.12,1.62):
    for y in (-.30,.30):rod('Drying rail',(-.76,y,z),(.76,y,z),.025,0)
    for j in range(3):
     x=-.5+j*.50;rod('Hanging twine',(x,0,z),(x,0,z-.08),.004,5);start=len(parts);pivot=Vector((x,0,z-.08));herb(pivot,'Yarrow' if j%2 else 'Thyme',.65,compact=True)
     flip=Matrix.Translation(pivot)@Matrix.Rotation(math.pi,4,'X')@Matrix.Translation(-pivot)
     for hanging in parts[start:]:hanging.matrix_world=flip@hanging.matrix_world
  elif family=='mill':
   lathe('Lower quern',[(.30,0),(.32,.10)],(0,0,.91),3);lathe('Turning millstone',[(.32,.11),(.30,.24),(.09,.26)],(0,0,.91),3,'Wheel');rod('Mill handle',(.22,0,1.15),(.22,0,1.38),.025,0,'Wheel');lathe('Grain hopper',[(.07,0),(.16,.20),(.14,.20),(.05,.02)],(0,0,1.17),0)
   sack((-.58,.05,.91),5,14);bowl((.60,-.15,.91),.15,4)
  elif family=='crock':
   for x,s in [(-.42,1),(.40,.8)]:
    lathe('Preserving crock',[(.24,0),(.32,.14),(.33,.53),(.25,.72),(.23,.75)],(x,0,0),4);lathe('Weighted lid',[(.27,.75),(.27,.79),(.07,.82)],(x,0,0),3);rod('Lid knob',(x,0,.82),(x,0,.88),.045,0)
   box('Crock shelf',(0,0,.025),(1.65,.84,.05),0)
  elif family=='barrel':
   for x in (-.44,.44):barrel((x,0,0));rod('Fermentation airlock',(x,0,.82),(x,0,1.03),.016,2);bottle((x+.10,0,.82),4,.35)
   rod('Tap outlet',(-.44,-.30,.20),(-.44,-.42,.20),.026,2);box('Tap handle',(-.44,-.37,.25),(.1,.02,.02),0)
  elif family=='collector':
   for x in (-1.0,1.0):
    for y in (-1.0,1.0):rod('Collector post',(x,y,0),(x,y,2.15),.055,0)
   lathe('Rain funnel',[(.14,.96),(.18,1.1),(1.16,2.1),(1.19,2.14),(1.13,2.14),(.12,1.05)],(0,0,0),5, sides=32)
   barrel((0,0,.05),1.1,False);lathe('Fill water surface',[(.27,0),(.27,.015)],(0,0,.30),13,'Water')
   box('Water level gauge',(.29,-.40,.56),(.06,.025,.49),5);box('Fill indicator',(.29,-.418,.38),(.055,.012,.025),10,'Water')
   box('Jar collection shelf',(0,-.87,.32),(1.75,.45,.07),0)
   for j in range(9):bottle((-.72+j*.18,-.87,.36),13,.45)
 elif kind=='plant':
  stage=spec['stage'];scale={1:.32,2:.68,3:1.25,4:.55}[stage]
  if family=='Mooncap':
   for j in range(2 if stage==1 else 5):a=j*2.399;mushroom((math.cos(a)*.12*scale,math.sin(a)*.12*scale,0),scale*(.6+.13*(j%3)),'Wind')
   if stage==4:
    # Harvested-state prop: clipped stems, not mature caps.
    for o in list(parts):bpy.data.objects.remove(o,do_unlink=True)
    parts=[]
    for j in range(5):a=j*2.399;rod('Cut mushroom stem',(.1*math.cos(a),.1*math.sin(a),0),(.1*math.cos(a),.1*math.sin(a),.04),.02,8,'Wind')
  else:herb(family=family,scale=scale*(1.6 if family=='Bramble' else 1),bone='Wind',ripe=stage==3)
 elif kind=='tool':
  rod('Ash tool haft',(0,0,-.46),(0,0,.48),.025,0);rod('Wrapped grip',(0,0,-.15),(0,0,.12),.029,1)
  for z in np.linspace(-.14,.11,10):ring('Grip winding',(0,0,z),.03,.003,5)
  if 'Pickaxe' in id:
   tube('Forged pick',[(-.35,0,.32),(-.19,0,.47),(0,0,.53),(.18,0,.47),(.35,0,.35)],[.004,.025,.045,.023,.003],2,'Root',10)
  elif 'Shovel' in id:
   o=mesh('Spade blade',[(-.12,0,.37),(.12,0,.37),(.14,-.015,.59),(0,-.035,.69),(-.14,-.015,.59),(0,-.03,.45)],[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5)],2);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Blade thickness','SOLIDIFY');m.thickness=.012;bpy.ops.object.modifier_apply(modifier=m.name)
  else:blade((0,0,.44),1)
 else:
  if family=='seed':
   box('Folded seed packet',(0,0,.015),(.15,.18,.03),15);symbol((0,0,.034),.045,('Bramble','Yarrow','Thyme','Mooncap').index(spec['plant']),6)
   for j in range(7):ell('Seed grain',(.09+random.random()*.05,random.uniform(-.07,.07),.008),(.006,.009,.005),14,'Root',8,4)
  elif id in ('resourceDelveThyme','resourceDelveYarrow','delveDriedThyme','delveDriedYarrow'):
   herb(family='Yarrow' if 'Yarrow' in id else 'Thyme',scale=.8,dry='Dried' in id);ring('Herb binding',(0,0,.09),.04,.008,5)
  elif id=='resourceDelveMooncap':
   for j in range(3):mushroom((j*.13-.13,0,0),.8+j*.1)
  elif id=='foodDelveBrambleberries':
   for j in range(12):a=j*2.399;ell('Berry cluster',(.07*math.cos(a),.07*math.sin(a),.025+.025*(j%3)),(.025,.025,.027),7,'Root',10,6)
   leaf((0,0,.06),(.13,.07,.08),.04)
  elif id in ('delveThornhide','delveGloomPelt','delveCuredLeather','delveWovenCloth'):
   tile=11 if 'Gloom' in id else 6 if 'Thorn' in id else 5 if 'Cloth' in id else 1;bundle(tile)
   if 'Thorn' in id:
    for j in range(6):x=-.12+j*.048;rod('Hide thorn',(x,0,.12),(x,0,.18+(.02 if j%2 else 0)),.012,0,r2=.001)
   if 'Gloom' in id:
    for j in range(9):x=-.14+j*.035;leaf((x,.08,.1),(x,.15,.1),.025,11)
  elif id=='delveForestCrystal':
   for j in range(5):a=j*2.399;x=.065*math.cos(a);y=.065*math.sin(a);lathe('Crystal point',[(.045,0),(.045,.14+j*.025),(.002,.22+j*.025)],(x,y,0),10,sides=6)
   for o in parts:
    for p in o.data.polygons:p.use_smooth=False
  elif 'Heritage' in id:
   heritage=['Human','Elf','Dwarf','Halfling','Orc','Tiefling'];index=next(i for i,n in enumerate(heritage) if n in id);lathe('Heritage seal',[(.09,0),(.09,.022)],(0,0,0),2,sides=24);ring('Seal border',(0,0,.024),.08,.006,9);symbol((0,0,.027),.05,index)
  elif any(s in id for s in ('Guide','Handbook')):book(tile=1 if 'Field' in id else 6 if 'Farm' in id else 11 if 'Readiness' in id else 2,mark=0 if 'Field' in id else 1 if 'Farm' in id else 2 if 'Processing' in id else 3)
  elif 'Notice' in id or 'Parcel' in id:
   index=next(i for i,n in enumerate(['Pantry','Herbs','Bread','Medicine','Rations']) if n in id)
   if 'Parcel' in id:
    box('Sealed supply parcel',(0,0,.10),(.35,.26,.20),5);box('Parcel twine',(0,0,.105),(.025,.27,.215),0);box('Parcel cross tie',(0,0,.105),(.36,.018,.215),0);z=.215
   else:box('Supply order parchment',(0,0,.008),(.25,.32,.016),15);z=.025
   lathe('Wax seal',[(.035,0),(.035,.009)],(0,0,z),[7,6,14,11,10][index]);symbol((0,0,z+.013),.025,index,8)
  elif id in ('delveRoughHandle','delveSeasonedTimber'):
   if id=='delveRoughHandle':rod('Shaped handle',(0,0,0),(0,0,.46),.025,0)
   else:
    for j in range(3):box('Seasoned plank',(0,(j-1)*.09,.04),(.50,.085,.08),0)
    for x in (-.17,.17):box('Timber binding',(x,0,.045),(.02,.28,.10),5)
  elif id=='delveLeatherBinding':
   for z in (.015,.035,.055):ring('Coiled leather strip',(0,0,z),.09,.012,1)
  elif id in ('delveIronFittings','delveDressedStone','delveRuneBlank'):
   for j in range(3):
    if 'Fittings' in id:box('Iron bracket',(0,j*.08-.08,.025),(.25,.025,.025),2);box('Bracket bend',(.11,j*.08-.08,.07),(.025,.025,.10),2)
    elif 'Stone' in id:box('Dressed stone',(0,0,.035+j*.075),(.26,.17,.07),3)
    else:lathe('Rune blank',[(.07,0),(.07,.022)],((j-1)*.075,0,.015*j),8,sides=12)
  elif id in ('delveCompost','delveMilledGrain','delveCharcoal','delveIronConcentrate','delveEmberSalts'):sack(content=14 if 'Grain' in id else 2 if 'Iron' in id else 9 if 'Salts' in id else 12)
  elif 'Repair' in id:
   bundle(5 if 'Focus' in id else 1);rod('Repair tool',(-.12,-.07,.14),(.13,.07,.14),.012,2)
   if 'Metal' in id:
    for j in range(3):box('Spare iron fitting',((j-1)*.07,0,.15),(.05,.08,.035),2)
   elif 'Focus' in id:lathe('Focus stone',[(.035,0),(.035,.03),(.002,.05)],(.09,0,.13),10,sides=6)
   else:rod('Bone needle',(-.13,.04,.15),(.13,.04,.15),.004,8)
  elif any(n in id for n in ('Poultice','Dressing')):
   bundle(8);leaf((-.1,0,.13),(.12,.05,.15),.05,6);box('Herbal dressing tie',(0,0,.08),(.025,.25,.16),6)
  elif any(n in id for n in ('Potion','Tincture','Draught','Spirit','Extract')):
   color=7 if 'Healing' in id else 6 if 'Stamina' in id else 9 if 'Ward' in id else 11 if 'Spirit' in id else 6;bottle(color=color);symbol((0,0,.294),.022,0 if 'Healing' in id else 3 if 'Stamina' in id else 4)
  elif id.startswith('drinkJar'):
   lathe('Open water jar',[(.075,0),(.09,.03),(.09,.16),(.07,.21),(.065,.22),(.057,.215),(.065,.17),(.08,.15),(.065,.025)],(0,0,0),4)
   if 'Empty' not in id:lathe('Visible jar water',[(.065,.17),(.065,.175)],(0,0,0),13 if 'Boiled' in id else 3)
  elif 'Tea' in id or 'Broth' in id:
   lathe('Drinking cup',[(.065,0),(.085,.015),(.095,.15),(.085,.16),(.078,.15),(.07,.025)],(0,0,0),4);lathe('Brew surface',[(.077,.13),(.077,.135)],(0,0,0),6 if 'Tea' in id else 14);o=ring('Cup handle',(.10,0,.08),.045,.009,4);o.rotation_euler.x=math.pi/2
  elif 'Preserve' in id:
   bottle(color=7,scale=1.2);box('Preserve cloth lid',(0,0,.325),(.10,.10,.025),5)
  elif 'Ration' in id:
   box('Ration wrapper',(0,0,.015),(.36,.26,.03),5);ell('Travel loaf',(-.07,0,.065),(.105,.08,.04),14,'Root',16,8);box('Dried meat',(.09,0,.06),(.12,.12,.055),4);leaf((-.15,-.1,.03),(.12,-.10,.04),.025,6)
   if 'Rations' in id:box('Ration strap',(0,0,.055),(.025,.28,.10),1)
  elif 'Bread' in id or 'Cakes' in id:
   for j in range(3 if 'Cakes' in id else 1):ell('Honeyberry cake' if 'Cakes' in id else 'Travel bread',((j-1)*.11 if 'Cakes' in id else 0,0,.055),(.075 if 'Cakes' in id else .18,.09,.05),14,'Root',16,8)
   for x in (-.08,0,.08):rod('Scored crust',(x,-.05,.10),(x,.05,.10),.004,15)
   if 'Cakes' in id:
    for x in (-.1,0,.1):ell('Berry topping',(x,0,.10),(.014,.014,.012),7,'Root',8,4)
  elif 'Skewer' in id:
   rod('Roasting skewer',(-.22,0,.045),(.22,0,.045),.008,0)
   for j in range(3):mushroom((-.12+j*.12,0,0),.45)
  elif id in ('foodDelveRoastedPumpkin','foodDelveSeasonedRoast','foodDelveIncursionSupper'):
   lathe('Serving platter',[(.15,0),(.23,.025),(.24,.04),(.21,.035),(.14,.018)],(0,0,0),4)
   if id=='foodDelveRoastedPumpkin':
    for j in range(3):
     y=(j-1)*.065;vs=[]
     for i in range(9):
      a=math.pi*i/8;vs.extend([(.15*math.cos(a),y-.025,.045+.065*math.sin(a)),(.15*math.cos(a),y+.025,.045+.065*math.sin(a))])
     fs=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(8)]+[tuple(range(0,18,2)),tuple(reversed(range(1,18,2)))];mesh('Roasted pumpkin wedge',vs,fs,14);rod('Pumpkin rind',(-.15,y,.045),(.15,y,.045),.008,6)
   else:
    ell('Roasted meat',(0,0,.085),(.15,.095,.07),4,'Root',20,10);rod('Roast bone',(-.2,0,.07),(.19,0,.07),.015,8);leaf((-.1,-.08,.11),(.12,-.07,.12),.025,6)
    if id=='foodDelveIncursionSupper':
     for j in range(5):a=j*math.tau/5;ell('Supper vegetables',(.18*math.cos(a),.16*math.sin(a),.06),(.028,.025,.025),14 if j%2 else 6,'Root',8,4)
  elif id.startswith('food'):
   bowl();lathe('Meal surface',[(.135,.075),(.135,.082)],(0,0,0),7 if 'Berr' in id else 14)
   for j in range(9):a=j*2.399;r=.09*(.5+.5*random.random());color=7 if 'Berr' in id else 4 if 'Roast' in id else 6 if j%3==0 else 14;ell('Meal ingredient',(r*math.cos(a),r*math.sin(a),.092),(.024,.022,.018),color,'Root',8,4)
  else:raise ValueError('Unclassified live item: '+id)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='Prop_LOD0';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 for p in o.data.polygons:
  expected=o.data.attributes['atlas_tile'].data[p.index].value
  for i in p.loop_indices:
   uv=o.data.uv_layers.active.data[i].uv
   if int(uv.x*4)+4*int(uv.y*4)!=expected:raise ValueError(id+' atlas tile escaped')
 for v in o.data.vertices:
  if not v.groups or abs(sum(g.weight for g in v.groups)-1)>.01:raise ValueError(id+' invalid weights')
 o.parent=rig;m=o.modifiers.new('Skin','ARMATURE');m.object=rig;lods=[o]
 for level,ratio in [(1,.55),(2,.25)]:
  d=o.copy();d.data=o.data.copy();bpy.context.collection.objects.link(d);d.name='Prop_LOD'+str(level)
  for m in list(d.modifiers):d.modifiers.remove(m)
  bpy.context.view_layer.objects.active=d;m=d.modifiers.new('LOD','DECIMATE');m.ratio=ratio;bpy.ops.object.modifier_apply(modifier=m.name);m=d.modifiers.new('Skin','ARMATURE');m.object=rig;lods.append(d)
 clips={'Idle':(2,True)}
 if kind=='plant':clips['Sway']=(3,True);clips['HarvestReact']=(.5,False)
 if kind=='tool':clips.update({'Swing':(.8,False),'Recover':(.6,False)})
 if family in ('saw','mill','forge'):clips['Work']=(2,True)
 if family=='collector':clips.update({'Empty':(1,True),'Fill':(2,False),'Full':(1,True)})
 for name,(duration,loop) in clips.items():
  action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action;last=round(duration*24)
  for f in range(last+1):
   scene.frame_set(f+1);q=f/last;wave=math.sin(math.tau*q);pulse=math.sin(math.pi*q)
   for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
   if name=='Sway':rig.pose.bones['Wind'].rotation_euler.y=.055*wave
   if name=='HarvestReact':rig.pose.bones['Wind'].rotation_euler.y=.14*math.sin(math.tau*q)*math.exp(-2*q)
   if name=='Swing':rig.pose.bones['Root'].rotation_euler.x=-1.0*pulse
   if name=='Recover':rig.pose.bones['Root'].rotation_euler.x=-.2*(1-q)
   if name=='Work':
    if family=='saw':rig.pose.bones['Tool'].location.x=.12*wave
    if family=='mill':rig.pose.bones['Wheel'].rotation_euler.z=math.tau*q
    if family=='forge':rig.pose.bones['Lid'].scale.z=.8+.2*wave
   if name in ('Empty','Fill','Full'):rig.pose.bones['Water'].location.z=.40*(q if name=='Fill' else 1 if name=='Full' else 0)
   for b in rig.pose.bones:
    b.keyframe_insert('rotation_euler',frame=f+1,group=b.name);b.keyframe_insert('location',frame=f+1,group=b.name);b.keyframe_insert('scale',frame=f+1,group=b.name)
 rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_start=1;scene.frame_end=49;scene.frame_set(1)
 out=os.path.join(OUT,id);os.makedirs(out,exist_ok=True);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in lods:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.fbx(filepath=os.path.join(out,id+'.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
 counts={}
 for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
 for o in lods[1:]:o.hide_render=True;o.hide_set(True)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,id+'.blend'),compress=True)
 data=dict(spec);data.update({'name':labels.get(id,id),'triangles':counts,'animations':{n:{'seconds':d,'loop':l} for n,(d,l) in clips.items()},'native_footprint':[3,3,3] if family=='collector' else [2,2,1] if kind=='station' else None,'status':'Original review assets; block/item hooks and live gameplay acceptance pending'})
 json.dump(data,open(os.path.join(out,'asset-manifest.json'),'w'),indent=2);catalogue.append(data);open(os.path.join(OUT,'progress.txt'),'a').write(id+' PASS\n')
try:
 requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];prior={}
 unknown=set(requested)-{e['id'] for e in entries}-{'station','plant','item','tool'}
 if unknown:raise ValueError('Unknown asset/category selector: '+', '.join(sorted(unknown)))
 if requested and os.path.exists(os.path.join(OUT,'catalogue.json')):prior={x['id']:x for x in json.load(open(os.path.join(OUT,'catalogue.json')))['assets']}
 open(os.path.join(OUT,'progress.txt'),'w').write('BUILD START '+str(len(entries))+' assets\n')
 for e in entries:
  if not requested or e['id'] in requested or e['kind'] in requested:
   manifest=os.path.join(OUT,e['id'],'asset-manifest.json')
   existing=json.load(open(manifest)) if os.path.exists(manifest) else {}
   if existing.get('art_revision','').startswith('BotanicalRebuild'):
    catalogue.append(existing);print('Preserving rebuilt botanical asset',e['id'],'— use rebuild_botanical_models.py to regenerate',flush=True)
   else:build(e)
 if requested:
  prior.update({x['id']:x for x in catalogue});catalogue=[prior[e['id']] for e in entries if e['id'] in prior]
 json.dump({'assets':catalogue,'aliases':aliases,'scope':'Live Forest station/plant/item art plus explicitly marked harvested/seed review props. Native crop/resource reuse and planned Arbor/knowledge mechanics unchanged.','axes':'Blender Z-up / Unity Y-up; ground-centred stations/plants, hand pivot gathering tools; integration must account for native ModelOffset.'},open(os.path.join(OUT,'catalogue.json'),'w'),indent=2)
 open(os.path.join(OUT,'PROVENANCE.txt'),'w').write('Original procedural geometry, 1K atlas, rigs and visual motions. No copied native meshes, textures or animation. Original project helper definitions from build_thornback.py; isolated UV selection and face tile checks. Existing XML supplies stable IDs and footprint contracts only.\n')
 open(os.path.join(OUT,'progress.txt'),'a').write('PASS '+str(len(catalogue))+' assets\n')
except Exception:
 open(os.path.join(OUT,'build-error.txt'),'w').write(traceback.format_exc());raise

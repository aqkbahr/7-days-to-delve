"""Original Forest armor. Blender 5.2; measured native bone transforms, original meshes/motion."""
import bpy, math, json, os, re, ast, sys, traceback
import numpy as np
from mathutils import Vector, Matrix, Quaternion
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
OUT=os.path.join(ROOT,'src/Art/ForestArmor');os.makedirs(OUT,exist_ok=True)
tree=ast.parse(open(os.path.join(ROOT,'tools/art/build_thornback.py')).read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','ell','tube')],type_ignores=[]),'original_helpers','exec'))
original_finish=finish
def finish(o,tile=0,bone=None):
 # Never let Blender's multi-object Edit Mode unwrap a previously joined slot.
 bpy.ops.object.select_all(action='DESELECT')
 o=original_finish(o,tile,bone)
 tag=o.data.attributes.new('atlas_tile','INT','FACE')
 for face in tag.data:face.value=tile
 return o
sets=[('Light','Wayfarer Cloth',0,0),('Medium','Border Leather',1,0),('Heavy','Scavenged Iron',2,0),('Padded','Padded Cloth',0,0),('ForgedLight','Forged Light',0,1),('ForgedMedium','Forged Medium',1,1),('ForgedHeavy','Forged Heavy',2,1)]
slots=['Helmet','Outfit','Gloves','Boots']
nodes={}
for line in open(os.path.join(ROOT,'artifacts/forest-armor/InspectProfile/Male-rig.txt')):
 m=re.match(r'NODE (\S+) parent=(\S+) pos=\(([^)]+)\) rot=\(([^)]+)\)',line)
 if m:
  name,parent,pos,rot=m.groups();nodes[name]={'parent':parent,'pos':[float(v) for v in pos.split(',')],'rot':[float(v) for v in rot.split(',')]}
names=[]
for n in nodes:
 p=n
 while p in nodes and p!='Origin':p=nodes[p]['parent']
 if p=='Origin' and not any(s in n for s in ('_sup_','CameraNode','Footsteps','Pouch')):names.append(n)
# Unity's FBX importer reflects X. Compensate here, not with a negative prefab scale.
world={};C=Matrix(((-1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
for n in names:
 d=nodes[n];x,y,z,w=d['rot'];local=Matrix.Translation(Vector(d['pos']))@Quaternion((w,x,y,z)).to_matrix().to_4x4();world[n]=(world[d['parent']]@local) if d['parent'] in world else local
B={n:C@w for n,w in world.items()};P={n:b.translation for n,b in B.items()}
json.dump({n:nodes[n] for n in names},open(os.path.join(OUT,'rig-contract.json'),'w'),indent=2)
N=2048;cell=512;px=np.ones((N,N,4),np.float32);yy,xx=np.mgrid[0:cell,0:cell];u=xx/cell;v=yy/cell;rng=np.random.default_rng(71)
colors=[(.23,.29,.17),(.30,.16,.075),(.27,.30,.32),(.10,.11,.115),(.56,.45,.28),(.30,.23,.16),(.17,.24,.29),(.39,.29,.12),(.22,.28,.28),(.45,.44,.32),(.42,.46,.48),(.19,.10,.055),(.12,.15,.12),(.42,.33,.21),(.57,.50,.34),(.26,.31,.34)]
for i,c in enumerate(colors):
 noise=rng.normal(0,.009,(cell,cell));grain=.009*np.sin(u*410)*np.sin(v*410) if i in (0,4,5,6,8,9,12) else .013*np.sin(u*90+np.sin(v*21))
 row,col=divmod(i,4);px[row*cell:(row+1)*cell,col*cell:(col+1)*cell,:3]=np.clip(np.array(c)+(noise+grain)[:,:,None],.008,.95)
image=bpy.data.images.new('ForestArmorAtlas',width=N,height=N);image.pixels.foreach_set(px.ravel());image.filepath_raw=os.path.join(OUT,'ForestArmorAtlas.png');image.file_format='PNG';image.save();image.pack()
catalogue=[]
clips={'Idle':(2,True),'Walk':(1,True),'Run':(.7,True),'Crouch':(1.4,False),'Attack':(.8,False),'Cast':(1.2,False),'Grip':(1,False)}

def build(key,label,weight,tier):
 global mat,parts
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 scene=bpy.context.scene;scene.render.fps=30;scene.unit_settings.system='METRIC'
 mat=bpy.data.materials.new(key+'_Surface');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='ForestArmorRig';rig.data.edit_bones.remove(rig.data.edit_bones[0])
 for n in names:
  b=rig.data.edit_bones.new(n);b.head=P[n];b.tail=b.head+B[n].to_3x3()@Vector((0,.035,0));b.align_roll(B[n].to_3x3()@Vector((0,0,1)))
  if nodes[n]['parent'] in names:b.parent=rig.data.edit_bones[nodes[n]['parent']]
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
 cloth=6 if tier else 5 if key=='Padded' else 0;leather=11 if tier else 1;metal=10 if tier else 2;trim=7 if tier else 4;base=cloth if weight==0 else leather if weight==1 else 3
 pieces={}
 def rod(name,a,b,r,tile,bone):return tube(name,[a,b],[r,r],tile,bone,8)
 def mesh(name,verts,faces,tile,bone=None):
  d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return finish(o,tile,bone)
 def box(name,p,scale,tile,bone):
  bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);m=o.modifiers.new('Rounded edges','BEVEL');m.width=min(scale)*.18;m.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);return finish(o,tile,bone)
 def weights(o,fn):
  for v in o.data.vertices:
   vals=fn(o.matrix_world@v.co);total=sum(vals.values())
   for n,w in vals.items():
    if w>1e-6:(o.vertex_groups.get(n) or o.vertex_groups.new(name=n)).add([v.index],w/total,'REPLACE')
 def torso_weights(p):
  chain=['Hips','Spine1','Spine2','Spine3','Neck'];z=p.z
  for a,b in zip(chain,chain[1:]):
   if z<=P[b].z:
    t=max(0,min(1,(z-P[a].z)/(P[b].z-P[a].z)));return {a:1-t,b:t}
  return {'Neck':1}
 def loft(name,rings,tile,bone=None,arc=math.tau,sides=32):
  # Elliptical rings, open at neck/hem. Thickness is explicit, not a two-sided shader.
  vs=[];fs=[];closed=abs(arc-math.tau)<.001;count=sides if closed else sides+1
  for z,rx,ry,cy in rings:
   for j in range(count):
    a=-arc/2+arc*j/sides;vs.append((rx*math.sin(a),cy+ry*math.cos(a),z))
  for i in range(len(rings)-1):
   for j in range(sides):k=(j+1)%count;fs.append((i*count+j,i*count+k,(i+1)*count+k,(i+1)*count+j))
  o=mesh(name,vs,[tuple(reversed(f)) for f in fs],tile,bone);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Fabric thickness','SOLIDIFY');m.thickness=.005;bpy.ops.object.modifier_apply(modifier=m.name)
  if bone is None:weights(o,torso_weights)
  return o
 def sleeve(name,chain,radii,tile):
  pts=[];rr=[];segments=[]
  for i,(a,b) in enumerate(zip(chain,chain[1:])):
   for j in range(5):
    t=j/5;pts.append(P[a].lerp(P[b],t));rr.append(radii[i]*(1-t)+radii[i+1]*t);segments.append((i,t))
  pts.append(P[chain[-1]]);rr.append(radii[-1]);segments.append((len(chain)-2,1))
  o=tube(name,pts,rr,tile,None,16)
  # Rings blend at joints over 25% of segment length; stay local to the anatomical chain.
  for ri,(i,t) in enumerate(segments):
   a=chain[i];b=chain[i+1];values={a:1}
   if t>.70 and i<len(chain)-2:values={a:(1-t)/.30,b:(t-.70)/.30}
   if t<.20 and i>0:values={chain[i-1]:(.20-t)/.40,a:1-(.20-t)/.40}
   for n,w in values.items():
    if w>0:(o.vertex_groups.get(n) or o.vertex_groups.new(name=n)).add(list(range(ri*16,(ri+1)*16)),w,'REPLACE')
  return o
 def band(name,p,r,tile,bone,normal=Vector((0,0,1)),minor=.006):
  bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=minor,major_segments=24,minor_segments=6,location=p);o=bpy.context.object;o.name=name;o.rotation_euler=Vector(normal).to_track_quat('Z','Y').to_euler();return finish(o,tile,bone)
 def panel(name,verts,tile,bone):
  # Convex armor panel with a raised centre ridge and solid back.
  center=sum((Vector(p) for p in verts),Vector())/len(verts);center.y-=.018
  o=mesh(name,verts+[center],[(i,(i+1)%len(verts),len(verts)) for i in range(len(verts))],tile,bone);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Plate thickness','SOLIDIFY');m.thickness=.009;bpy.ops.object.modifier_apply(modifier=m.name)
  for p in o.data.polygons:p.use_smooth=False
  return o
 for slot in slots:
  parts=[];id='armorDelve'+key+slot
  if slot=='Helmet':
   cy=.025
   if weight==0:
    loft('Open faced hood',[(1.49,.095,.095,cy),(1.59,.125,.14,cy),(1.70,.139,.145,cy),(1.79,.12,.13,cy),(1.85,.065,.08,cy),(1.865,.008,.01,cy)],base,'Head',arc=4.65)
    # Opening edge is separately reinforced, leaving the face unobstructed.
    for side in (-1,1):
     points=[(side*.069,-.04,1.49),(side*.095,-.075,1.59),(side*.101,-.075,1.70),(side*.087,-.064,1.79),(side*.047,-.029,1.85),(0,.02,1.865)]
     tube('Hood opening binding',points,[.009]*len(points),trim,'Head',8)
    if key=='Padded':
     for j in range(7):
      a=-1.9+j*3.8/6;tube('Quilted hood seam',[(.13*math.sin(a),cy+.145*math.cos(a),1.60),(.126*math.sin(a),cy+.137*math.cos(a),1.75),(.055*math.sin(a),cy+.074*math.cos(a),1.845)],[.0025]*3,9,'Head',6)
    if tier:
     panel('Hood brow ornament',[(-.025,-.10,1.80),(0,-.11,1.83),(.025,-.10,1.80),(0,-.12,1.77)],trim,'Head')
   else:
    loft('Crowned helmet',[(1.735,.128,.15,cy),(1.78,.128,.15,cy),(1.84,.09,.11,cy),(1.88,.012,.018,cy)],metal if weight==2 else leather,'Head')
    loft('Rear neck guard',[(1.55,.12,.11,.04),(1.65,.14,.145,.04),(1.745,.13,.15,cy)],metal if weight==2 else leather,'Head',arc=3.8)
    for side in (-1,1):
     panel('Cheek guard',[(side*.115,-.09,1.745),(side*.115,-.13,1.67),(side*.075,-.11,1.59),(side*.125,-.035,1.60)],metal if weight==2 else leather,'Head')
    band('Brow rim',(0,cy,1.745),.13,trim if tier else 3,'Head')
    if weight==2:
     box('Nasal guard',(0,-.129,1.708),(.024,.019,.12),metal,'Head')
     for a in np.linspace(-2.8,2.8,9):ell('Helmet rivet',(.128*math.sin(a),cy+.151*math.cos(a),1.756),(.005,.005,.005),trim,'Head',8,4)
    if tier:box('Crown ridge',(0,.025,1.864),(.025,.14,.025),trim,'Head')
  elif slot=='Outfit':
   loft('Fitted tunic',[(.86,.165,.115,.028),(.97,.17,.12,.028),(1.08,.16,.12,.028),(1.19,.19,.14,.028),(1.34,.215,.145,.028),(1.44,.195,.125,.028),(1.51,.075,.075,.028)],base)
   for side in ('Left','Right'):
    sleeve('Sleeve',[side+'Arm',side+'ForeArm',side+'Hand'],[.082,.063,.038],cloth if weight==0 else 5)
    sleeve('Trousers',[side+'UpLeg',side+'Leg',side+'Foot'],[.10,.075,.05],12 if weight==0 else 5)
    if weight>0:
     p=P[side+'Arm'];ell('Layered shoulder',p+Vector((0,0,.015)),(.112,.118,.075),metal if weight==2 else leather,side+'Arm',16,8)
     if tier:ell('Shoulder reinforcement',p+Vector((0,-.012,.05)),(.10,.107,.045),metal if weight==2 else 7,side+'Arm',16,8)
    p=P[side+'UpLeg'].lerp(P[side+'Leg'],.75);ell('Knee reinforcement',p+Vector((0,-.073,-.08)),(.075,.028,.075),metal if weight==2 else leather,side+'Leg',12,8)
   loft('Waist belt',[(1.025,.174,.132,.028),(1.075,.173,.132,.028)],leather,'Hips')
   box('Belt buckle',(0,-.115,1.05),(.06,.025,.05),trim,'Hips');box('Belt centre',(0,-.131,1.05),(.035,.009,.028),3,'Hips')
   for side in (-1,1):
    box('Utility pouch',(side*.17,-.07,1.015),(.07,.065,.12),leather,'Hips');box('Pouch flap',(side*.17,-.109,1.04),(.076,.012,.055),trim if tier else leather,'Hips')
   if weight==0:
    # Split tabard follows each thigh rather than stretching across the legs.
    for side,n in [(-1,'Right'),(1,'Left')]:
     panel('Split tunic skirt',[(side*.015,-.103,.99),(side*.16,-.08,.99),(side*.175,-.11,.73),(side*.035,-.13,.70)],cloth,n+'UpLeg')
    for z in np.linspace(1.12,1.43,7):rod('Front lacing',(-.022,-.122,z),(.022,-.122,z+.025),.003,trim,'Spine2' if z<1.32 else 'Spine3')
    if key=='Padded':
     for x in np.linspace(-.14,.14,9):rod('Gambeson quilting',(x,-.126,1.11),(x,-.12,1.42),.002,9,'Spine3')
    if tier:
     loft('Reinforced collar',[(1.45,.105,.09,.025),(1.52,.076,.078,.025)],leather,'Neck')
     for side in (-1,1):panel('Tail trim',[(side*.04,-.135,.74),(side*.16,-.12,.77),(side*.17,-.12,.73),(side*.04,-.135,.70)],trim,('Right' if side<0 else 'Left')+'UpLeg')
   elif weight==1:
    for sign in (-1,1):panel('Leather cuirass',[(sign*.015,-.126,1.12),(sign*.17,-.105,1.14),(sign*.20,-.11,1.39),(sign*.075,-.10,1.46),(sign*.015,-.13,1.40)],leather,'Spine3')
    for z in (1.18,1.28,1.38):
     rod('Chest cross strap',(-.16,-.135,z),(.16,-.135,z+.045),.012,trim if tier else 5,'Spine3')
     for x in (-.13,.13):ell('Leather stud',(x,-.15,z+.025),(.006,.004,.006),metal,'Spine3',8,4)
    if tier:
     for j in range(3):panel('Brigandine waist plate',[(-.15,-.12,1.13+j*.07),(.15,-.12,1.13+j*.07),(.14,-.14,1.08+j*.07),(-.14,-.14,1.08+j*.07)],metal,'Spine2')
   else:
    panel('Raised breastplate',[(-.18,-.13,1.40),(-.07,-.13,1.47),(.07,-.13,1.47),(.18,-.13,1.40),(.18,-.14,1.21),(0,-.17,1.17),(-.18,-.14,1.21)],metal,'Spine3')
    panel('Backplate',[(-.17,.17,1.39),(.17,.17,1.39),(.15,.16,1.15),(-.15,.16,1.15)],metal,'Spine3')
    for j in range(3):loft('Articulated waist lame',[(1.06+j*.05,.182,.15,.025),(1.105+j*.05,.182,.15,.025)],metal,'Spine1' if j<2 else 'Spine2')
    for side,n in [(-1,'Right'),(1,'Left')]:
     for j in range(3):panel('Thigh tasset',[(side*.025,-.14,.99-j*.07),(side*.17,-.115,.99-j*.07),(side*.17,-.12,.93-j*.07),(side*.035,-.15,.91-j*.07)],metal,n+'UpLeg')
    for x in (-.145,.145):
     for z in (1.26,1.36,1.40):ell('Chest rivet',(x,-.153,z),(.005,.004,.005),trim,'Spine3',8,4)
    if tier:panel('Breastplate crest',[(-.035,-.17,1.37),(0,-.18,1.41),(.035,-.17,1.37),(0,-.19,1.30)],trim,'Spine3')
  elif slot=='Gloves':
   for side,sign in [('Left',-1),('Right',1)]:
    hand=P[side+'Hand'];fore=P[side+'ForeArm'];a=fore.lerp(hand,.65)
    o=tube('Wrist cuff',[a,hand],[.048,.043],leather,side+'ForeArm',16)
    ends=[P[side+'Hand'+f+'1'] for f in ('Index','Middle','Ring','Pinky')];center=sum(ends,Vector())/4
    palm=ell('Glove palm',hand.lerp(center,.55),(.065,.035,.055),leather,side+'Hand',16,8)
    # Orient the palm along the actual hand axis, keeping finger bone chains separate.
    palm.rotation_euler=(center-hand).to_track_quat('X','Z').to_euler()
    for finger in ('Index','Middle','Ring','Pinky','Thumb'):
     chain=[side+'Hand'+finger+str(i) for i in range(1,5) if side+'Hand'+finger+str(i) in P]
     if len(chain)<2:continue
     sleeve('Articulated '+finger,chain,[.011 if finger!='Thumb' else .014]*len(chain),leather)
     if weight>0:ell('Knuckle reinforcement',P[chain[0]]+Vector((0,-.008,.009)),(.014,.016,.012),metal if weight==2 else trim,chain[0],8,4)
    band('Cuff binding',a,.049,trim,side+'ForeArm',hand-fore)
    if weight==2:
     mid=hand.lerp(center,.5);ell('Gauntlet back',mid+Vector((0,-.02,.013)),(.055,.022,.045),metal,side+'Hand',12,6)
    if tier:band('Forged wrist clasp',a.lerp(hand,.35),.047,metal,side+'ForeArm',hand-fore,minor=.007)
  else:
   for side in ('Left','Right'):
    foot=P[side+'Foot'];knee=P[side+'Leg'];top=foot.lerp(knee,.65 if weight>0 else .52)
    tube('Boot shaft',[foot,foot.lerp(top,.45),top],[.061,.07,.079],leather,side+'Leg',16)
    toe=P[side+'ToeBase'];center=foot.lerp(toe,.55);center.z=.075
    ell('Boot foot',center,(.069,.16,.065),leather,side+'Foot',20,10)
    sole=ell('Layered sole',center+Vector((0,0,-.038)),(.072,.163,.026),3,side+'Foot',20,8)
    for j in range(3):band('Boot straps',foot.lerp(top,.25+j*.27),.075,trim if tier else 5,side+'Leg')
    if weight>0:
     p=foot.lerp(top,.6);panel('Shin guard',[(p.x-.055,p.y-.074,p.z+.09),(p.x+.055,p.y-.074,p.z+.09),(p.x+.04,p.y-.077,p.z-.09),(p.x-.04,p.y-.077,p.z-.09)],metal if weight==2 else leather,side+'Leg')
    if weight==2:ell('Armored toe',center+Vector((0,-.055,.025)),(.073,.09,.038),metal,side+'Foot',16,8)
  bpy.ops.object.select_all(action='DESELECT')
  for o in parts:o.select_set(True)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=slot+'_LOD0';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  for poly in o.data.polygons:
   expected=o.data.attributes['atlas_tile'].data[poly.index].value
   for i in poly.loop_indices:
    uv=o.data.uv_layers.active.data[i].uv
    if int(uv.x*4)+4*int(uv.y*4)!=expected:raise ValueError(id+' UV escaped its assigned material tile')
  m=o.modifiers.new('Skin','ARMATURE');m.object=rig;o.parent=rig;lods=[o]
  for level,ratio in [(1,.55),(2,.25)]:
   d=o.copy();d.data=o.data.copy();bpy.context.collection.objects.link(d);d.name=slot+'_LOD'+str(level)
   for m in list(d.modifiers):d.modifiers.remove(m)
   bpy.context.view_layer.objects.active=d;m=d.modifiers.new('LOD reduction','DECIMATE');m.ratio=ratio;bpy.ops.object.modifier_apply(modifier=m.name);m=d.modifiers.new('Skin','ARMATURE');m.object=rig;lods.append(d)
  for obj in lods:
   for v in obj.data.vertices:
    if not v.groups:raise ValueError(id+' unweighted vertex')
    if abs(sum(g.weight for g in v.groups)-1)>.01:raise ValueError(id+' non-normalized weights')
  pieces[slot]=lods
 # Original fitting motions; rotation conversion is explicit world-axis to native bone-local space.
 def rotate(n,degrees):
  q=Quaternion(Vector((1,0,0)),math.radians(degrees[0]))@Quaternion(Vector((0,1,0)),math.radians(degrees[1]))@Quaternion(Vector((0,0,1)),math.radians(degrees[2]));basis=rig.data.bones[n].matrix_local.to_quaternion();rig.pose.bones[n].rotation_quaternion=basis.inverted()@q@basis
 for name,(duration,loop) in clips.items():
  action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action;last=round(duration*30)
  for f in range(last+1):
   scene.frame_set(f+1);q=f/last;wave=math.sin(math.tau*q);pulse=math.sin(math.pi*q)
   for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0)
   rotate('Head',(0,0,2*wave));rotate('Spine3',(1.2*wave,0,0))
   for side,sign in [('Left',1),('Right',-1)]:
    if name in ('Walk','Run'):
     amp=26 if name=='Walk' else 43;rotate(side+'UpLeg',(sign*amp*wave,0,0));rotate(side+'Leg',(-max(0,sign*wave)*amp*1.2,0,0));rotate(side+'Arm',(-sign*amp*.5*wave,0,0));rotate(side+'Foot',(sign*8*wave,0,0))
    elif name=='Crouch':rotate(side+'UpLeg',(55*pulse,0,0));rotate(side+'Leg',(-100*pulse,0,0));rotate(side+'Foot',(45*pulse,0,0))
    elif name in ('Attack','Cast'):rotate(side+'Arm',(40*pulse,sign*15*pulse,sign*12*pulse));rotate(side+'ForeArm',(20*pulse,0,0))
    elif name=='Grip':
     for finger in ('Index','Middle','Ring','Pinky','Thumb'):
      for j in (1,2,3):
       n=side+'Hand'+finger+str(j)
       if n in names:rig.pose.bones[n].rotation_quaternion=Quaternion(Vector((0,0,1)),math.radians(sign*55*pulse))
    if name=='Idle':rotate(side+'Hand',(1*wave,0,0))
   if name=='Crouch':rig.pose.bones['Hips'].location.y=-.28*pulse;rotate('Spine2',(18*pulse,0,0))
   if name=='Attack':rotate('Spine2',(0,0,18*pulse))
   for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=f+1,group=b.name);b.keyframe_insert('location',frame=f+1,group=b.name)
 rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_start=1;scene.frame_end=61;scene.frame_set(1)
 for slot,lods in pieces.items():
  id='armorDelve'+key+slot;out=os.path.join(OUT,id);os.makedirs(out,exist_ok=True)
  bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
  for o in lods:o.select_set(True)
  bpy.context.view_layer.objects.active=rig
  bpy.ops.export_scene.fbx(filepath=os.path.join(out,id+'.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
  counts={}
  for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
  data={'id':id,'name':label+' '+slot,'set':key,'slot':slot,'family':'armor','tier':'Forged' if tier else 'Field','bones':len(names),'triangles':counts,'animations':{n:{'seconds':d,'loop':l} for n,(d,l) in clips.items()},'status':'Original reference-fit art; native SDCS/morph/first-person integration pending'}
  json.dump(data,open(os.path.join(out,'asset-manifest.json'),'w'),indent=2);catalogue.append(data)
 # One editable source per complete set keeps all four pieces registered together.
 for lods in pieces.values():
  for o in lods[1:]:o.hide_render=True;o.hide_set(True)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,key+'.blend'))
 open(os.path.join(OUT,'progress.txt'),'a').write(key+' PASS\n')
try:
 open(os.path.join(OUT,'progress.txt'),'w').write('BUILD START\n')
 for entry in sets:build(*entry)
 json.dump({'armor':catalogue,'sets':[{'key':s[0],'name':s[1]} for s in sets],'scope':'28 armor pieces / seven sets; shared native reference skeleton, original pose-check animations','integration':'Not activated. SDCS body exclusions, morphs, hair masks and first-person glove views require native fitting.'},open(os.path.join(OUT,'catalogue.json'),'w'),indent=2)
 open(os.path.join(OUT,'PROVENANCE.txt'),'w').write('Original project-authored geometry, procedural atlas and seven fitting motions. Native male/female Fiber prefabs inspected only for bone names/transforms and bounds. No native mesh, texture or animation copied. One editable blend per complete set; one FBX per item. Native gameplay stats unchanged.\n')
 open(os.path.join(OUT,'progress.txt'),'a').write('PASS 28 pieces\n')
except Exception:
 open(os.path.join(OUT,'build-error.txt'),'w').write(traceback.format_exc());raise

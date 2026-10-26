"""Original Forest enemy meshes, native-reference rigs and presentation clips.
Run in Blender background. Native geometry/animation is never copied.
"""
import bpy, math, random, json, os, re, sys, ast, traceback
import numpy as np
from mathutils import Vector, Matrix, Quaternion
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
IDS=['delveCorruptedWalker','delveImp','delvePossessedSoldier','delveDemonSpawn','delveWarpedBrute','delveAshboundWarden']
SIZES=[.95,.75,1,1,1.12,1.15]
tree=ast.parse(open(os.path.join(ROOT,'tools/art/build_thornback.py')).read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','ell','tube')],type_ignores=[]),'original_geometry_helpers','exec'))
old_finish=finish
def finish(o,tile=0,bone=None):
 bpy.ops.object.select_all(action='DESELECT');o=old_finish(o,tile,bone)
 attr=o.data.attributes.new('atlas_tile','INT','FACE')
 for d in attr.data:d.value=tile
 return o
C=Matrix(((-1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
def build(entity):
 global mat,parts
 index=IDS.index(entity);walker,imp,soldier,demon,brute,warden=[index==i for i in range(6)]
 random.seed(190+index);out=os.path.join(ROOT,'src/Art/ForestEnemies',entity);os.makedirs(out,exist_ok=True)
 def progress(s):open(os.path.join(out,'build-progress.txt'),'w').write(s)
 progress('rig and atlas')
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.fps=30
 nodes={}
 for line in open(os.path.join(ROOT,'artifacts/forest-enemies/InspectProfile',entity+'-rig.txt')):
  m=re.match(r'NODE (\S+) parent=(\S+) pos=\(([^)]+)\) rot=\(([^)]+)\) scale=\(([^)]+)\)',line)
  if m:
   n,p,xyz,q,s=m.groups();nodes[n]={'parent':p,'pos':list(map(float,xyz.split(','))),'rot':list(map(float,q.split(','))),'scale':list(map(float,s.split(',')))}
 names=[]
 for n in nodes:
  p=n
  while p in nodes and p!='Origin':p=nodes[p]['parent']
  if p=='Origin':names.append(n)
 native={};points={}
 for n in names:
  d=nodes[n];x,y,z,w=d['rot'];local=Matrix.LocRotScale(Vector(d['pos']),Quaternion((w,x,y,z)),Vector(d['scale']))
  native[n]=native[d['parent']]@local if d['parent'] in native else local;points[n]=(C@native[n]).translation
 bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name=entity+'_Rig';rig.data.edit_bones.remove(rig.data.edit_bones[0])
 for n in names:
  b=rig.data.edit_bones.new(n);basis=C@native[n];b.head=basis.translation;b.tail=b.head+basis.to_3x3()@Vector((0,.035,0));b.align_roll(basis.to_3x3()@Vector((0,0,1)))
  if nodes[n]['parent'] in names:b.parent=rig.data.edit_bones[nodes[n]['parent']]
 if imp:
  for i in range(4):
   n='Tail'+str(i+1);b=rig.data.edit_bones.new(n);b.head=points['Hips']+Vector((.05*i,.12+.17*i,-.08-.035*i));b.tail=b.head+Vector((.05,.17,-.035));b.parent=rig.data.edit_bones['Hips' if i==0 else 'Tail'+str(i)];points[n]=b.head.copy()
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
 base=[(.28,.32,.20),(.36,.21,.16),(.22,.25,.19),(.20,.15,.16),(.32,.29,.24),(.25,.22,.21)][index]
 colors=[base,(.23,.17,.105),(.66,.58,.40),(.065,.055,.045),(.78,.35,.10),(.23,.32,.12),(.38,.19,.12),(.12,.14,.16),(.32,.35,.34),(.41,.29,.13),(.50,.46,.35),(.11,.08,.075),(.02,.017,.014),(.36,.075,.04),(.16,.21,.24),(.45,.35,.20)]
 N=2048;cell=512;pixels=np.ones((N,N,4),np.float32);emission=np.zeros_like(pixels);emission[:,:,3]=1;rng=np.random.default_rng(190+index);yy,xx=np.mgrid[0:cell,0:cell];u=xx/cell;v=yy/cell
 for i,color in enumerate(colors):
  grain=rng.normal(0,.016,(cell,cell))+.02*np.sin(u*180+np.sin(v*29)*2)*np.sin(v*63)
  if i==1:grain+=.035*np.sin(u*140+np.sin(v*10)*3)
  if i in (7,8,14):grain+=.012*np.sin(v*330)
  row,col=divmod(i,4);pixels[row*cell:(row+1)*cell,col*cell:(col+1)*cell,:3]=np.clip(np.array(color)+grain[:,:,None],.003,.95)
  if i==4:emission[row*cell:(row+1)*cell,col*cell:(col+1)*cell,:3]=np.array(color)*.23
 for label,data in [('Albedo',pixels),('Emission',emission)]:
  image=bpy.data.images.new(entity+'_'+label,width=N,height=N);image.pixels.foreach_set(data.ravel());image.filepath_raw=os.path.join(out,label+'.png');image.file_format='PNG';image.save();image.pack()
 mat=bpy.data.materials.new(entity+'_Surface');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.78
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images[entity+'_Albedo'];mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);parts=[]
 def slab(name,p,outline,depth,tile,bone,angle=0):
  rotation=Matrix.Rotation(angle,3,'Z');verts=[]
  for y in [-depth/2,depth/2]:
   for x,z in outline:verts.append(p+rotation@Vector((x,y,z)))
  count=len(outline);faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
  for i in range(count):j=(i+1)%count;faces.append((i,j,j+count,i+count))
  data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);finish(o,tile,bone)
  for face in o.data.polygons:face.use_smooth=False
  return o
 masses=[]
 def mass(p,scale):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=p);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);masses.append(o)
 def capsule(a,b,r1,r2):
  for i in range(max(3,int((b-a).length/.055))+1):
   steps=max(3,int((b-a).length/.055));t=i/steps;r=r1*(1-t)+r2*t;mass(a.lerp(b,t),(r,r,r))
 hip=points['Hips'];head=points['Head'];chest=points['Spine3'];neck=points['Neck'];broad=1.5 if brute else .88 if imp or demon else 1
 mass(hip+Vector((0,0,.015)),(.18*broad,.125*broad,.17));mass(hip.lerp(chest,.47),(.15*broad,.12*broad,.23));mass(chest+Vector((0,0,.07)),(.235*broad,.145*broad,.225))
 capsule(chest+Vector((0,0,.13)),head,.095,.072)
 mass(head+Vector((0,-.025,.075)),(.108 if not imp else .115,.105,.15));mass(head+Vector((0,-.065,.005)),(.088,.08,.065))
 segments=[]
 torso=['Hips','Spine','Spine1','Spine2','Spine3','Neck','Head']
 for i,n in enumerate(torso):segments.append((n,points[n],points[torso[i+1]] if i+1<len(torso) else head+Vector((0,0,.18))))
 for side in ['Left','Right']:
  chain=[side+n for n in ['UpLeg','Leg','Foot','ToeBase']]
  for i in range(2):
   a,b=points[chain[i]],points[chain[i+1]];capsule(a,b,(.105 if i==0 else .072)*broad,(.075 if i==0 else .047)*broad);segments.append((chain[i],a,b))
  foot=points[side+'Foot'];mass(foot+Vector((0,-.055,-.055)),(.075*broad,.135,.075));segments.append((side+'Foot',foot,points[side+'ToeBase']))
  arm=[side+n for n in ['Arm','ForeArm','Hand']];capsule(chest+Vector((0,0,.1)),points[arm[0]],.12*broad,.095*broad)
  for i in range(2):
   r=(.085 if i==0 else .065)*broad*(1.6 if brute and side=='Right' and i==1 else 1)
   capsule(points[arm[i]],points[arm[i+1]],r,r*.72);segments.append((arm[i],points[arm[i]],points[arm[i+1]]))
  a=points[side+'Hand'];b=points[side+'HandMiddle1'];capsule(a,b,.06*(1.35 if imp else 1),.045);segments.append((side+'Hand',a,b))
 progress('fusing and weighting anatomy')
 bpy.ops.object.select_all(action='DESELECT')
 for o in masses:o.select_set(True)
 bpy.context.view_layer.objects.active=masses[0];bpy.ops.object.join();body=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 mod=body.modifiers.new('Continuous anatomy','REMESH');mod.mode='VOXEL';mod.voxel_size=.017;bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=body.modifiers.new('Sculpt smoothing','SMOOTH');mod.factor=1;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=body.modifiers.new('Retopology','DECIMATE');mod.ratio=min(1,9500/max(1,len(body.data.polygons)*2));bpy.ops.object.modifier_apply(modifier=mod.name);finish(body,0)
 groups={n:body.vertex_groups.new(name=n) for n in names}
 for vertex in body.data.vertices:
  p=vertex.co;side='Left' if p.x>0 else 'Right'
  allowed=torso if p.z>neck.z-.035 else [side+'UpLeg',side+'Leg',side+'Foot','Hips'] if p.z<hip.z-.10 else [side+'Arm',side+'ForeArm',side+'Hand','Spine3'] if abs(p.x)>(.25*broad if p.z>hip.z+.1 else .27) else torso
  scored=[]
  for n,a,b in segments:
   if n not in allowed:continue
   ab=b-a;t=max(0,min(1,(p-a).dot(ab)/max(ab.length_squared,1e-8)));dist=(p-a-t*ab).length;scored.append((n,1/(dist+.035)**6))
  best=sorted(scored,key=lambda v:v[1],reverse=True)[:4];total=sum(w for n,w in best)
  for n,w in best:groups[n].add([vertex.index],w/total,'REPLACE')
 progress('hands and silhouette details')
 for side in ['Left','Right']:
  sign=1 if side=='Left' else -1
  for digit in ['Thumb','Index','Middle','Ring','Pinky']:
   chain=[side+'Hand'+digit+str(i) for i in range(1,5)]
   for i,n in enumerate(chain[:-1]):tube('Articulated '+digit,[points[n],points[chain[i+1]]],[.018 if imp else .014,.013 if imp else .011],1 if walker else 0,n,7)
   n=chain[-2];p=points[chain[-1]];direction=(p-points[n]).normalized();tube('Tapered claw',[p,p+direction*(.045 if imp or demon else .022)+Vector((0,-.012,-.01))],[.012,.001],2,n,6)
  # Brow, recessed eyes, cheek and ears give the face a readable direction.
  ell('Deep eye socket',head+Vector((sign*.049,-.116,.087)),(.042,.014,.029),12,'Head',12,8)
  ell('Dull eye',head+Vector((sign*.049,-.129,.088)),(.023,.008,.010),4,'Head',12,8)
  tube('Brow',[head+Vector((sign*.014,-.12,.115)),head+Vector((sign*.09,-.095,.13))],[.022,.018],0 if not warden else 7,'Head',8)
  ell('Cheek plane',head+Vector((sign*.076,-.078,.027)),(.035,.05,.055),0,'Head',12,8)
  if imp:
   p=head+Vector((sign*.09,0,.08));tube('Swept ear',[p,p+Vector((sign*.14,.045,.08)),p+Vector((sign*.22,.12,.13))],[.055,.04,.001],6,'Head',8)
  else:ell('Ear',head+Vector((sign*.106,.005,.055)),(.022,.025,.044),0,'Head',12,8)
 ell('Nose',head+Vector((0,-.128,.043)),(.025,.035,.044),0,'Head',12,8)
 tube('Mouth crease',[head+Vector((-.065,-.113,-.013)),head+Vector((0,-.137,-.022)),head+Vector((.065,-.113,-.013))],[.008,.012,.008],12,'Jaw',8)
 for j in range(6):
  p=head+Vector(((j-2.5)*.018,-.137,-.018));tube('Broken teeth',[p,p+Vector((0,-.003,-.014-(j%2)*.009))],[.007,.002],2,'Jaw',5)
 # Layered ragged waist covering, deliberately opaque with geometric torn edges.
 for j in range(12):
  a=j*2*math.pi/12;p=hip+Vector((math.cos(a)*.18*broad,math.sin(a)*.135*broad,-.01))
  slab('Torn waist panel',p,[(-.055,.015),(.055,.015),(.065,-.18),(.024,-.23-random.random()*.08),(.005,-.20),(-.035,-.28),(-.062,-.17)],.012,3 if not walker else 1,'Hips',a+math.pi/2)
 if walker:
  slab('Root scar across face',head+Vector((.065,-.134,.09)),[(-.025,.08),(.025,.075),(.03,-.085),(.005,-.11),(-.02,-.045)],.018,1,'Head')
  for j in range(7):
   p=points['LeftArm']+Vector((random.uniform(-.04,.07),random.uniform(-.03,.07),random.uniform(-.04,.10)))
   tube('Split bark shoulder',[p,p+Vector((.04,.04,.16)),p+Vector((.03,.10,.25+random.random()*.1))],[.065,.041,.002],1,'LeftArm',7)
  for j in range(9):
   p=chest+Vector((random.uniform(-.17,.15),-.145,random.uniform(-.12,.20)));ell('Moss patch',p,(.04,.012,.055),5,'Spine3',10,6)
  for side in ['Left','Right']:
   a=points[side+'ForeArm'];b=points[side+'Hand'];tube('Binding root',[a+Vector((0,-.07,0)),a.lerp(b,.5)+Vector((.04,-.06,0)),b+Vector((0,-.05,-.03))],[.022,.018,.009],1,side+'ForeArm',7)
 if imp or demon:
  for sign in [-1,1]:
   p=head+Vector((sign*.075,.025,.17));tube('Broken swept horn' if imp else 'Forked cranial crest',[p,p+Vector((sign*.07,.035,.12)),p+Vector((sign*.10,.12,.17 if imp else .28))],[.047,.027,.008 if imp else .001],2 if imp else 7,'Head',8)
   if demon:
    p=head+Vector((sign*.12,.06,.30));tube('Crest fork',[p,p+Vector((sign*.07,-.035,.15))],[.025,.001],7,'Head',7)
  if imp:
   for i in range(4):
    n='Tail'+str(i+1);p=points[n];end=points.get('Tail'+str(i+2),p+Vector((.04,.16,.05)));tube('Balancing tail',[p,end],[.042-i*.008,.034-i*.008],0,n,9)
  if demon:
   for j in range(6):
    p=hip.lerp(neck,j/5)+Vector((0,.14,.02));tube('Dorsal ridge',[p,p+Vector((0,.14,.07)),p+Vector((0,.20,.13))],[.048,.027,.001],7,'Spine3' if j>2 else 'Spine1',7)
   for sign in [-1,1]:
    for j in range(4):
     p=chest+Vector((sign*.06,-.147,.11-j*.065));tube('Dull red rib seam',[p,p+Vector((sign*.13,.02,-.045))],[.009,.004],13,'Spine3',6)
 if brute:
  ell('Heavy squared jaw',head+Vector((0,-.055,-.018)),(.132,.095,.064),0,'Jaw',8,5)
  for j in range(11):
   p=chest+Vector((random.uniform(-.27,.27),.19,random.uniform(-.14,.19)));o=ell('Stony back growth',p,(random.uniform(.06,.10),.11,random.uniform(.08,.16)),8,'Spine3',8,5)
  p=points['RightForeArm'].lerp(points['RightHand'],.5);ell('Oversized armored forearm',p,(.14,.12,.17),8,'RightForeArm',10,7)
  for j in range(4):
   p=chest+Vector((-.15+j*.1,-.22,.12));tube('Scarred rib fold',[p,p+Vector((.025,-.01,-.16))],[.026,.012],6,'Spine3',7)
 if soldier or warden:
  # Faceted overlapping plates, attached to relevant bones instead of rigid whole-body shells.
  for sign,side in [(1,'Left'),(-1,'Right')]:
   p=chest+Vector((sign*.102,-.167,.055));slab('Fractured breastplate',p,[(-.105,.13),(.07,.15),(.12,.08),(.11,-.075),(.04,-.14),(-.09,-.10)],.045,7,'Spine3')
   for j in range(3):slab('Articulated abdominal lame',hip+Vector((sign*.082,-.15,.08+j*.065)),[(-.09,.035),(.09,.035),(.10,-.025),(.015,-.045),(-.095,-.025)],.025,8,'Spine1')
   p=points[side+'Arm'];ell('Asymmetric pauldron',p+Vector((0,0,.055)),(.17 if side=='Left' else .12,.17,.11),7,side+'Arm',8,6)
   a=points[side+'Leg'];b=points[side+'Foot'];slab('Shin plate',a.lerp(b,.55)+Vector((0,-.085,0)),[(-.068,.17),(.065,.17),(.07,.11),(.043,-.17),(-.045,-.17),(-.071,.10)],.035,7,side+'Leg')
   for j in range(3):
    p=points[side+'Arm']+Vector((sign*.055,-.12,.04-j*.045));ell('Oxidized armor rivet',p,(.012,.01,.012),9,side+'Arm',8,5)
  ell('Broken helm',head+Vector((0,.005,.115)),(.128,.113,.13),7,'Head',10,7)
  for sign in [-1,1]:
   tube('Visor rim',[head+Vector((sign*.015,-.124,.11)),head+Vector((sign*.095,-.106,.13)),head+Vector((sign*.115,-.06,.02))],[.024,.025,.02],8,'Head',7)
  if warden:
   slab('Champion angular face guard',head+Vector((0,-.156,.01)),[(-.095,.04),(-.035,.02),(0,.07),(.035,.02),(.095,.04),(.075,-.055),(0,-.09),(-.075,-.055)],.022,7,'Head')
   for j in range(7):
    a=j*math.pi/6;p=head+Vector((math.cos(a)*.10,math.sin(a)*.08,.20));tube('Broken crown',[p,p+Vector((math.cos(a)*.045,math.sin(a)*.045,.13+(j%3)*.04))],[.033,.003],7,'Head',6)
   for sign in [-1,1]:
    tube('Ash seam',[chest+Vector((sign*.04,-.184,.17)),chest+Vector((sign*.065,-.19,.02)),chest+Vector((sign*.13,-.16,-.08))],[.006,.008,.003],4,'Spine3',6)
    p=points['LeftArm']+Vector((sign*.06,.02,.13));tube('Champion shoulder crest',[p,p+Vector((sign*.07,.03,.14))],[.04,.002],8,'LeftArm',6)
 progress('LODs and UV validation')
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();mesh=bpy.context.object;mesh.name='Creature_LOD0';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 tags=mesh.data.attributes['atlas_tile'];uv=mesh.data.uv_layers.active.data
 for p in mesh.data.polygons:
  for li in p.loop_indices:
   if int(uv[li].uv.x*4)+4*int(uv[li].uv.y*4)!=tags.data[p.index].value:raise ValueError('Atlas tile drift')
 mesh.data.calc_loop_triangles()
 if len(mesh.data.loop_triangles)>25000:raise ValueError('LOD0 over 25k triangles')
 modifier=mesh.modifiers.new('Skin','ARMATURE');modifier.object=rig;mesh.parent=rig;lods=[mesh]
 for level,ratio in [(1,.5),(2,.2)]:
  o=mesh.copy();o.data=mesh.data.copy();bpy.context.collection.objects.link(o);o.name='Creature_LOD'+str(level)
  for m in list(o.modifiers):o.modifiers.remove(m)
  bpy.context.view_layer.objects.active=o;m=o.modifiers.new('LOD','DECIMATE');m.ratio=ratio;bpy.ops.object.modifier_apply(modifier=m.name);m=o.modifiers.new('Skin','ARMATURE');m.object=rig;lods.append(o)
 clips={'Idle':(3,True),'Walk':(1.4 if walker or brute else 1.05,True),'Run':(.75,True),'TurnLeft':(1,True),'TurnRight':(1,True),'Alert':(1.1,False),'HitFront':(.6,False),'HitLeft':(.6,False),'HitRight':(.6,False),'AttackWindup':(.7,False),'Attack':(.65,False),'AttackRunning':(.8,False),'Recovery':(1,False),'Death':(1.3,False),'Corpse':(1,True),'Sleep':(3,True),'Wake':(1.5,False)}
 if imp:clips.update({'LeapTakeoff':(.4,False),'LeapAir':(.6,True),'LeapLand':(.4,False),'Scamper':(.65,True)})
 if brute:clips.update({'Brace':(2,True),'Rush':(4,True),'Spent':(5,True)})
 if warden:clips.update({'Windup':(1.2,True),'Assault':(.8,True),'BossRecovery':(2,True),'Withdraw':(1.2,True)})
 def rot(n,x=0,y=0,z=0):
  if n not in rig.pose.bones:return
  from mathutils import Euler
  basis=rig.data.bones[n].matrix_local.to_quaternion();q=Euler(tuple(math.radians(v) for v in (x,y,z)),'XYZ').to_quaternion();rig.pose.bones[n].rotation_quaternion=basis.inverted()@q@basis
 def move(n,v):rig.pose.bones[n].location=rig.data.bones[n].matrix_local.to_quaternion().inverted()@Vector(v)
 progress('113 total presentation clips across roster; baking this rig')
 for name,(duration,loop) in clips.items():
  action=bpy.data.actions.new(name);action.use_fake_user=True;action['loop']=loop;rig.animation_data_create();rig.animation_data.action=action;last=round(duration*30)
  for f in range(last+1):
   scene.frame_set(f+1);q=f/last;wave=math.sin(q*2*math.pi);pulse=math.sin(q*math.pi)
   for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.scale=(1,1,1)
   # Relax the native A-pose; world Y rotations lower arms in the Blender X/Z plane.
   for side,sign in [('Left',1),('Right',-1)]:rot(side+'Arm',-8,sign*35,0);rot(side+'ForeArm',-12,0,0)
   lean=14 if walker else 22 if imp else 7 if brute or demon else 0
   rot('Spine2',lean+1.3*wave);rot('Neck',-lean*.45);rot('Head',1.8*wave,0,2*wave);move('Hips',(0,0,.004*wave))
   if imp:
    for i in range(4):rot('Tail'+str(i+1),0,4*math.sin(q*2*math.pi-i*.5),7*math.sin(q*2*math.pi-i*.5))
   if name in ('Walk','Run','AttackRunning','Scamper','Rush','Assault','Withdraw'):
    fast=name not in ('Walk','Withdraw');amp=28 if fast else 15;stride=math.sin(q*10*math.pi) if name=='Rush' else wave
    if walker:stride=math.sin(q*2*math.pi+.2*math.sin(q*2*math.pi))
    for side,sign in [('Left',1),('Right',-1)]:
     s=stride*sign;rot(side+'UpLeg',amp*s);rot(side+'Leg',-amp*.95*max(0,-s));rot(side+'Foot',amp*.25*s);rot(side+'Arm',-amp*.55*s-8,sign*35,0);rot(side+'ForeArm',-15-8*max(0,s))
    move('Hips',(0,0,.012*math.sin(q*4*math.pi)));rot('Spine2',lean+2*math.sin(q*4*math.pi),0,3*wave)
   if name in ('TurnLeft','TurnRight'):rot('Spine2',lean,0,(1 if name=='TurnLeft' else -1)*(10+3*wave));rot('Head',0,0,(1 if name=='TurnLeft' else -1)*22)
   if name=='Alert':rot('Head',-12*pulse,0,18*pulse);rot('Spine2',lean-5*pulse)
   if name.startswith('Hit'):rot('Spine2',lean-12*pulse,(15 if name=='HitLeft' else -15 if name=='HitRight' else 0)*pulse,0);rot('Head',-18*pulse)
   if name in ('AttackWindup','Attack','AttackRunning','Windup','Assault'):
    amount=q if name=='AttackWindup' else .8+.08*wave if name=='Windup' else 1-q if name=='Attack' else pulse
    side='Right' if brute or demon else 'Left';sign=-1 if side=='Right' else 1
    if soldier or warden:rot(side+'Arm',-115*amount,sign*(20+15*(1-amount)),0);rot(side+'ForeArm',-50*amount)
    elif demon:rot(side+'Arm',-55*amount,sign*15,sign*45*amount);rot(side+'ForeArm',-40*amount)
    else:rot(side+'Arm',-75*amount,sign*20,0);rot(side+'ForeArm',-25*amount)
    rot('Spine2',lean-9*amount,0,sign*10*amount);rot('Head',-6*amount)
   if name in ('Recovery','Spent','BossRecovery'):rot('Spine2',lean+10*pulse);rot('Head',12*pulse);move('Hips',(0,0,-.025*pulse))
   if name=='Brace':
    rot('Spine2',22+2*wave);rot('RightArm',-50,15,0);rot('RightForeArm',-65);move('Hips',(0,0,-.08));rot('LeftUpLeg',20);rot('RightUpLeg',20);rot('LeftLeg',-35);rot('RightLeg',-35)
   if name in ('LeapTakeoff','LeapAir','LeapLand','Scamper'):
    t=1-q if name=='LeapTakeoff' else .55+.08*wave if name=='LeapAir' else math.sin(q*math.pi) if name=='LeapLand' else .35
    move('Hips',(0,0,-.18*t));rot('Spine2',28+10*t)
    for side,sign in [('Left',1),('Right',-1)]:rot(side+'UpLeg',40*t);rot(side+'Leg',-70*t);rot(side+'Arm',-50*t,sign*20,0)
   if name in ('Death','Corpse'):
    t=1 if name=='Corpse' else min(1,q*1.35);rot('Hips',0,88*t,0);move('Hips',(0,0,-hip.z*.76*t));rot('Head',16*t);rot('Spine2',12*t)
    for side,sign in [('Left',1),('Right',-1)]:rot(side+'Arm',-20,sign*38,0);rot(side+'UpLeg',15*t);rot(side+'Leg',-30*t)
   if name in ('Sleep','Wake'):
    t=1 if name=='Sleep' else 1-q;rot('Spine2',30*t+lean*(1-t)+.8*wave*t);rot('Head',22*t);move('Hips',(0,0,-.22*t));rot('LeftUpLeg',45*t);rot('RightUpLeg',45*t);rot('LeftLeg',-80*t);rot('RightLeg',-80*t)
   if name in ('Death','Corpse'):
    for i in range(4):rot('Tail'+str(i+1))
   for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=f+1,group=b.name);b.keyframe_insert('location',frame=f+1,group=b.name)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.rotation_quaternion=Quaternion();b.location=(0,0,0)
 bpy.context.view_layer.update();progress('FBX export')
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in lods:o.select_set(True)
 bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.fbx(filepath=os.path.join(out,entity+'.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
 counts={}
 for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
 for o in lods[1:]:o.hide_render=True;o.hide_set(True)
 rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_start=1;scene.frame_end=91;scene.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,entity+'.blend'),compress=True)
 json.dump({'entity':entity,'status':'authored review asset; native combat integration pending','native_geometry_copied':False,'source_size_scale':SIZES[index],'rig_bones':len(rig.data.bones),'triangles':counts,'animations':{n:{'seconds':d,'loop':l} for n,(d,l) in clips.items()},'texture_size':2048,'materials':1,'uv_tile_validation':'PASS','root_motion':False,'damage_events':False},open(os.path.join(out,'asset-manifest.json'),'w'),indent=2)
 json.dump({n:nodes[n] for n in names},open(os.path.join(out,'rig-contract.json'),'w'),indent=2)
 open(os.path.join(out,'PROVENANCE.txt'),'w').write('Original project-authored mesh, atlas, weights and animation curves. Native skeleton transforms measured for fitting only. No native mesh, texture or animation copied. Presentation clips contain no damage or AI events. Existing game timing remains authoritative. Native entity, hitbox, ragdoll and multiplayer integration remain pending.\n')
 progress('PASS');print('FOREST_ENEMY_PASS',entity,counts,flush=True)
try:
 requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else IDS
 for entity in requested:
  if entity not in IDS:raise ValueError('Unknown enemy '+entity)
  build(entity)
except Exception:
 open(os.path.join(ROOT,'artifacts/forest-enemies/blender-error.txt'),'w').write(traceback.format_exc());raise





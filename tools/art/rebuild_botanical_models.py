"""Botanical rebuild: actual compound leaves, branching, inflorescences and gilled fungi.
Run with Blender --background --python ... . Original rigs/actions remain unchanged.
"""
from pathlib import Path
import bpy,math,random,json,sys,traceback
import numpy as np
from mathutils import Vector
STAGE=Path('D:/Projects/Codex/7DaysToDelve/PlantRebuild20261026')
specs=json.loads((STAGE/'plants.json').read_text())['assets']
TAU=math.tau

def textures():
    source=bpy.data.images.load(str(STAGE/'Artwork/BotanicalAtlas-original.png'),check_existing=False)
    # Original generated diffuse patches plus original pollen/petal/fabric swatches.
    source.scale(2048,1024);data=np.empty(2048*1024*4,np.float32);source.pixels.foreach_get(data);data=data.reshape(1024,2048,4)
    atlas=np.ones((1536,2048,4),np.float32);atlas[512:,:,:]=data
    rng=np.random.default_rng(91);y,x=np.mgrid[:512,:512]
    for i,c in enumerate(((.87,.83,.67),(.67,.43,.61),(.65,.43,.13),(.43,.31,.18))):
        noise=rng.normal(0,.012,(512,512));weave=.018*np.sin(x*1.57)*np.sin(y*1.57) if i==3 else .012*np.sin(y/35)
        atlas[:512,i*512:(i+1)*512,:3]=np.clip(np.array(c)+(noise+weave)[...,None],.01,.95)
    # Gentle micro-normal derived from diffuse detail, not a claimed high-poly bake.
    normal=np.ones_like(atlas);normal[:,:,:3]=(.5,.5,1)
    for row in range(3):
        for col in range(4):
            tile=atlas[row*512:(row+1)*512,col*512:(col+1)*512,:3];lum=tile@np.array((.2126,.7152,.0722));dy,dx=np.gradient(lum)
            n=np.stack((-dx*.85,-dy*.85,np.ones_like(dx)),axis=-1);n/=np.linalg.norm(n,axis=-1)[...,None];normal[row*512:(row+1)*512,col*512:(col+1)*512,:3]=n*.5+.5
    out=STAGE/'UnityProject/Assets/BotanicalTextures';out.mkdir(exist_ok=True)
    for name,pixels in [('Albedo',atlas),('Normal',normal)]:
        im=bpy.data.images.new('Botanical'+name,width=2048,height=1536);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(out/(name+'.png'));im.file_format='PNG';im.save()
    bpy.data.images.remove(source)

def uv(tile,u,v):
    # Tile indices follow artwork order, then cream / lavender / pollen / flax.
    row=2-tile//4;col=tile%4
    return ((col+.025+.95*u)/4,(row+.025+.95*v)/3)

class Geometry:
    def __init__(self,rng):self.v=[];self.f=[];self.uv=[];self.c=[];self.rng=rng;self.labels={}
    def part(self,vs,fs,tile,uvs=None,tint=(1,1,1),label='detail'):
        start=len(self.v);self.v.extend([tuple(p) for p in vs]);self.f.extend([tuple(start+i for i in f) for f in fs]);self.labels[label]=self.labels.get(label,0)+1
        if uvs is None:uvs=[(.5,.5)]*len(vs)
        self.uv.extend([uv(tile,*p) for p in uvs]);shade=self.rng.uniform(.84,1.05)
        self.c.extend([(*[min(1.3,t*shade) for t in tint],.88) for _ in vs])
    def tube(self,points,radius,tile=3,sides=7,label='branch',tint=(1,1,1)):
        pts=[Vector(p) for p in points];vs=[];uvs=[];fs=[]
        for i,p in enumerate(pts):
            d=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();side=d.cross(Vector((0,1,0)))
            if side.length<.01:side=d.cross(Vector((1,0,0)))
            side.normalize();other=d.cross(side);r=radius*(1-.72*i/(len(pts)-1))
            for j in range(sides+1):
                a=j*TAU/sides;vs.append(p+(side*math.cos(a)+other*math.sin(a))*r);uvs.append((j/sides,i/(len(pts)-1)))
        for i in range(len(pts)-1):
            for j in range(sides):a=i*(sides+1)+j;fs.append((a,a+1,a+sides+2,a+sides+1))
        self.part(vs,fs,tile,uvs,tint,label)
    def leaf(self,base,tip,width,tile=0,serrated=False,tint=(1,1,1),rings=8,roll=0,label='leaf'):
        a,b=Vector(base),Vector(tip);d=b-a;side=d.cross(Vector((0,0,1)))
        if side.length<.001:side=Vector((1,0,0))
        side.normalize();normal=side.cross(d).normalized();side=side*math.cos(roll)+normal*math.sin(roll);normal=side.cross(d).normalized()
        vs=[];uvs=[];fs=[]
        for i in range(rings+1):
            t=i/rings;profile=math.sin(math.pi*t)**.75
            if serrated:profile*=1 if i%2==0 else .82
            center=a+d*t+normal*(math.sin(math.pi*t)*width*.24)-Vector((0,0,1))*d.length*.13*t*t
            for k in (-1,0,1):
                vs.append(center+side*k*width*profile-normal*abs(k)*width*.16*profile);uvs.append((.5+.47*k,t))
        for i in range(rings):
            for j in range(2):p=i*3+j;fs.append((p,p+1,p+4,p+3))
        self.part(vs,fs,tile,uvs,tint,label)
    def sphere(self,p,scale,tile=7,tint=(1,1,1),sides=7,rings=4,label='fruit'):
        p=Vector(p);vs=[];uvs=[];fs=[]
        for i in range(rings+1):
            b=math.pi*i/rings
            for j in range(sides+1):
                a=TAU*j/sides;vs.append(p+Vector((math.sin(b)*math.cos(a)*scale[0],math.sin(b)*math.sin(a)*scale[1],math.cos(b)*scale[2])));uvs.append((j/sides,i/rings))
        for i in range(rings):
            for j in range(sides):a=i*(sides+1)+j;fs.append((a,a+1,a+sides+2,a+sides+1))
        self.part(vs,fs,tile,uvs,tint,label)
    def flower(self,p,r,lavender=False):
        p=Vector(p)
        for k in range(5):
            angle=k*TAU/5;direction=Vector((math.cos(angle),math.sin(angle),0));self.leaf(p,p+direction*r+Vector((0,0,r*.1)),r*.34,9 if lavender else 8,rings=3,label='petal')
        self.sphere(p+Vector((0,0,.001)),(r*.22,r*.22,r*.16),10,sides=5,rings=2,label='pollen')
    def berry(self,p,r,ripe=True):
        p=Vector(p)
        for j in range(18):
            z=1-2*(j+.5)/18;a=j*2.399963;xy=math.sqrt(1-z*z);pos=p+Vector((math.cos(a)*xy,math.sin(a)*xy,z*1.2))*r*.7
            self.sphere(pos,(r*.29,r*.29,r*.31),7,(1,1,1) if ripe else (1.8,.7,.65),sides=5,rings=3,label='berry drupelet')
        for j in range(5):a=j*TAU/5;self.leaf(p+Vector((0,0,r)),p+Vector((math.cos(a)*r*.7,math.sin(a)*r*.7,r*1.1)),r*.14,2,rings=2,label='fruit calyx')

def bramble(g,stage,scale=1,origin=(0,0,0),compact=False):
    origin=Vector(origin);h=(.19,.58,.86,.43)[stage-1]*scale;count=(2,4,5,4)[stage-1] if not compact else 2
    for j in range(count):
        angle=j*2.399+g.rng.uniform(-.25,.25);reach=h*g.rng.uniform(.34,.58);tip=origin+Vector((math.cos(angle)*reach,math.sin(angle)*reach,h*g.rng.uniform(.7,1)));bend=origin+Vector((math.cos(angle)*reach*.28,math.sin(angle)*reach*.28,h*.65));base=origin+Vector((math.cos(angle)*.025,math.sin(angle)*.025,0))*scale;points=[base,base.lerp(bend,.45)+Vector((0,0,h*.035)),bend,bend.lerp(tip,.6),tip]
        g.tube(points,.007*scale if stage>1 else .003*scale,sides=8)
        for k in range(1,5 if stage>1 else 3):
            t=k/5;node=bend.lerp(tip,max(0,(t-.5)*2)) if t>.5 else origin.lerp(bend,t*2);a=angle+(-1 if k%2 else 1)*1.6;length=h*(.17 if stage>1 else .40);end=node+Vector((math.cos(a)*length,math.sin(a)*length,.035*scale));g.tube([node,end],.0018*scale,2,sides=5,label='petiole')
            for m in range(3 if stage>1 else 1):
                aa=a+(m-1)*.85;start=end if m==1 else node.lerp(end,.7);ll=(.105 if stage>1 else .07)*scale*g.rng.uniform(.8,1.15);to=start+Vector((math.cos(aa)*ll,math.sin(aa)*ll,ll*.27));g.leaf(start,to,ll*.34,0,True,rings=12,roll=g.rng.uniform(-.35,.35),label='serrated bramble leaflet')
            if stage>1:
                pos=node+Vector((math.cos(a+1)*.012,math.sin(a+1)*.012,0));g.tube([node,pos,pos+Vector((0,0,.018*scale))],.002*scale,3,sides=4,label='recurved thorn')
        if stage==3:
            stalk=tip+Vector((0,0,-.025*scale));g.tube([tip,stalk],.0015*scale,2,sides=5)
            for k in range(2):g.berry(stalk+Vector(((k-.5)*.04*scale,0,-.01*scale)),.021*scale,ripe=(j+k)%5!=0)
            if j%2==0:
                flower=tip+Vector((.025,0,.015))*scale;g.tube([tip,flower],.0008*scale,2,sides=5,label='flower pedicel');g.flower(flower,.015*scale)

def yarrow(g,stage,scale=1,origin=(0,0,0),compact=False,dry=False):
    origin=Vector(origin);h=(.16,.38,.61,.23)[stage-1]*scale;count=(2,4,6,4)[stage-1] if not compact else 3;tint=(1.18,.95,.65) if dry else (1,1,1)
    for j in range(count):
        a=j*2.399;top=origin+Vector((math.cos(a)*h*.22,math.sin(a)*h*.22,h*g.rng.uniform(.78,1)));g.tube([origin,origin.lerp(top,.35)+Vector((.015*scale,0,0)),top],.0025*scale,11 if dry else 1,sides=6,tint=tint)
        for k in range(1,5):
            node=origin.lerp(top,k/6);angle=a+k*2.4;length=(.09 if stage>1 else .055)*scale;end=node+Vector((math.cos(angle)*length,math.sin(angle)*length,length*.23));g.tube([node,end],.0007*scale,1,sides=4,tint=tint,label='feather midrib');d=end-node;side=Vector((-d.y,d.x,0)).normalized()
            for n in range(1,7):
                t=n/8;pos=node+d*t;ll=length*.26*math.sin(math.pi*t)
                for sign in (-1,1):g.leaf(pos,pos+side*sign*ll+d*.10,ll*.22,11 if dry else 1,rings=3,tint=tint,roll=g.rng.uniform(-.4,.4),label='yarrow feather leaflet')
        if stage==3:
            for n in range(8):
                angle=n*2.399;r=math.sqrt(n/8)*.052*scale;end=top+Vector((math.cos(angle)*r,math.sin(angle)*r,.008*scale+(1-r/(.06*scale))*.007*scale));g.tube([top-Vector((0,0,.045*scale)),end],.0007*scale,1,sides=4,label='corymb branch')
                for small in range(3):
                    aa=small*TAU/3;flower=end+Vector((math.cos(aa)*.005,math.sin(aa)*.005,.002))*scale;g.tube([end,flower],.00035*scale,1,sides=3,label='corymb pedicel');g.flower(flower,.006*scale)
    if stage>1 and not compact:
        # Ground rosette: the tall inflorescences emerge from a feathered crown.
        for j in range(9):
            a=j*2.399;d=Vector((math.cos(a),math.sin(a),.3));length=.11*scale;tip=origin+d*length;g.tube([origin,tip],.001*scale,1,sides=4,tint=tint,label='basal leaf rachis');side=Vector((-d.y,d.x,0))
            for n in range(1,9):
                t=n/10;p=origin+d*length*t;ll=length*.23*math.sin(math.pi*t)
                for sign in (-1,1):g.leaf(p,p+side*ll*sign+d*.008*scale,ll*.2,1,rings=3,tint=tint,label='basal feather leaflet')

def thyme(g,stage,scale=1,origin=(0,0,0),compact=False,dry=False):
    origin=Vector(origin);h=(.095,.23,.32,.15)[stage-1]*scale;count=(3,7,11,7)[stage-1] if not compact else 4;tint=(1.2,.95,.62) if dry else (1,1,1)
    for j in range(count):
        a=j*2.399;top=origin+Vector((math.cos(a)*h*.5,math.sin(a)*h*.5,h*g.rng.uniform(.55,1)));bend=origin.lerp(top,.55)+Vector((0,0,h*.1));g.tube([origin,bend,top],.002*scale,3,sides=5)
        for k in range(1,8):
            t=k/8;node=origin.lerp(top,t)+Vector((0,0,h*.1*math.sin(math.pi*t)));angle=a+k*math.pi*.5;length=.018*scale*g.rng.uniform(.8,1.3)
            for sign in (-1,1):g.leaf(node,node+Vector((math.cos(angle)*length*sign,math.sin(angle)*length*sign,length*.26)),length*.35,11 if dry else 2,rings=4,tint=tint,roll=g.rng.uniform(-.25,.25),label='opposite thyme leaf')
            if stage>1 and k in (2,4):
                aa=angle+1.3;end=node+Vector((math.cos(aa)*h*.22,math.sin(aa)*h*.22,h*.18));g.tube([node,end],.0008*scale,3,sides=4,label='thyme lateral shoot')
                for n in range(1,5):
                    p=node.lerp(end,n/5);ll=.014*scale;direction=Vector((math.cos(aa+math.pi/2),math.sin(aa+math.pi/2),.25))
                    for sign in (-1,1):g.leaf(p,p+direction*ll*sign,ll*.38,11 if dry else 2,rings=4,tint=tint,label='lateral opposite leaf')
        if stage==3 and not dry:
            for n in range(3):angle=n*2.399;g.flower(top+Vector((math.cos(angle)*.008,math.sin(angle)*.008,n*.003))*scale,.005*scale,True)

def mooncap(g,stage,scale=1,origin=(0,0,0),compact=False):
    origin=Vector(origin);count=(2,4,6,3)[stage-1] if not compact else 3
    for j in range(count):
        a=j*2.399;ss=(.4,.65,1,.25)[stage-1]*scale*g.rng.uniform(.64,1.1);p=origin+Vector((math.cos(a)*.13*scale*math.sqrt(j/max(1,count)),math.sin(a)*.13*scale*math.sqrt(j/max(1,count)),0));height=.16*ss;rad=.085*ss;tilt=Vector((g.rng.uniform(-.016,.016),g.rng.uniform(-.016,.016),0))*ss
        g.tube([p,p+Vector((0,0,height*.45))+tilt*.35,p+Vector((0,0,height))+tilt],.016*ss,6,sides=12,label='fibrous fungus stipe')
        center=p+Vector((0,0,height))+tilt;vs=[];uvs=[];fs=[];rings=9;sides=36
        for k in range(rings+1):
            t=k/rings;r=rad*t;z=rad*.53*(1-t*t)-rad*.08*t**7
            for n in range(sides+1):
                angle=n*TAU/sides;rr=r*(1+.027*math.sin(angle*7+j)+.015*math.sin(angle*13));vs.append(center+Vector((math.cos(angle)*rr,math.sin(angle)*rr,z+rad*.015*math.sin(angle*9)*t)));uvs.append((.5+.46*t*math.cos(angle),.5+.46*t*math.sin(angle)))
        for k in range(rings):
            for n in range(sides):q=k*(sides+1)+n;fs.append((q,q+sides+1,q+sides+2,q+1))
        g.part(vs,fs,4,uvs,(1,1,1),'irregular domed cap')
        vs=[center+Vector((0,0,-.008*ss))];uvs=[(.5,.5)];rim=[]
        for n in range(sides+1):
            angle=n*TAU/sides;rr=rad*(1+.027*math.sin(angle*7+j)+.015*math.sin(angle*13));edge=center+Vector((math.cos(angle)*rr,math.sin(angle)*rr,-rad*.08+rad*.015*math.sin(angle*9)));rim.append(edge);vs.append(edge-Vector((0,0,.0015*ss)));uvs.append((.5+.46*math.cos(angle),.5+.46*math.sin(angle)))
        g.part(vs,[(0,n+2,n+1) for n in range(sides)],5,uvs,label='gilled underside')
        lip=[];lipuv=[]
        for n,p in enumerate(rim):lip.extend([p,p-Vector((0,0,.0015*ss))]);lipuv.extend([(n/sides,.50),(n/sides,.55)])
        g.part(lip,[(n*2,n*2+1,n*2+3,n*2+2) for n in range(sides)],6,lipuv,label='continuous rolled cap rim')
        for n in range(24):
            a=n*TAU/24;v=Vector((math.cos(a),math.sin(a),0));side=Vector((-v.y,v.x,0))*rad*.006;start=center+v*rad*.2-Vector((0,0,.006*ss));end=center+v*rad*.94-Vector((0,0,.008*ss));g.part([start-side,start+side,end+side,end-side,end-Vector((0,0,.003*ss))],[(0,1,2,3),(0,3,4),(3,2,4)],5,[(.5,.5)]*5,label='radial gill ridge')

def build(spec):
    identity=spec['id'];bpy.ops.wm.open_mainfile(filepath=spec['source']);rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');before={a.name:tuple(a.frame_range) for a in bpy.data.actions};bones={b.name:tuple(tuple(row) for row in b.matrix_local) for b in rig.data.bones}
    for o in list(bpy.data.objects):
        if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
    for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0);b.scale=(1,1,1)
    rng=random.Random(identity);g=Geometry(rng);family=spec.get('plant',spec['family']);kind=spec['kind'];stage=spec.get('stage',3)
    if family not in ('Bramble','Yarrow','Thyme','Mooncap'):
        family=next(f for f in ('Bramble','Yarrow','Thyme','Mooncap') if f in identity)
    builder={'Bramble':bramble,'Yarrow':yarrow,'Thyme':thyme,'Mooncap':mooncap}[family]
    if kind=='plant':builder(g,stage)
    elif identity.endswith('1_Seed'):
        # A folded flax seed envelope with tucked flap, cord and specimen mark.
        w=.095;h=.13;t=.009
        g.part([(-w,-t,0),(w,-t,0),(w,-t,h),(-w,-t,h),(-w,t,0),(w,t,0),(w,t,h),(-w,t,h)],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],11,[(0,0),(1,0),(1,1),(0,1)]*2,label='seed envelope')
        g.part([(-w,-t-.001,h),(w,-t-.001,h),(0,-t-.003,h*.58)],[(0,1,2)],11,[(0,1),(1,1),(.5,.58)],(.85,.85,.85),'folded flap')
        for x in (-.064,.064):g.tube([(x,-t-.004,0),(x,-t-.004,h),(x,t+.004,h),(x,t+.004,0)],.0015,6,sides=5,label='seed packet cord')
        # Small botanical specimen rests against packet, keeping family recognition.
        builder(g,1,.45,origin=(0,-.025,.01),compact=True)
    elif family=='Bramble':
        for j in range(7):a=j*2.399;g.berry((.07*math.cos(a)*math.sqrt(j/7),.055*math.sin(a)*math.sqrt(j/7),.028+.012*(j%2)),.025)
        g.leaf((-.06,.02,.015),(.055,.08,.027),.035,0,True,rings=12)
    elif family=='Mooncap':mooncap(g,3,.8,compact=True)
    else:
        dry='Dried' in identity;builder(g,3,.48,compact=True,dry=dry)
        # A short tied bundle keeps fresh/dried harvest items recognisable.
        for z in (.026,.035):g.tube([(.014*math.cos(n*TAU/12),.012*math.sin(n*TAU/12),z) for n in range(13)],.0015,6,sides=5,label='herb bundle tie')
    mesh=bpy.data.meshes.new(identity+'_BotanicalMesh');mesh.from_pydata(g.v,[],g.f);mesh.update();obj=bpy.data.objects.new('Prop_LOD0',mesh);bpy.context.collection.objects.link(obj)
    layer=mesh.uv_layers.new(name='UVMap');colors=mesh.color_attributes.new(name='BotanicalVariation',type='FLOAT_COLOR',domain='CORNER')
    maxz=max(v[2] for v in g.v)
    for poly in mesh.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index;layer.data[li].uv=g.uv[vi];c=g.c[vi];colors.data[li].color=(*c[:3],.80+.20*min(1,max(0,g.v[vi][2])/maxz))
    root=obj.vertex_groups.new(name='Root');wind=obj.vertex_groups.new(name='Wind')
    for v in mesh.vertices:
        weight=min(.9,max(0,v.co.z/maxz)**1.25*.88) if kind=='plant' else 0
        root.add([v.index],1-weight,'REPLACE')
        if weight>0:wind.add([v.index],weight,'REPLACE')
    mat=bpy.data.materials.new('BotanicalSurface');mat.use_nodes=True;nodes=mat.node_tree.nodes;bsdf=nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.79;tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(STAGE/'UnityProject/Assets/BotanicalTextures/Albedo.png'));mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);color=nodes.new('ShaderNodeVertexColor');color.layer_name='BotanicalVariation';mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mat.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(color.outputs['Color'],mix.inputs[2]);mat.node_tree.links.new(mix.outputs['Color'],bsdf.inputs['Base Color']);mesh.materials.append(mat)
    obj.parent=rig;mod=obj.modifiers.new('Skin','ARMATURE');mod.object=rig;lods=[obj]
    for level,ratio in ((1,.38),(2,.11)):
        duplicate=obj.copy();duplicate.data=mesh.copy();bpy.context.collection.objects.link(duplicate);duplicate.name='Prop_LOD'+str(level)
        for mod in list(duplicate.modifiers):duplicate.modifiers.remove(mod)
        bpy.context.view_layer.objects.active=duplicate;mod=duplicate.modifiers.new('Botanical LOD','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name);mod=duplicate.modifiers.new('Skin','ARMATURE');mod.object=rig;lods.append(duplicate)
    assert before=={a.name:tuple(a.frame_range) for a in bpy.data.actions},'Animation contract changed'
    assert bones=={b.name:tuple(tuple(row) for row in b.matrix_local) for b in rig.data.bones},'Skeleton changed'
    for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0);b.scale=(1,1,1)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for o in lods:o.select_set(True);o.hide_set(False);o.hide_render=False
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(STAGE/'UnityProject/Assets/Models'/(identity+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
    out=STAGE/'Sources'/identity;out.mkdir(exist_ok=True)
    for o in lods[1:]:o.hide_render=True;o.hide_set(True)
    if 'Idle' in bpy.data.actions:rig.animation_data.action=bpy.data.actions['Idle']
    bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/(identity+'.blend')),compress=True)
    counts=[]
    for o in lods:o.data.calc_loop_triangles();counts.append(len(o.data.loop_triangles))
    (out/'model.json').write_text(json.dumps({'id':identity,'family':family,'stage':stage,'kind':kind,'triangles':counts,'parts':g.labels,'bones':len(bones),'clips':len(before),'geometry':'original reconstructed botanical forms','texture':'original AI diffuse atlas + procedural swatches; gentle image-derived micro normal'},indent=2))
    print('BOTANICAL_PASS',identity,counts,flush=True)

try:
    textures();requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    completed=0
    for spec in specs:
        if requested and spec['id'] not in requested:continue
        (STAGE/'Reports/blender-progress.txt').write_text('BUILDING '+spec['id']);build(spec);completed+=1
    (STAGE/'Reports/blender-progress.txt').write_text('PASS rebuilt '+str(completed)+' selected botanical models')
except Exception:
    (STAGE/'Reports/blender-error.txt').write_text(traceback.format_exc());raise

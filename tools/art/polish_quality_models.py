"""Non-destructive Blender pass over existing sources; retains their animation data."""
import bpy,bmesh,sys,os,json,math,traceback,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from quality_surfaces import build_surfaces,KINDS
STAGE=Path('D:/AlliumArt/QualityPass20261025')
inventory=json.loads((STAGE/'inventory.json').read_text())['models']
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def components(mesh):
    parent=list(range(len(mesh.vertices)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for edge in mesh.edges:
        a,b=edge.vertices;parent[find(a)]=find(b)
    result={}
    for i in range(len(parent)):result.setdefault(find(i),[]).append(i)
    return sorted(result.values(),key=len,reverse=True)
def tile_ids(mesh):
    tiles=[0]*len(mesh.vertices);uv=mesh.uv_layers.active
    for face in mesh.polygons:
        ids=list(face.loop_indices);center=sum((uv.data[j].uv for j in ids),Vector((0,0)))/len(ids)
        tile=min(3,max(0,int(center.x*4)))+4*min(3,max(0,int(center.y*4)))
        for vi in face.vertices:tiles[vi]=tile
    return tiles
def anatomy(obj,rig,spec):
    group=spec['group'];mesh=obj.data;parts=components(mesh);tiles=tile_ids(mesh);body=set(parts[0]);changes=[]
    def bone(name):return obj.matrix_world.inverted()@rig.matrix_world@rig.data.bones[name].head_local
    if group not in ('enemies','quadrupeds','thornback'):return tiles,parts,changes
    head=bone('Head');hip=bone('Hips');chest=bone('Spine3' if group=='enemies' else 'Spine1' if 'Spine1' in rig.data.bones else 'Spine')
    # Resolve the exaggerated separate eye forms before adding surface texture.
    for ids in parts[1:]:
        if len(ids)<4:continue
        c=sum((mesh.vertices[i].co for i in ids),Vector())/len(ids)
        if sum(tiles[i]==4 for i in ids)/len(ids)>.8 and (c-head).length<.35:
            for i in ids:mesh.vertices[i].co=c+(mesh.vertices[i].co-c)*.58
            changes.append('recessed proportional eyes')
    if group=='enemies':
        for i in body:
            v=mesh.vertices[i];p=v.co
            # Broad, continuous sculpt changes, confined to the front of the torso.
            front=max(0,min(1,(chest.y-p.y+.015)/.12))
            if hip.z+.04<p.z<chest.z+.22 and abs(p.x-hip.x)<.30:
                x=p.x-hip.x;z=p.z-chest.z
                pec=math.exp(-((abs(x)-.105)/.08)**2-((z-.06)/.075)**2)
                sternum=math.exp(-(x/.023)**2-((z-.03)/.17)**2)
                absrelief=sum(math.exp(-((abs(x)-.048)/.038)**2-((z+a)/.025)**2) for a in (.10,.17,.24))
                v.co.y-=front*(.016*pec+.006*absrelief-.009*sternum)
            if (p-head).length<.19:
                # Narrow lower jaw and define a forehead/cheek transition.
                f=math.exp(-((p.z-head.z-.02)/.07)**2)
                v.co.x=head.x+(p.x-head.x)*(1-.08*f)
        changes+=['pectoral/sternum/abdominal planes','narrowed lower facial contour']
    else:
        for i in body:
            v=mesh.vertices[i];p=v.co;dx=abs(p.x-hip.x)
            # Lateral ribcage/tendon break-up and a leaner underbelly, without moving joints.
            side=max(0,min(1,dx/.13));rib=math.exp(-((p.y-chest.y-.10)/.20)**2-((p.z-chest.z+.05)/.16)**2)
            v.co.x+=math.copysign(.005*math.sin((p.y-chest.y)*53)*rib*side,p.x-hip.x)
            if spec['id']=='delveGloomcat' and (p-head).length<.22:v.co.x=head.x+(p.x-head.x)*.91
        changes+=['subtle ribcage and tendon planes','fur silhouette details']
    mesh.update();return tiles,parts,changes
def native_details_only(obj,rig,spec):
    mesh=obj.data;parts=components(mesh);tiles=tile_ids(mesh);keep=set();identity=spec['id'];inv=obj.matrix_world.inverted()@rig.matrix_world
    head=inv@rig.data.bones['Head'].head_local;hip=inv@rig.data.bones['Hips'].head_local
    for ids in parts[1:]:
        c=sum((mesh.vertices[i].co for i in ids),Vector())/len(ids);tile=max(set(tiles[i] for i in ids),key=lambda t:sum(tiles[i]==t for i in ids));retain=False
        if identity=='delveCorruptedWalker':retain=tile in (1,5) and c.z>hip.z+.12
        elif identity=='delveImp':
            tail=any(obj.vertex_groups[g.group].name.startswith('Tail') for i in ids for g in mesh.vertices[i].groups)
            retain=tail or tile==2 and c.z>head.z+.12 or tile==6 and abs(c.x-head.x)>.13
        elif identity=='delveDemonSpawn':retain=tile==7
        elif identity=='delvePossessedSoldier':retain=tile in (7,8,9) and c.z<head.z-.08
        elif identity=='delveWarpedBrute':retain=tile==8
        elif identity=='delveAshboundWarden':retain=tile in (7,8,9) or tile==4 and c.z<head.z-.1
        elif identity=='delveThornbackBoar':retain=tile in (1,9,5,13) and c.z>hip.z-.05
        elif identity=='delveHellhound':retain=tile in (5,8) and c.z>hip.z-.1 or tile==1 and c.z>hip.z+.06 and abs(c.x-hip.x)<.09
        elif identity=='delveGloomcat':
            tail=any(obj.vertex_groups[g.group].name.startswith('Tail') for i in ids for g in mesh.vertices[i].groups)
            retain=tile==1 and (tail or abs(c.x-head.x)>.11 and (c-head).length<.35)
        elif identity=='delveCrystalStag':retain=tile in (5,10,14) and c.z>hip.z
        if retain:keep.update(ids)
    # Never export a second creature body, eyes, muzzle, hands or feet.
    if not keep:raise ValueError('No identity details selected for '+identity)
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in keep],context='VERTS');bm.to_mesh(mesh);bm.free();mesh.update()
    return tile_ids(mesh),components(mesh),['native body, face, limbs and skin retained at runtime','original identity details only; duplicate anatomy removed']
def add_details(obj,rig,spec,tiles,parts):
    mesh=obj.data;group=spec['group'];kinds=KINDS.get(group,KINDS['props']);verts=[];faces=[];uvs=[];weights=[]
    # Geometry is attached with the source vertex's actual skin weights.
    def emit(points,fs,tile,source):
        start=len(verts);verts.extend(points);faces.extend(tuple(start+j for j in f) for f in fs)
        weights.extend([[ (obj.vertex_groups[g.group].name,g.weight) for g in source.groups] for _ in points])
        r,c=divmod(tile,4);uvs.extend([((c+.22+(j%2)*.56)/4,(r+.22+(j%3)*.25)/4) for j in range(len(points))])
    mesh.update();body=set(parts[0]);added=0
    if group in ('quadrupeds','thornback'):
        candidates=[i for i in parts[0] if tiles[i] in (0,8) and mesh.vertices[i].normal.z>-.25]
        stride=max(1,len(candidates)//220)
        for i in candidates[::stride]:
            v=mesh.vertices[i];p=v.co;n=v.normal.normalized();side=n.cross(Vector((0,1,0)))
            if side.length<.1:side=n.cross(Vector((1,0,0)))
            side.normalize();length=.022 if group=='thornback' else .014
            emit([p-side*.003,p+side*.003,p+n*length+Vector((0,.012,-.003))],[(0,1,2),(2,1,0)],1 if group=='quadrupeds' else 8,v);added+=1
    elif group=='enemies':
        # Raised scars stay close to the surface; no replacement hitboxes or bones.
        candidates=[i for i in parts[0] if tiles[i]==0 and mesh.vertices[i].normal.y<-.55]
        for i in candidates[::max(1,len(candidates)//35)]:
            v=mesh.vertices[i];p=v.co;n=v.normal.normalized();t=n.cross(Vector((1,0,.3))).normalized();side=n.cross(t)
            emit([p-t*.011,p+side*.002+n*.0015,p+t*.011,p-side*.002+n*.0015],[(0,1,2),(0,2,3)],6,v);added+=1
    elif group in ('props','armor'):
        for ids in parts:
            if len(ids)<20:continue
            tile=tiles[ids[0]];kind=kinds[tile]
            if kind not in ('wood','metal','leather','cloth'):continue
            # Keep small-scale construction detail within the original silhouette.
            for i in ids[::max(1,len(ids)//2)][:2]:
                v=mesh.vertices[i];p=v.co;n=v.normal.normalized()
                if n.length<.5:continue
                t=n.cross(Vector((0,0,1)))
                if t.length<.1:t=n.cross(Vector((0,1,0)))
                t.normalize();b=n.cross(t);radius=.002 if group=='armor' else .0018
                if kind in ('wood','metal'):
                    emit([p+t*radius,p+b*radius,p-t*radius,p-b*radius,p+n*radius*.6],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],2,v)
                else:emit([p-t*.004-b*.0006,p+t*.004-b*.0006,p+t*.004+b*.0006+n*.0005,p-t*.004+b*.0006+n*.0005],[(0,1,2),(0,2,3)],4 if group=='armor' else 8,v)
                added+=1
            if added>=100:break
    if not verts:return 0
    data=bpy.data.meshes.new('SurfaceConstruction');data.from_pydata(verts,[],faces);data.update();layer=data.uv_layers.new(name='UVMap')
    for loop in data.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
    detail=bpy.data.objects.new('SurfaceConstruction',data);bpy.context.collection.objects.link(detail);detail.matrix_world=obj.matrix_world.copy()
    for name in {n for pairs in weights for n,w in pairs}:detail.vertex_groups.new(name=name)
    for i,pairs in enumerate(weights):
        for name,w in pairs:detail.vertex_groups[name].add([i],w,'REPLACE')
    detail.data.materials.append(obj.data.materials[0]);bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);detail.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.join();return added
def paint(obj):
    mesh=obj.data;mesh.update();mesh.calc_loop_triangles();bvh=BVHTree.FromPolygons([v.co for v in mesh.vertices],[t.vertices for t in mesh.loop_triangles],all_triangles=True)
    attr=mesh.color_attributes.get('QualityColor') or mesh.color_attributes.new(name='QualityColor',type='FLOAT_COLOR',domain='POINT');mesh.color_attributes.active_color=attr
    for v,d in zip(mesh.vertices,attr.data):
        p=v.co;n=v.normal.normalized();t=n.cross(Vector((0,0,1)))
        if t.length<.1:t=n.cross(Vector((0,1,0)))
        t.normalize();b=n.cross(t);blocked=0
        for ray in (n*.8+t*.6,n*.8-t*.3+b*.52,n*.8-t*.3-b*.52):
            hit=bvh.ray_cast(p+n*.0015,ray.normalized(),.07)
            if hit[0] is not None:blocked+=1
        ao=1-blocked*.14;wave=math.sin(p.x*31+math.sin(p.y*17))*math.sin(p.z*23+p.y*9);shade=.94+wave*.065
        d.color=(shade,shade*(1+wave*.016),shade*(1-wave*.02),ao)
def process(spec):
    out=Path(spec['destination']);out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=spec['blend']);scene=bpy.context.scene
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=None
    for p in rig.pose.bones:p.location=(0,0,0);p.rotation_euler=(0,0,0);p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
    scene.frame_set(1);bpy.context.view_layer.update()
    bones_before={b.name:list(b.matrix_local) for b in rig.data.bones};actions_before={a.name:tuple(a.frame_range) for a in bpy.data.actions}
    target=spec['slot']+'_LOD0';mesh=bpy.data.objects.get(target)
    if mesh is None:raise ValueError('Missing '+target+' in '+spec['blend'])
    mesh.hide_set(False);mesh.hide_render=False
    for o in list(bpy.data.objects):
        if o.type=='MESH' and o!=mesh:bpy.data.objects.remove(o,do_unlink=True)
    texture_id=spec['id'] if spec['group'] in ('enemies','quadrupeds','thornback') else spec['group']
    textures=STAGE/'UnityProject/Assets/QualitySurfaces'/texture_id
    source=STAGE/'UnityProject/Assets/Legacy'/spec['group']/spec['texture']
    if not (textures/'Albedo.png').exists():images=build_surfaces(bpy,str(source),spec['group'],spec['id'],str(textures))
    else:images={n:bpy.data.images.load(str(textures/(n+'.png')),check_existing=True) for n in ('Albedo','Normal','Metallic','Occlusion','Emission')}
    material=bpy.data.materials.new('Quality_'+texture_id);material.use_nodes=True;bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7
    tx=material.node_tree.nodes.new('ShaderNodeTexImage');tx.image=images['Albedo'];material.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mesh.data.materials.clear();mesh.data.materials.append(material)
    native=spec['group'] in ('enemies','quadrupeds','thornback')
    if native:tiles,parts,changes=native_details_only(mesh,rig,spec);details=0
    else:tiles,parts,changes=anatomy(mesh,rig,spec);details=add_details(mesh,rig,spec,tiles,parts)
    # Preserve normals on hard fittings. Only small prop edges receive an extra bevel.
    if spec['group']=='props' and spec['kind']!='plant':
        bpy.context.view_layer.objects.active=mesh;bev=mesh.modifiers.new('Crafted edge bevel','BEVEL');bev.width=.0008;bev.segments=2;bev.limit_method='ANGLE';bev.angle_limit=.7
        bpy.ops.object.modifier_move_up(modifier=bev.name);bpy.ops.object.modifier_apply(modifier=bev.name)
    paint(mesh);lods=[mesh]
    for level,ratio in ((1,.50),(2,.20)):
        o=mesh.copy();o.data=mesh.data.copy();bpy.context.collection.objects.link(o);o.name=spec['slot']+'_LOD'+str(level)
        for mod in list(o.modifiers):o.modifiers.remove(mod)
        bpy.context.view_layer.objects.active=o;dec=o.modifiers.new('Quality LOD','DECIMATE');dec.ratio=ratio;bpy.ops.object.modifier_apply(modifier=dec.name);skin=o.modifiers.new('Skin','ARMATURE');skin.object=rig;lods.append(o)
    assert actions_before=={a.name:tuple(a.frame_range) for a in bpy.data.actions}
    assert bones_before=={b.name:list(b.matrix_local) for b in rig.data.bones}
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for o in lods:o.hide_set(False);o.hide_render=False;o.select_set(True)
    bpy.context.view_layer.objects.active=rig
    fbx=STAGE/'UnityProject/Assets/Legacy'/spec['group']/spec['fbx']
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
    for image in images.values():image.pack()
    for o in lods[1:]:o.hide_render=True;o.hide_set(True)
    if 'Idle' in bpy.data.actions:rig.animation_data.action=bpy.data.actions['Idle']
    scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/(spec['id']+'.blend')),compress=True)
    counts={}
    for o in lods:o.data.calc_loop_triangles();counts[o.name]=len(o.data.loop_triangles)
    result=dict(id=spec['id'],status='PASS',bones=len(bones_before),actions=len(actions_before),triangles=counts,details=details,changes=changes,source=spec['blend'],texture_id=texture_id,native_foundation=native)
    (out/'quality.json').write_text(json.dumps(result,indent=2));print('QUALITY_PASS',spec['id'],counts,flush=True)
try:
    for spec in inventory:
        if not spec['blend'] or requested and spec['id'] not in requested and spec['group'] not in requested:continue
        if (Path(spec['destination'])/'quality.json').exists() and '--force' not in requested:continue
        (STAGE/'Reports/blender-progress.txt').write_text('BUILDING '+spec['id']);process(spec)
    (STAGE/'Reports/blender-progress.txt').write_text('PASS selected sources')
except Exception:
    (STAGE/'Reports/blender-error.txt').write_text(traceback.format_exc());raise

"""Original deterministic PBR surfaces; no downloaded or native game textures."""
import math
def weapon_surfaces(bpy, np, out):
    import os
    size=2048; cell=size//4
    y,x=np.mgrid[0:cell,0:cell].astype(np.float32); u=x/cell; v=y/cell
    rng=np.random.default_rng(718)
    maps={n:np.ones((size,size,4),np.float32) for n in ('Atlas','Normal','Metallic','Occlusion','Emission')}
    colors=[(.43,.255,.105),(.19,.085,.038),(.53,.57,.60),(.16,.18,.20),(.51,.28,.105),(.30,.12,.055),(.08,.43,.72),(.82,.24,.035),(.38,.08,.52),(.055,.39,.19),(.055,.40,.46),(.72,.64,.43),(.035,.028,.022),(.32,.34,.32),(.42,.46,.28),(.57,.35,.12)]
    for i,base in enumerate(colors):
        noise=rng.normal(0,1,(cell,cell)).astype(np.float32)
        broad=(np.sin(u*19+np.sin(v*11))*np.sin(v*23-u*9)+np.sin(u*41+v*31))*.5
        height=noise*.03; variation=broad*.06; metal=0; rough=.75
        if i in (0,4):
            warp=u*110+np.sin(v*9)*3+np.sin(v*27)*.6
            grain=np.sin(warp)+.4*np.sin(warp*2.73)
            pores=np.maximum(0,-np.sin(warp*3.2)-.83)
            knot=np.sin(np.sqrt(((u-.62)*2.8)**2+((v-.43)*.7)**2)*150)
            mask=np.exp(-(((u-.62)/.13)**2+((v-.43)/.23)**2))
            height=grain*.16-pores*.5+knot*mask*.18+noise*.025
            variation=height*.18+broad*.065;rough=.63
        elif i in (1,5):
            creases=np.maximum(0,np.sin(u*43+np.sin(v*37)*2)*np.sin(v*57+u*8)-.65)
            height=noise*.07-creases*.6;variation=broad*.06-creases*.2+noise*.013;rough=.76
        elif i in (2,3,15):
            scratch=np.maximum(0,np.sin(v*530+np.sin(u*8))-.96)*(np.sin(u*23)>.15)
            pits=np.maximum(0,noise-1.7)
            height=noise*.025-pits*.12-scratch*.16
            variation=broad*.045+scratch*.20-pits*.045;metal=.92 if i!=3 else .75;rough=.34 if i==2 else .48
        elif i==11:
            height=np.sin(u*170+np.sin(v*13))*.045+noise*.015
            variation=broad*.055+height*.3;rough=.48
        elif i==14:
            weave=np.sin(u*math.tau*95)*np.sin(v*math.tau*95)
            height=weave*.12+noise*.025;variation=weave*.045+broad*.07;rough=.9
        elif 6<=i<=10:
            veins=np.exp(-np.abs(np.sin(u*19+v*11+np.sin(v*17)))*45)
            height=veins*.03;variation=broad*.08+veins*.22;metal=.15;rough=.19
        else:
            height=noise*.065+broad*.1;variation=broad*.07+noise*.02
        row,col=divmod(i,4);sl=np.s_[row*cell:(row+1)*cell,col*cell:(col+1)*cell]
        maps['Atlas'][sl][:,:,:3]=np.clip(np.array(base)+variation[:,:,None],.008,.95)
        dy,dx=np.gradient(height);normal=np.stack((-dx*2,-dy*2,np.ones_like(dx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        maps['Normal'][sl][:,:,:3]=normal*.5+.5
        maps['Metallic'][sl][:,:,:3]=metal
        maps['Metallic'][sl][:,:,3]=np.clip(1-rough+variation*.25,.05,.88)
        maps['Occlusion'][sl][:,:,:3]=np.clip(1+height[:,:,None]*.32,.6,1)
        maps['Emission'][sl][:,:,:3]=np.array(base)*(.22 if 6<=i<=10 else 0)
    result={}
    for name,px in maps.items():
        image=bpy.data.images.new('ForestWeapon'+name,width=size,height=size,alpha=True)
        if name not in ('Atlas','Emission'):image.colorspace_settings.name='Non-Color'
        image.pixels.foreach_set(px.ravel());image.filepath_raw=os.path.join(out,'ForestWeapon'+name+'.png');image.file_format='PNG';image.save();image.pack();result[name]=image
    return result

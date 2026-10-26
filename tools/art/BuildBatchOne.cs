using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEditor;using UnityEngine;
public static class BuildBatchOne {
 static Material wood,iron,cloth,amber;static List<string> paths=new List<string>(),names=new List<string>();
 static Material Mat(string n,Color color,float metal=0,float gloss=.2f){var m=new Material(Shader.Find("Standard"));m.color=color;m.SetFloat("_Metallic",metal);m.SetFloat("_Glossiness",gloss);AssetDatabase.CreateAsset(m,"Assets/Generated/"+n+".mat");return m;}
 static GameObject Part(GameObject root,string n,PrimitiveType type,Vector3 pos,Vector3 size,Material mat,Vector3 rot=default(Vector3)) {var g=GameObject.CreatePrimitive(type);g.name=n;g.transform.SetParent(root.transform,false);g.transform.localPosition=pos;g.transform.localScale=size;g.transform.localEulerAngles=rot;g.GetComponent<Renderer>().sharedMaterial=mat;UnityEngine.Object.DestroyImmediate(g.GetComponent<Collider>());return g;}
 static void Beam(GameObject root,string n,Vector3 a,Vector3 b,float thick,Material mat){var g=Part(root,n,PrimitiveType.Cube,(a+b)/2,new Vector3(thick,thick,(b-a).magnitude),mat);g.transform.localRotation=Quaternion.LookRotation(b-a);}
 static void Wheel(GameObject root,float x,float z,bool broken){
  float y=.56f,r=.52f;int count=20;
  for(int j=0;j<count;j++){if(broken&&j>9&&j<16)continue;float a=j*Mathf.PI*2/count,b=(j+1)*Mathf.PI*2/count;Vector3 v=new Vector3(x,y+Mathf.Sin(a)*r,z+Mathf.Cos(a)*r),w=new Vector3(x,y+Mathf.Sin(b)*r,z+Mathf.Cos(b)*r);Beam(root,"IronTyre",v,w,.08f,iron);Beam(root,"OakFelloe",v+new Vector3(0,-Mathf.Sin(a)*.055f,-Mathf.Cos(a)*.055f),w+new Vector3(0,-Mathf.Sin(b)*.055f,-Mathf.Cos(b)*.055f),.10f,wood);}
  for(int j=0;j<10;j++){if(broken&&j>4&&j<8)continue;float a=j*Mathf.PI*2/10;Beam(root,"Spoke",new Vector3(x,y,z),new Vector3(x,y+Mathf.Sin(a)*.46f,z+Mathf.Cos(a)*.46f),.055f,wood);}
  Part(root,"Hub",PrimitiveType.Cylinder,new Vector3(x,y,z),new Vector3(.22f,.14f,.22f),iron,new Vector3(0,0,90));
 }
 static GameObject Wagon(int stage){var r=new GameObject("delveWagon"+stage);
  for(int x=-1;x<=1;x+=2){Beam(r,"Chassis",new Vector3(x*.52f,.64f,-2.05f),new Vector3(x*.52f,.64f,2.05f),.17f,wood);}
  foreach(float z in new[]{-1.45f,1.40f}){Beam(r,"Axle",new Vector3(-.86f,.56f,z),new Vector3(.86f,.56f,z),.13f,iron);Wheel(r,-.83f,z,stage==2||(stage==1&&z>0));if(stage<2||z<0)Wheel(r,.83f,z,stage==2);}
  for(int i=0;i<12;i++){if(stage==2&&i%3!=0)continue;if(stage==1&&i==9)continue;Part(r,"DeckPlank",PrimitiveType.Cube,new Vector3(0,.77f,-1.95f+i*.35f),new Vector3(1.5f,.09f,.32f),wood);}
  if(stage<2){for(int side=-1;side<=1;side+=2){for(int j=0;j<4;j++){if(stage==1&&side>0&&j>1)continue;Part(r,"SideBoard",PrimitiveType.Cube,new Vector3(side*.75f,.91f+j*.18f,0),new Vector3(.075f,.15f,4.1f),wood);}foreach(float z in new[]{-1.95f,0,1.95f}){Part(r,"IronStrap",PrimitiveType.Cube,new Vector3(side*.80f,1.17f,z),new Vector3(.045f,.85f,.08f),iron);for(int j=0;j<3;j++)Part(r,"Rivet",PrimitiveType.Sphere,new Vector3(side*.827f,.9f+j*.28f,z),Vector3.one*.055f,iron);}}
   for(int j=0;j<(stage==0?4:2);j++)Part(r,"Tailgate",PrimitiveType.Cube,new Vector3(0,.91f+j*.18f,-2.02f),new Vector3(1.48f,.15f,.075f),wood);
  }
  if(stage==0){for(int j=0;j<3;j++){float z=-1.2f+j*1.05f;Part(r,"CargoCrate",PrimitiveType.Cube,new Vector3(j==1?.22f:-.18f,1.15f,z),new Vector3(.75f,.65f,.8f),wood);foreach(float x in new[]{-.28f,.28f})Part(r,"CrateBand",PrimitiveType.Cube,new Vector3((j==1?.22f:-.18f)+x,1.16f,z),new Vector3(.06f,.68f,.83f),iron);}Part(r,"RolledCanvas",PrimitiveType.Cylinder,new Vector3(0,1.64f,.1f),new Vector3(.33f,.65f,.33f),cloth,new Vector3(0,0,90));}
  else {for(int j=0;j<4;j++)Part(r,"BrokenPlank",PrimitiveType.Cube,new Vector3((j%2==0?.22f:-.28f),.86f+j*.035f,-.8f+j*.55f),new Vector3(.19f,.065f,stage==1?1.3f:1.0f),wood,new Vector3(3,j*31,4));}
  if(stage<2){Part(r,"DriverBench",PrimitiveType.Cube,new Vector3(0,1.28f,1.62f),new Vector3(1.45f,.12f,.42f),wood);Beam(r,"Drawbar",new Vector3(0,.66f,1.9f),new Vector3(0,.45f,2.65f),.13f,wood);}
  return r;
 }
 static void Combine(GameObject root,string id){foreach(var m in new[]{wood,iron,cloth,amber}){var renderers=root.GetComponentsInChildren<MeshRenderer>().Where(x=>x.sharedMaterial==m).ToArray();if(renderers.Length==0)continue;var mesh=new Mesh();mesh.CombineMeshes(renderers.Select(x=>new CombineInstance{mesh=x.GetComponent<MeshFilter>().sharedMesh,transform=root.transform.worldToLocalMatrix*x.transform.localToWorldMatrix}).ToArray());mesh.RecalculateBounds();AssetDatabase.CreateAsset(mesh,"Assets/Generated/"+id+"_"+m.name+".asset");foreach(var x in renderers)UnityEngine.Object.DestroyImmediate(x.gameObject);var g=new GameObject(m.name);g.transform.SetParent(root.transform,false);g.AddComponent<MeshFilter>().sharedMesh=mesh;g.AddComponent<MeshRenderer>().sharedMaterial=m;}}
 static void Save(GameObject g,string id){Combine(g,id);if(id.StartsWith("delveWagon")){g.layer=16;g.tag="T_Block";}var box=g.AddComponent<BoxCollider>();box.center=id.StartsWith("delveWagon")?new Vector3(0,.85f,.25f):new Vector3(0,.09f,0);box.size=id.StartsWith("delveWagon")?new Vector3(1.9f,1.7f,5.0f):new Vector3(.35f,.22f,.3f);string p="Assets/Generated/"+id+".prefab";PrefabUtility.SaveAsPrefabAsset(g,p);paths.Add(p);names.Add(id);}
 static void Icon(GameObject g,string file,float size,Vector3 focus){var camObj=new GameObject("IconCamera");var cam=camObj.AddComponent<Camera>();cam.orthographic=true;cam.orthographicSize=size;cam.backgroundColor=Color.clear;cam.clearFlags=CameraClearFlags.SolidColor;cam.transform.position=focus+new Vector3(6,4,7);cam.transform.LookAt(focus);cam.nearClipPlane=.01f;cam.farClipPlane=30;var rt=new RenderTexture(512,512,24,RenderTextureFormat.ARGB32);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var t=new Texture2D(512,512,TextureFormat.RGBA32,false);t.ReadPixels(new Rect(0,0,512,512),0,0);t.Apply();File.WriteAllBytes(file,t.EncodeToPNG());RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(t);UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(camObj);}
 public static void Run(){try{ var tags=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);var list=tags.FindProperty("tags");bool found=false;for(int i=0;i<list.arraySize;i++)if(list.GetArrayElementAtIndex(i).stringValue=="T_Block")found=true;if(!found){list.InsertArrayElementAtIndex(list.arraySize);list.GetArrayElementAtIndex(list.arraySize-1).stringValue="T_Block";tags.ApplyModifiedProperties();}Directory.CreateDirectory("Assets/Generated");Directory.CreateDirectory("../Bundle");Directory.CreateDirectory("../Preview");
  wood=Mat("WeatheredOak",new Color(.31f,.19f,.085f));iron=Mat("ForgedIron",new Color(.13f,.14f,.13f),.65f,.25f);cloth=Mat("Linen",new Color(.51f,.46f,.32f));amber=Mat("AmberResin",new Color(.83f,.34f,.045f),.1f,.55f);
  // Vehicle TintColor may replace the material color in-game. Bake the actual
  // wood/iron/canvas colors into albedo textures so a white tint preserves them.
  foreach(var material in new[]{wood,iron,cloth}){
   var tex=new Texture2D(256,256);var baseColor=material.color;
   for(int y=0;y<256;y++)for(int x=0;x<256;x++){
    float grain=Mathf.PerlinNoise(x*.12f,y*.008f);
    float wear=Mathf.PerlinNoise(x*.035f,y*.035f);
    float tone=material==wood?.62f+grain*.55f+wear*.15f:material==iron?.72f+wear*.38f:.85f+(((x/2+y/2)%2)==0?.12f:0);
    tex.SetPixel(x,y,new Color(baseColor.r*tone,baseColor.g*tone,baseColor.b*tone,1));
   }
   tex.Apply();AssetDatabase.CreateAsset(tex,"Assets/Generated/"+material.name+"Albedo.asset");material.mainTexture=tex;material.color=Color.white;
  }
  RenderSettings.ambientLight=new Color(.65f,.65f,.65f);var light=new GameObject("Key").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.25f;light.transform.rotation=Quaternion.Euler(45,-35,0);
  for(int stage=0;stage<3;stage++){var g=Wagon(stage);Save(g,g.name);Icon(g,"../Preview/wagon"+stage+".png",3,new Vector3(0,.8f,0));UnityEngine.Object.DestroyImmediate(g);}
  var resin=new GameObject("delveCraftingResin");for(int j=0;j<5;j++){var g=Part(resin,"ResinChunk",PrimitiveType.Cube,new Vector3((j%3-1)*.09f,.06f+(j/3)*.06f,(j/3-.5f)*.10f),new Vector3(.11f,.09f,.13f),amber,new Vector3(j*17,j*41,13));var mesh=UnityEngine.Object.Instantiate(g.GetComponent<MeshFilter>().sharedMesh);var v=mesh.vertices;for(int k=0;k<v.Length;k++){float n=Mathf.PerlinNoise(v[k].x*3+j*7+10,v[k].y*4+v[k].z*2+10);v[k]*=.65f+n*.65f;}mesh.vertices=v;mesh.RecalculateNormals();g.GetComponent<MeshFilter>().sharedMesh=mesh;}
  Save(resin,resin.name);Icon(resin,"../Preview/delveCraftingResin.png",.23f,new Vector3(0,.09f,0));UnityEngine.Object.DestroyImmediate(resin);
  AssetDatabase.SaveAssets();var b=new AssetBundleBuild{assetBundleName="batchone.unity3d",assetNames=paths.ToArray(),addressableNames=names.ToArray()};if(BuildPipeline.BuildAssetBundles("../Bundle",new[]{b},BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)==null)throw new Exception("Bundle failed");File.WriteAllText("../result.txt","PASS: three distinct wagon stages and resin; prefab meshes/materials and icons built.");EditorApplication.Exit(0);
 }catch(Exception e){Debug.LogException(e);File.WriteAllText("../result.txt","FAIL "+e);EditorApplication.Exit(1);}}
}


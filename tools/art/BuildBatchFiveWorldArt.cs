using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEditor;using UnityEngine;
public static class BuildBatchFiveWorldArt {
 static Material wood,iron,cloth,amber;static List<string> paths=new List<string>(),names=new List<string>();
 static Material Mat(string n,Color color,float metal=0,float gloss=.2f){var m=new Material(Shader.Find("Standard"));m.color=color;m.SetFloat("_Metallic",metal);m.SetFloat("_Glossiness",gloss);AssetDatabase.CreateAsset(m,"Assets/Generated/"+n+".mat");return m;}
 static GameObject Part(GameObject root,string n,PrimitiveType type,Vector3 pos,Vector3 size,Material mat,Vector3 rot=default(Vector3)) {var g=GameObject.CreatePrimitive(type);g.name=n;g.transform.SetParent(root.transform,false);g.transform.localPosition=pos;g.transform.localScale=size;g.transform.localEulerAngles=rot;g.GetComponent<Renderer>().sharedMaterial=mat;UnityEngine.Object.DestroyImmediate(g.GetComponent<Collider>());return g;}
 static void Beam(GameObject root,string n,Vector3 a,Vector3 b,float thick,Material mat){var g=Part(root,n,PrimitiveType.Cube,(a+b)/2,new Vector3(thick,thick,(b-a).magnitude),mat);g.transform.localRotation=Quaternion.LookRotation(b-a);}
 static void Crate(GameObject root,Vector3 center,Vector3 size,float angle,bool broken){var g=new GameObject("Crate");g.transform.SetParent(root.transform,false);g.transform.localPosition=center;g.transform.localEulerAngles=new Vector3(0,angle,0);
 for(int i=0;i<5;i++){float t=(i-2)*size.y/5;for(int side=-1;side<=1;side+=2){Part(g,"SidePlank",PrimitiveType.Cube,new Vector3(side*size.x*.5f,t,0),new Vector3(.035f,size.y*.18f,size.z),wood);if(!(broken&&i==3&&side==1))Part(g,"EndPlank",PrimitiveType.Cube,new Vector3(0,t,side*size.z*.5f),new Vector3(size.x,size.y*.18f,.035f),wood);}}
 for(int i=0;i<5;i++){if(broken&&i==2)continue;Part(g,"Lid",PrimitiveType.Cube,new Vector3((i-2)*size.x/5,size.y*.5f,0),new Vector3(size.x*.18f,.035f,size.z),wood);}
 for(int side=-1;side<=1;side+=2){foreach(float x in new[]{-.36f,.36f})Part(g,"Batten",PrimitiveType.Cube,new Vector3(x*size.x,0,side*(size.z*.5f+.025f)),new Vector3(.065f,size.y+.04f,.035f),wood);Beam(g,"DiagonalBrace",new Vector3(-size.x*.40f,-size.y*.39f,side*(size.z*.5f+.05f)),new Vector3(size.x*.40f,size.y*.39f,side*(size.z*.5f+.05f)),.045f,wood);}
 }
 static GameObject Stack(bool scattered){var g=new GameObject(scattered?"delveCrateStackScattered":"delveCrateStack");Crate(g,new Vector3(0,.27f,0),new Vector3(.78f,.5f,1.0f),0,scattered);if(!scattered)Crate(g,new Vector3(.025f,.83f,-.06f),new Vector3(.65f,.55f,.76f),7,false);else Part(g,"LooseBoard",PrimitiveType.Cube,new Vector3(.1f,.57f,0),new Vector3(.64f,.04f,.11f),wood,new Vector3(0,19,0));return g;}
 static void Combine(GameObject root,string id){foreach(var m in new[]{wood,iron,cloth,amber}){var renderers=root.GetComponentsInChildren<MeshRenderer>().Where(x=>x.sharedMaterial==m).ToArray();if(renderers.Length==0)continue;var mesh=new Mesh();mesh.CombineMeshes(renderers.Select(x=>new CombineInstance{mesh=x.GetComponent<MeshFilter>().sharedMesh,transform=root.transform.worldToLocalMatrix*x.transform.localToWorldMatrix}).ToArray());mesh.RecalculateBounds();AssetDatabase.CreateAsset(mesh,"Assets/Generated/"+id+"_"+m.name+".asset");foreach(var x in renderers)UnityEngine.Object.DestroyImmediate(x.gameObject);var g=new GameObject(m.name);g.transform.SetParent(root.transform,false);g.AddComponent<MeshFilter>().sharedMesh=mesh;g.AddComponent<MeshRenderer>().sharedMaterial=m;}}
 static void Icon(GameObject g,string file,float size,Vector3 focus){var camObj=new GameObject("IconCamera");var cam=camObj.AddComponent<Camera>();cam.orthographic=true;cam.orthographicSize=size;cam.backgroundColor=Color.clear;cam.clearFlags=CameraClearFlags.SolidColor;cam.transform.position=focus+new Vector3(6,4,7);cam.transform.LookAt(focus);cam.nearClipPlane=.01f;cam.farClipPlane=30;var rt=new RenderTexture(512,512,24,RenderTextureFormat.ARGB32);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var t=new Texture2D(512,512,TextureFormat.RGBA32,false);t.ReadPixels(new Rect(0,0,512,512),0,0);t.Apply();File.WriteAllBytes(file,t.EncodeToPNG());RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(t);UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(camObj);}
 static GameObject Chest(bool unused){var g=new GameObject("delveIronboundCrate");g.tag="T_Block";
 // All boards and straps fit within exactly one voxel, including the collider.
 for(int i=0;i<6;i++){float h=(i+.5f)/6;
  for(int side=-1;side<=1;side+=2){
   Part(g,"SidePlank",PrimitiveType.Cube,new Vector3(side*.475f,h,0),new Vector3(.04f,.162f,.95f),wood);
   Part(g,"EndPlank",PrimitiveType.Cube,new Vector3(0,h,side*.475f),new Vector3(.95f,.162f,.04f),wood);
  }
  for(int side=-1;side<=1;side+=2)Part(g,"TopBottom",PrimitiveType.Cube,new Vector3((i-2.5f)/6,.5f+side*.48f,0),new Vector3(.162f,.04f,.96f),wood);
 }
 foreach(float a in new[]{-.35f,.35f})for(int side=-1;side<=1;side+=2){
  Part(g,"EndBand",PrimitiveType.Cube,new Vector3(a,.5f,side*.49f),new Vector3(.055f,1,.02f),iron);
  Part(g,"SideBand",PrimitiveType.Cube,new Vector3(side*.49f,.5f,a),new Vector3(.02f,1,.055f),iron);
  Part(g,"TopBand",PrimitiveType.Cube,new Vector3(a,.99f,0),new Vector3(.055f,.02f,1),iron);
 }
 return g;
 }
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
  for(int variant=0;variant<1;variant++){var g=Chest(variant==1);Combine(g,g.name);var c=g.AddComponent<BoxCollider>();c.center=new Vector3(0,.5f,0);c.size=Vector3.one;string p="Assets/Generated/"+g.name+".prefab";PrefabUtility.SaveAsPrefabAsset(g,p);paths.Add(p);names.Add(g.name);Icon(g,"../Preview/"+g.name+".png",.85f,new Vector3(0,.5f,0));UnityEngine.Object.DestroyImmediate(g);}
  AssetDatabase.SaveAssets();var b=new AssetBundleBuild{assetBundleName="batchfiveworld.unity3d",assetNames=paths.ToArray(),addressableNames=names.ToArray()};if(BuildPipeline.BuildAssetBundles("../Bundle",new[]{b},BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)==null)throw new Exception("Bundle failed");File.WriteAllText("../result.txt","PASS full one-metre ironbound supply crate mesh, collider and icon");EditorApplication.Exit(0);
 }catch(Exception e){Debug.LogException(e);File.WriteAllText("../result.txt","FAIL "+e);EditorApplication.Exit(1);}}
}


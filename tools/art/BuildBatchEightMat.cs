using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;
public static class BuildBatchEightMat {
 static Material Make(string name,Color color){var m=new Material(Shader.Find("Standard"));var tex=new Texture2D(64,64,TextureFormat.RGBA32,false);for(int y=0;y<64;y++)for(int x=0;x<64;x++){float tone=.83f+.2f*Mathf.PerlinNoise(x*.5f,y*.06f);tex.SetPixel(x,y,new Color(color.r*tone,color.g*tone,color.b*tone,1));}tex.Apply();AssetDatabase.CreateAsset(tex,"Assets/Generated/"+name+"Albedo.asset");m.mainTexture=tex;m.color=Color.white;m.SetFloat("_Glossiness",.08f);AssetDatabase.CreateAsset(m,"Assets/Generated/"+name+".mat");return m;}
 static void Part(GameObject root,Vector3 p,Vector3 s,Material m){var g=GameObject.CreatePrimitive(PrimitiveType.Cube);g.transform.SetParent(root.transform,false);g.transform.localPosition=p;g.transform.localScale=s;g.GetComponent<Renderer>().sharedMaterial=m;UnityEngine.Object.DestroyImmediate(g.GetComponent<Collider>());}
 public static void Run(){try{
  Directory.CreateDirectory("Assets/Generated");Directory.CreateDirectory("../Bundle");Directory.CreateDirectory("../Preview");
  var tags=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);var list=tags.FindProperty("tags");bool found=false;for(int i=0;i<list.arraySize;i++)if(list.GetArrayElementAtIndex(i).stringValue=="T_Block")found=true;if(!found){list.InsertArrayElementAtIndex(list.arraySize);list.GetArrayElementAtIndex(list.arraySize-1).stringValue="T_Block";tags.ApplyModifiedProperties();}
  var straw=Make("WovenRush",new Color(.57f,.40f,.20f));var cross=Make("CrossRush",new Color(.41f,.29f,.13f));var binding=Make("FiberBinding",new Color(.29f,.20f,.09f));var root=new GameObject("delveFieldCraftingMat");root.tag="T_Block";
  for(int x=0;x<20;x++)for(int z=0;z<20;z++){
   float px=(x-9.5f)*.045f,pz=(z-9.5f)*.045f;bool over=(x+z)%2==0;
   Part(root,new Vector3(px,over?.028f:.016f,pz),new Vector3(.038f,.012f,.046f),straw);
   Part(root,new Vector3(px,over?.016f:.028f,pz),new Vector3(.046f,.012f,.038f),cross);
  }
  for(int s=-1;s<=1;s+=2){Part(root,new Vector3(s*.46f,.022f,0),new Vector3(.025f,.032f,.95f),binding);Part(root,new Vector3(0,.022f,s*.46f),new Vector3(.95f,.032f,.025f),binding);}
  foreach(var mat in new[]{straw,cross,binding}){var rs=root.GetComponentsInChildren<MeshRenderer>().Where(r=>r.sharedMaterial==mat).ToArray();var mesh=new Mesh();mesh.CombineMeshes(rs.Select(r=>new CombineInstance{mesh=r.GetComponent<MeshFilter>().sharedMesh,transform=r.transform.localToWorldMatrix}).ToArray());AssetDatabase.CreateAsset(mesh,"Assets/Generated/"+mat.name+".asset");foreach(var r in rs)UnityEngine.Object.DestroyImmediate(r.gameObject);var g=new GameObject(mat.name);g.transform.SetParent(root.transform,false);g.AddComponent<MeshFilter>().sharedMesh=mesh;g.AddComponent<MeshRenderer>().sharedMaterial=mat;}
  var col=root.AddComponent<BoxCollider>();col.center=new Vector3(0,.026f,0);col.size=new Vector3(.98f,.052f,.98f);
  string path="Assets/Generated/delveFieldCraftingMat.prefab";PrefabUtility.SaveAsPrefabAsset(root,path);AssetDatabase.SaveAssets();
  RenderSettings.ambientLight=new Color(.65f,.65f,.65f);var light=new GameObject("Key").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.2f;light.transform.rotation=Quaternion.Euler(45,-35,0);
  var cam=new GameObject("Camera").AddComponent<Camera>();cam.orthographic=true;cam.orthographicSize=.71f;cam.backgroundColor=Color.clear;cam.clearFlags=CameraClearFlags.SolidColor;cam.transform.position=new Vector3(1.6f,2.6f,1.8f);cam.transform.LookAt(new Vector3(0,.02f,0));var rt=new RenderTexture(512,512,24);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var image=new Texture2D(512,512,TextureFormat.RGBA32,false);image.ReadPixels(new Rect(0,0,512,512),0,0);image.Apply();File.WriteAllBytes("../Preview/delveFieldCraftingMat.png",image.EncodeToPNG());
  var build=new AssetBundleBuild{assetBundleName="fieldmatbatch08.unity3d",assetNames=new[]{path},addressableNames=new[]{"delveFieldCraftingMat"}};if(BuildPipeline.BuildAssetBundles("../Bundle",new[]{build},BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)==null)throw new Exception("Bundle failed");
  File.WriteAllText("../result.txt","PASS woven 0.95m mat; 0.98m interaction collider; three combined meshes; no tool sockets");EditorApplication.Exit(0);
 }catch(Exception e){Debug.LogException(e);File.WriteAllText("../result.txt","FAIL "+e);EditorApplication.Exit(1);}}
}

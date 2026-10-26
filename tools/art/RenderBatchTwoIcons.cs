using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;
public static class RenderBatchTwoIcons {
 [Serializable] public class Spec {public string id,bundle,asset;}
 [Serializable] public class Input {public Spec[] icons;public string output;}
 public static void Run(){try{
  var input=JsonUtility.FromJson<Input>(File.ReadAllText("Assets/icon-input.json"));Directory.CreateDirectory(input.output);
  RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.65f,.65f,.65f);
  var light=new GameObject("IconLight").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.2f;light.transform.rotation=Quaternion.Euler(35,205,0);
  foreach(var batch in input.icons.GroupBy(x=>x.bundle)){
   var bundle=AssetBundle.LoadFromFile(batch.Key);if(bundle==null)throw new Exception("Bundle "+batch.Key);
   foreach(var spec in batch){
    var asset=bundle.LoadAsset<GameObject>(spec.asset);if(asset==null)throw new Exception("Asset "+spec.asset);
    var instance=UnityEngine.Object.Instantiate(asset);foreach(var a in instance.GetComponentsInChildren<Animator>())a.enabled=false;
    foreach(var lod in instance.GetComponentsInChildren<LODGroup>())lod.enabled=false;
    foreach(var r in instance.GetComponentsInChildren<Renderer>())if(r.name.Contains("LOD1")||r.name.Contains("LOD2"))r.enabled=false;
    if(spec.id.EndsWith("Gloves"))foreach(var skin in instance.GetComponentsInChildren<SkinnedMeshRenderer>()){
     if(!skin.enabled)continue;var mesh=new Mesh();skin.BakeMesh(mesh);var vertices=mesh.vertices;
     for(int i=0;i<vertices.Length;i++){var v=skin.transform.TransformPoint(vertices[i]);v.x-=Mathf.Sign(v.x)*.34f;vertices[i]=instance.transform.InverseTransformPoint(v);}mesh.vertices=vertices;mesh.RecalculateBounds();mesh.RecalculateNormals();
     var compact=new GameObject("CompactGloves");compact.transform.SetParent(instance.transform,false);compact.AddComponent<MeshFilter>().sharedMesh=mesh;compact.AddComponent<MeshRenderer>().sharedMaterials=skin.sharedMaterials;skin.enabled=false;
    }
    Bounds bounds=new Bounds();bool first=true;
    foreach(var r in instance.GetComponentsInChildren<Renderer>()){
     if(!r.enabled)continue;var skin=r as SkinnedMeshRenderer;Bounds b=r.bounds;
     if(skin!=null){var mesh=new Mesh();skin.BakeMesh(mesh);b=new Bounds(skin.transform.TransformPoint(mesh.vertices[0]),Vector3.zero);foreach(var v in mesh.vertices)b.Encapsulate(skin.transform.TransformPoint(v));UnityEngine.Object.DestroyImmediate(mesh);}
     if(first){bounds=b;first=false;}else bounds.Encapsulate(b);
    }
    if(first||bounds.size.magnitude<.001f)throw new Exception("No visible geometry "+spec.id);
    var camera=new GameObject("IconCamera").AddComponent<Camera>();camera.orthographic=true;camera.backgroundColor=Color.clear;camera.clearFlags=CameraClearFlags.SolidColor;
    var direction=spec.id.StartsWith("armor")?new Vector3(.25f,.08f,1):new Vector3(.65f,.4f,1);
    camera.transform.position=bounds.center+direction.normalized*10;camera.transform.LookAt(bounds.center);
    float extent=0;foreach(float x in new[]{-1f,1f})foreach(float y in new[]{-1f,1f})foreach(float z in new[]{-1f,1f}){var q=camera.transform.InverseTransformPoint(bounds.center+Vector3.Scale(bounds.extents,new Vector3(x,y,z)));extent=Mathf.Max(extent,Mathf.Abs(q.x),Mathf.Abs(q.y));}
    camera.orthographicSize=extent*1.10f;camera.nearClipPlane=.01f;camera.farClipPlane=40;
    var rt=new RenderTexture(512,512,24,RenderTextureFormat.ARGB32);camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;
    var tex=new Texture2D(512,512,TextureFormat.RGBA32,false);tex.ReadPixels(new Rect(0,0,512,512),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(input.output,spec.id+".png"),tex.EncodeToPNG());RenderTexture.active=null;
    UnityEngine.Object.DestroyImmediate(tex);UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(camera.gameObject);UnityEngine.Object.DestroyImmediate(instance);
   }bundle.Unload(true);
  }File.WriteAllText("../icons-result.txt","PASS "+input.icons.Length+" original model icons");EditorApplication.Exit(0);
 }catch(Exception e){File.WriteAllText("../icons-result.txt","FAIL "+e);Debug.LogException(e);EditorApplication.Exit(1);}}
}

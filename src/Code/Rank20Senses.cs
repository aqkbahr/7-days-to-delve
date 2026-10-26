using System;using System.Collections.Generic;using HarmonyLib;using UnityEngine;
namespace Delve {
 [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
 public static class AttachRank20Senses {static void Postfix(EntityPlayerLocal __instance){if(CharacterProgression.IsLocal(__instance)&&SystemInfo.graphicsDeviceType!=UnityEngine.Rendering.GraphicsDeviceType.Null&&__instance.GetComponent<Rank20Senses>()==null)__instance.gameObject.AddComponent<Rank20Senses>();}}
 public class Rank20Senses:MonoBehaviour {
  sealed class Marker {public LineRenderer Line;public Vector3i Position;public bool Ore;}
  static List<Vector3i> offsets;
  readonly List<Marker> markers=new List<Marker>();EntityPlayerLocal player;Material material;Vector3i center;Vector3 lastOrigin;int cursor;float crouchSince=-1,nextVisibility,nextScan;bool scanning;
  public static bool Wild(string name){switch(name){case "plantedDelveBramble3Harvest":case "plantedDelveYarrow3Harvest":case "plantedDelveThyme3Harvest":case "plantedDelveMooncap3Harvest":case "plantedCorn3Harvest":case "plantedPotato3Harvest":case "plantedPumpkin3Harvest":case "plantedMushroom3Harvest":case "plantedBlueberry3Harvest":case "plantedGoldenrod3Harvest":case "plantedChrysanthemum3Harvest":return true;default:return false;}}
  void Start(){player=GetComponent<EntityPlayerLocal>();if(offsets==null){offsets=new List<Vector3i>();for(int x=-15;x<=15;x++)for(int y=-15;y<=15;y++)for(int z=-15;z<=15;z++)if(x*x+y*y+z*z<=225)offsets.Add(new Vector3i(x,y,z));offsets.Sort((a,b)=>(a.x*a.x+a.y*a.y+a.z*a.z).CompareTo(b.x*b.x+b.y*b.y+b.z*b.z));}}
  bool Visible(Vector3i pos){Vector3 aim=new Vector3(pos.x+.5f,pos.y+.5f,pos.z+.5f);var eye=player.GetLookRay().origin;RaycastHit hit;if(!Physics.Linecast(eye-Origin.position,aim-Origin.position,out hit,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))return true;Vector3 impact=hit.point+Origin.position;return impact.x>=pos.x-.02f&&impact.x<=pos.x+1.02f&&impact.y>=pos.y-.02f&&impact.y<=pos.y+1.02f&&impact.z>=pos.z-.02f&&impact.z<=pos.z+1.02f;}
  void Hide(){foreach(var m in markers)m.Line.enabled=false;}
  int FreeMarker(){for(int i=0;i<markers.Count;i++)if(!markers[i].Line.enabled)return i;return markers.Count;}
  void Update(){
   if(player==null||offsets==null)return;bool gather=Rank20.Has(player,"Farming","GatherersEye"),ore=Rank20.Has(player,"Mining","OreSense");
   if(lastOrigin!=Origin.position){lastOrigin=Origin.position;for(int i=0;i<markers.Count;i++)if(markers[i].Line.enabled)Show(i,markers[i].Position,markers[i].Ore);}
   if(player.IsDead()||!player.IsCrouching||(!gather&&!ore)){crouchSince=-1;scanning=false;Hide();return;}
   if(crouchSince<0)crouchSince=Time.time;ore&=Time.time-crouchSince>=2;
   var pos=new Vector3i((int)Math.Floor(player.position.x),(int)Math.Floor(player.position.y),(int)Math.Floor(player.position.z));
   if(!scanning&&(Time.time>=nextScan||pos!=center)){center=pos;cursor=0;scanning=true;Hide();}
   if(scanning){int used=0;foreach(var m in markers)if(m.Line.enabled)used++;int end=Math.Min(offsets.Count,cursor+128);
    for(;cursor<end;cursor++){var d=offsets[cursor];bool near=d.x*d.x+d.y*d.y+d.z*d.z<=144;if(!ore&&(!gather||!near))continue;var p=center+d;var block=player.world.GetBlock(p);if(block.isair)continue;string name=block.Block.GetBlockName();bool mineral=ore&&name.StartsWith("terrOre",StringComparison.Ordinal);if(!mineral&&!(gather&&near&&Wild(name)))continue;if(used>=16||!Visible(p))continue;Show(FreeMarker(),p,mineral);used++;}
    if(cursor>=offsets.Count){scanning=false;nextScan=Time.time+1;}
   }
   if(Time.time>=nextVisibility){nextVisibility=Time.time+.1f;foreach(var m in markers)if(m.Line.enabled){Vector3 target=new Vector3(m.Position.x+.5f,m.Position.y+.5f,m.Position.z+.5f);var block=player.world.GetBlock(m.Position);bool eligible=!block.isair&&(m.Ore?ore&&block.Block.GetBlockName().StartsWith("terrOre",StringComparison.Ordinal):gather&&Wild(block.Block.GetBlockName()));if(!eligible||(target-player.GetLookRay().origin).sqrMagnitude>(m.Ore?225:144)||!Visible(m.Position))m.Line.enabled=false;}}
  }
  void Show(int index,Vector3i pos,bool ore){
   if(material==null){var shader=Shader.Find("Sprites/Default");if(shader==null)return;material=new Material(shader);}
   if(index>=markers.Count){var go=new GameObject("DelveVisibleResourceOutline");var line=go.AddComponent<LineRenderer>();line.sharedMaterial=material;line.useWorldSpace=true;line.startWidth=line.endWidth=.018f;line.positionCount=16;line.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;line.receiveShadows=false;markers.Add(new Marker{Line=line});}
   var m=markers[index];m.Position=pos;m.Ore=ore;m.Line.startColor=m.Line.endColor=ore?new Color(.3f,.8f,1,.65f):new Color(.5f,1,.35f,.65f);
   Vector3 corner=new Vector3(pos.x,pos.y,pos.z)-Origin.position;Vector3[] vertices={new Vector3(0,0,0),new Vector3(1,0,0),new Vector3(1,0,1),new Vector3(0,0,1),new Vector3(0,0,0),new Vector3(0,1,0),new Vector3(1,1,0),new Vector3(1,0,0),new Vector3(1,1,0),new Vector3(1,1,1),new Vector3(1,0,1),new Vector3(1,1,1),new Vector3(0,1,1),new Vector3(0,0,1),new Vector3(0,1,1),new Vector3(0,1,0)};for(int i=0;i<vertices.Length;i++)vertices[i]+=corner;m.Line.SetPositions(vertices);m.Line.enabled=true;
  }
  void OnDestroy(){foreach(var m in markers)if(m.Line!=null)Destroy(m.Line.gameObject);if(material!=null)Destroy(material);}
 }
}

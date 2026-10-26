using System;using System.Collections.Generic;using UnityEngine;
namespace DelvePresentation {
 // Shared by the staged game assembly and the isolated Unity acceptance tests.
 public sealed class NativeBodyFoundation:IDisposable {
  public const string Marker="DelveNativeBodyFoundation_v1";
  sealed class State {public Renderer Renderer;public Material[] Original,Owned;}
  readonly List<State> states=new List<State>();
  public int TintedMaterials {get;private set;}
  public static bool Enabled(GameObject visual){return visual!=null&&visual.transform.Find(Marker)!=null;}
  public static Color Palette(string id){switch(id){
   case "delveCorruptedWalker":return new Color(.82f,.95f,.78f);
   case "delveImp":return new Color(.96f,.74f,.62f);
   case "delvePossessedSoldier":return new Color(.82f,.90f,.83f);
   case "delveDemonSpawn":return new Color(.82f,.68f,.69f);
   case "delveWarpedBrute":return new Color(.91f,.88f,.80f);
   case "delveAshboundWarden":return new Color(.78f,.80f,.83f);
   case "delveHellhound":return new Color(.75f,.62f,.58f);
   case "delveGloomcat":return new Color(.65f,.62f,.78f);
   case "delveCrystalStag":return new Color(.83f,.94f,.94f);
   case "delveThornbackBoar":return new Color(.86f,.82f,.69f);
   default:return Color.white;
  }}
  public void Apply(Renderer[] renderers,string id){
   Dispose();Color tint=Palette(id);
   foreach(var renderer in renderers){if(renderer==null)continue;var originals=renderer.sharedMaterials;var owned=(Material[])originals.Clone();bool changed=false;
    for(int i=0;i<originals.Length;i++){
     var source=originals[i];if(source==null)continue;
     // Never replace a game's custom shader or infer its packed-mask channels.
     string property=source.HasProperty("_BaseColor")?"_BaseColor":source.HasProperty("_Color")?"_Color":null;
     if(property==null)continue;var value=source.GetColor(property);var copy=new Material(source);copy.name=source.name+"_DelveNativeTint";copy.SetColor(property,new Color(value.r*tint.r,value.g*tint.g,value.b*tint.b,value.a));owned[i]=copy;changed=true;TintedMaterials++;
    }
    if(changed){renderer.sharedMaterials=owned;states.Add(new State{Renderer=renderer,Original=originals,Owned=owned});}
   }
  }
  public void Dispose(){
   foreach(var s in states){if(s.Renderer!=null)s.Renderer.sharedMaterials=s.Original;for(int i=0;i<s.Owned.Length;i++)if(s.Owned[i]!=s.Original[i]){if(Application.isPlaying)UnityEngine.Object.Destroy(s.Owned[i]);else UnityEngine.Object.DestroyImmediate(s.Owned[i]);}}
   states.Clear();TintedMaterials=0;
  }
 }
}

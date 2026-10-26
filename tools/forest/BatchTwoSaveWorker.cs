using System;using System.IO;using System.Xml;using System.Text;using System.Reflection;using System.Collections.Generic;using UnityEngine;
// Offline migration on a disposable copy only. All changes are exact-match and journalled.
public static class BatchTwoSaveWorker {
 static Dictionary<string,Chunk> chunks;static HashSet<Chunk> dirty;static StringBuilder log;static string folder;
 static Chunk At(int x,int z){Chunk c;chunks.TryGetValue((x>>4)+","+(z>>4),out c);return c;}
 static sbyte Density(float h,int y){float h2=h+.5f;int top=(int)h2;sbyte d=y<top?(sbyte)-128:y>top+1?(sbyte)127:y==top?(sbyte)(-128*(h2-top)):(sbyte)(127*(1-(h2-top)));return d==0?(y<=top?(sbyte)-1:(sbyte)1):d;}
 static string Storage(Chunk c){var s=new StringBuilder();foreach(var te in c.GetTileEntities().list){var t=te as TileEntityComposite;var st=t==null?null:t.GetFeature<TEFeatureStorage>();if(st==null)continue;s.Append(te.localChunkPos+":"+st.lootListName+":");foreach(var item in st.ItemGrid.CloneItems())s.Append(item.itemValue.type+"/"+item.count+"/"+item.itemValue.Quality+",");s.AppendLine();}return s.ToString();}
 public static string Run(string mode){
  bool apply=mode=="apply";folder=ModManager.GetMod("BatchTwoSaveTools",true).Path;
  if(!GameIO.GetUserGameDataDir().Replace('\\','/').EndsWith("/BatchTwoSave"))throw new Exception("Disposable BatchTwoSave profile required");
  var world=GameManager.Instance.World;if(world.GetPlayers().Count!=0)throw new Exception("No players allowed during offline migration");
  var manager=(RegionFileManager)typeof(ChunkProviderGenerateWorld).GetField("m_RegionFileManager",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance).GetValue(world.ChunkCache.ChunkProvider);
  chunks=new Dictionary<string,Chunk>();dirty=new HashSet<Chunk>();log=new StringBuilder();var before=new Dictionary<Chunk,string>();
  foreach(long key in manager.GetAllChunkKeys()){var c=manager.GetChunkSync(key);if(c==null)throw new Exception("Unreadable chunk");chunks[c.X+","+c.Z]=c;before[c]=Storage(c);}
  int changed=0,skipped=0,already=0;
  using(var r=new BinaryReader(File.OpenRead(Path.Combine(folder,"columns.bin"))))while(r.BaseStream.Position<r.BaseStream.Length){int x=r.ReadInt32(),z=r.ReadInt32();float old=r.ReadUInt16()/257f,next=r.ReadUInt16()/257f;var c=At(x,z);if(c==null)continue;int lx=x&15,lz=z&15,ot=(int)(old+.5f),nt=(int)(next+.5f);bool valid=true,done=true;
   for(int y=nt-2;y<=ot+3;y++){var b=c.GetBlock(lx,y,lz);sbyte d=c.GetDensity(lx,y,lz);if(d!=Density(old,y))valid=false;if(d!=Density(next,y))done=false;if(!b.isair&&!b.isTerrain&&!(b.Block.IsTerrainDecoration&&!b.ischild&&!b.Block.isMultiBlock&&b.damage==0))valid=false;if(c.GetTileEntity(new Vector3i(lx,y,lz))!=null)valid=false;}
   if(done){already++;continue;}if(!valid){skipped++;log.AppendLine("SKIP modified terrain "+x+","+z);continue;}
   var top=c.GetBlock(lx,ot,lz);if(!top.isTerrain){skipped++;continue;}var decor=c.GetBlock(lx,ot+1,lz);if(!decor.isair&&(!decor.Block.IsTerrainDecoration||decor.Block.isMultiBlock)){skipped++;continue;}
   changed++;if(!apply)continue;
   for(int y=nt-2;y<=ot+3;y++){if(y==nt)c.SetBlockRaw(lx,y,lz,top);else if(y==nt+1)c.SetBlockRaw(lx,y,lz,decor);else if(y>nt+1)c.SetBlockRaw(lx,y,lz,BlockValue.Air);c.SetDensity(lx,y,lz,Density(next,y));}c.SetTerrainHeight(lx,lz,(byte)nt);dirty.Add(c);
  }
  log.AppendLine("TERRAIN eligible="+changed+" preserved_modified="+skipped+" already="+already);
  // Every existing storage entity and item remains byte-for-byte owned by its original object.
  foreach(var pair in before)if(Storage(pair.Key)!=pair.Value)throw new Exception("Terrain altered storage "+pair.Key.X+","+pair.Key.Z);
  int eligible=0,restored=0,protectedCells=0;var doc=new XmlDocument();doc.Load(Path.Combine(folder,"cells.xml"));var prefabs=new Dictionary<string,Prefab>();
  foreach(XmlElement e in doc.SelectNodes("/repairs/cell")){int x=int.Parse(e.GetAttribute("x")),y=int.Parse(e.GetAttribute("y")),z=int.Parse(e.GetAttribute("z"));var c=At(x,z);if(c==null)continue;var current=c.GetBlock(x&15,y,z&15);string old=e.GetAttribute("before"),target=e.GetAttribute("after");if(current.Block.GetBlockName()==target)continue;if(current.Block.GetBlockName()!=old||current.damage!=0){protectedCells++;continue;}
   string name=e.GetAttribute("prefab");Prefab p;if(!prefabs.TryGetValue(name,out p)){p=new Prefab();if(!p.Load(name,true,true,false,false))throw new Exception("Missing prefab "+name);prefabs[name]=p;}int px=int.Parse(e.GetAttribute("lx")),py=int.Parse(e.GetAttribute("ly")),pz=int.Parse(e.GetAttribute("lz"));var value=p.GetBlock(px,py,pz);if(value.Block.GetBlockName()!=target)throw new Exception("Candidate mismatch "+name);
   // Use prefab's already-rotated child cells, refusing overlaps with saved structures.
   var changes=new List<KeyValuePair<Vector3i,BlockValue>>();changes.Add(new KeyValuePair<Vector3i,BlockValue>(new Vector3i(x,y,z),value));bool safe=true;
   if(value.Block.isMultiBlock)for(int dz=-5;dz<=5;dz++)for(int dy=-2;dy<=5;dy++)for(int dx=-5;dx<=5;dx++){int a=px+dx,b=py+dy,d=pz+dz;if(a<0||b<0||d<0||a>=p.size.x||b>=p.size.y||d>=p.size.z)continue;var child=p.GetBlock(a,b,d);if(!child.ischild)continue;var parent=child.Block.multiBlockPos.GetParentPos(new Vector3i(a,b,d),child);if(parent!=new Vector3i(px,py,pz))continue;var cc=At(x+dx,z+dz);if(cc==null||!cc.GetBlock((x+dx)&15,y+dy,(z+dz)&15).isair){safe=false;break;}changes.Add(new KeyValuePair<Vector3i,BlockValue>(new Vector3i(x+dx,y+dy,z+dz),child));}
   if(!safe){protectedCells++;continue;}eligible++;if(!apply)continue;var te=c.GetTileEntity(new Vector3i(x&15,y,z&15));foreach(var change in changes){var pos=change.Key;var cc=At(pos.x,pos.z);cc.SetBlockRaw(pos.x&15,pos.y,pos.z&15,change.Value);dirty.Add(cc);}
   if(te==null){var composite=new TileEntityComposite(c,value);composite.localChunkPos=new Vector3i(x&15,y,z&15);c.AddTileEntity(composite);restored++;}else if(!(te is TileEntityComposite))throw new Exception("Unexpected legacy storage "+te.GetType());else {var expected=new TileEntityComposite(c,value);var st=((TileEntityComposite)te).GetFeature<TEFeatureStorage>();var intended=expected.GetFeature<TEFeatureStorage>();if(st==null||intended==null)throw new Exception("Missing storage feature");st.lootListName=intended.lootListName;}
   log.AppendLine("CONTAINER "+x+","+y+","+z+" "+old+" -> "+target+" existingTE="+(te!=null));
  }
  log.AppendLine("CONTAINERS eligible="+eligible+" new_storage="+restored+" preserved_modified="+protectedCells);
  doc.Load(Path.Combine(folder,"gardens.xml"));int gardens=0;
  foreach(XmlElement e in doc.SelectNodes("/gardens/cell")){int x=int.Parse(e.GetAttribute("x")),y=int.Parse(e.GetAttribute("y")),z=int.Parse(e.GetAttribute("z"));var c=At(x,z);if(c==null)continue;int lx=x&15,lz=z&15;if(c.GetBlock(lx,y,lz).Block.GetBlockName()!="delveFarmPlotPlate")continue;
   var crop=c.GetBlock(lx,y+1,lz);if(!crop.isair&&!crop.Block.GetBlockName().StartsWith("planted")){log.AppendLine("SKIP modified garden "+x+","+z);continue;}bool safe=true;for(int yy=y+2;yy<=y+4;yy++){var b=c.GetBlock(lx,yy,lz);if(!b.isair&&!b.ischild)safe=false;}if(!safe)continue;
   var p=new Prefab();if(!p.Load(e.GetAttribute("prefab"),true,true,false,false))throw new Exception("Garden base missing");int px=int.Parse(e.GetAttribute("lx")),py=int.Parse(e.GetAttribute("ly")),pz=int.Parse(e.GetAttribute("lz"));var ground=p.GetBlock(px,py,pz);if(ground.Block.GetBlockName()=="terrainFiller")ground=Block.GetBlockValue("terrForestGround",false);if(!ground.isTerrain)throw new Exception("Garden ground not terrain");gardens++;if(!apply)continue;
   // Move the existing root/children, never regenerate harvested crops.
   for(int yy=y+4;yy>=y+2;yy--)c.SetBlockRaw(lx,yy,lz,c.GetBlock(lx,yy-1,lz));var plate=Block.GetBlockValue("delveFarmPlotPlate",false);plate.rotation=0;c.SetBlockRaw(lx,y+1,lz,plate);c.SetDensity(lx,y+1,lz,127);c.SetBlockRaw(lx,y,lz,ground);c.SetDensity(lx,y,lz,p.GetDensity(px,py,pz));dirty.Add(c);
  }log.AppendLine("GARDENS eligible="+gardens);
  if(apply){foreach(var c in dirty){c.RecalcHeights();c.isModified=true;c.NeedsRegeneration=true;manager.SaveChunkSnapshot(c,true);}manager.WaitSaveDone();}
  log.AppendLine("PASS "+mode+" chunks="+chunks.Count+" modified="+dirty.Count);File.WriteAllText(Path.Combine(folder,"migration-"+mode+".txt"),log.ToString());return "[BatchTwoSave] "+log.ToString();
 }
}

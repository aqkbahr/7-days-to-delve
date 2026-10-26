using System.Collections.Generic; namespace DelveBatchEleven { public class Exchange {public string Title,Skill;public int Rank;public Exchange(string t,string s,int r){Title=t;Skill=s;Rank=r;}} public static class Exchanges {public static readonly Dictionary<string,Exchange> Rows=new Dictionary<string,Exchange>{
{"casinocoin|delvefarmdispatch|60|foodcropcorn=6,foodcroppotato=4",new Exchange("Supply Order: Wayrest Pantry","Farming",1)},
{"casinocoin|delvefarmdispatch|90|delvedriedthyme=2,delvedriedyarrow=3",new Exchange("Supply Order: Infirmary: Dried Herbs","Alchemy",10)},
{"casinocoin|delvefarmdispatch|140|fooddelvetravelbread=4",new Exchange("Supply Order: Guard: Bread Supply","Cooking",10)},
{"casinocoin|delvefarmdispatch|180|medicaldelveyarrowtincture=3",new Exchange("Supply Order: Infirmary: Tinctures","Alchemy",20)},
{"casinocoin|delvefarmdispatch|240|fooddelvetrailration=4",new Exchange("Supply Order: Expedition: Rations","Cooking",20)},
{"resourceforgediron|delvefarmdispatch|4|foodbakedpotato=6",new Exchange("Supply Order: Smithy: Potato Supper","Cooking",1)},
{"resourceleather|delvefarmdispatch|6|foodcornbread=4",new Exchange("Supply Order: Outfitters: Corn Bread","Cooking",1)},
{"casinocoin|delvefarmdispatch|60|delvefarmparcelpantry=1",new Exchange("Redeem legacy parcel: Pantry","Farming",1)},
{"casinocoin|delvefarmdispatch|90|delvefarmparcelherbs=1",new Exchange("Redeem legacy parcel: Herbs","Farming",1)},
{"casinocoin|delvefarmdispatch|140|delvefarmparcelbread=1",new Exchange("Redeem legacy parcel: Bread","Farming",1)},
{"casinocoin|delvefarmdispatch|180|delvefarmparcelmedicine=1",new Exchange("Redeem legacy parcel: Medicine","Farming",1)},
{"casinocoin|delvefarmdispatch|240|delvefarmparcelrations=1",new Exchange("Redeem legacy parcel: Rations","Farming",1)}};}}
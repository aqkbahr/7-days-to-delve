using System;
using Delve;
class ProgressionUiTests
{
    static int checks;
    static void Assert(bool condition,string name){checks++;if(!condition)throw new Exception(name);}
    static void Main()
    {
        Assert(ProgressionUiModel.Fraction(0)==0,"baseline");
        Assert(ProgressionUiModel.Fraction(22)==.5f,"half first rank");
        Assert(ProgressionUiModel.Fraction(44)==0,"rank rollover");
        Assert(ProgressionUiModel.Fraction(23760)==1,"cap");
        Assert(ProgressionUiModel.Fraction(float.NaN)==0,"invalid save");
        foreach(var skill in ProgressionUiData.Skills)
        foreach(var perk in skill.Perks)
        {
            Assert(TalentCatalog.Entries.ContainsKey(perk.Id),"catalog identity");
            string[] pages=ProgressionUiModel.Pages(perk.Description,30,10);
            Assert(pages.Length>0,"description exists");
            foreach(string page in pages)Assert(page.Split('\n').Length<=10,"vertical bounds");
            Assert(string.Join(" ",pages).Replace('\n',' ')==string.Join(" ",perk.Description.Split(new char[]{' ','\n','\r'},StringSplitOptions.RemoveEmptyEntries)),"no lost description text");
        }
        Console.WriteLine("PASS: "+checks+" progression UI model checks.");
    }
}

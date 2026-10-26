using System;
using System.Collections.Generic;
using System.Text;
namespace Delve
{
    public sealed class PerkUiDefinition
    {
        public readonly string Id, Name, Description;
        public PerkUiDefinition(string id,string name,string description) { Id=id;Name=name;Description=description; }
    }
    public sealed class SkillUiDefinition
    {
        public readonly string Id, Title, Training;
        public readonly int Tab;
        public readonly string[] Branches;
        public readonly PerkUiDefinition[] Perks;
        public SkillUiDefinition(string id,string title,int tab,string training,string[] branches,PerkUiDefinition[] perks)
        { Id=id;Title=title;Tab=tab;Training=training;Branches=branches;Perks=perks; }
    }
    public static class ProgressionUiModel
    {
        // Explicit wrapping makes long design descriptions readable without clipping.
        public static string[] Pages(string text,int columns,int rows)
        {
            var lines=new List<string>();var line=new StringBuilder();
            foreach(string word in (text??"").Split(new char[]{' ','\r','\n'},StringSplitOptions.RemoveEmptyEntries))
            {
                if(line.Length>0 && line.Length+word.Length+1>columns) {lines.Add(line.ToString());line.Length=0;}
                if(line.Length>0)line.Append(' ');line.Append(word);
            }
            if(line.Length>0)lines.Add(line.ToString());
            var pages=new List<string>();
            for(int i=0;i<lines.Count;i+=rows)pages.Add(string.Join("\n",lines.GetRange(i,Math.Min(rows,lines.Count-i)).ToArray()));
            if(pages.Count==0)pages.Add("");return pages.ToArray();
        }
        public static float Fraction(float practice)
        {
            practice=ProficiencyRules.Credit(practice,0);int rank=ProficiencyRules.Rank(practice);
            return rank==100?1:(practice-ProficiencyRules.Threshold(rank))/ProficiencyRules.NextCost(rank);
        }
    }
}

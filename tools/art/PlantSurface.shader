Shader "Delve/BotanicalSurface" {
 Properties {
  _MainTex("Botanical albedo",2D)="white"{} _BumpMap("Micro normal",2D)="bump"{}
  _BumpScale("Normal strength",Range(0,1))=.3
 }
 SubShader {
  Tags {"RenderType"="Opaque"} LOD 250
  Cull Off
  CGPROGRAM
  #pragma surface surf Standard fullforwardshadows vertex:vert
  #pragma target 3.0
  #include "UnityStandardUtils.cginc"
  sampler2D _MainTex,_BumpMap;half _BumpScale;
  struct Input {float2 uv_MainTex;float4 color:COLOR;float facing:VFACE;};
  void vert(inout appdata_full v){ }
  void surf(Input IN,inout SurfaceOutputStandard o){
   o.Albedo=tex2D(_MainTex,IN.uv_MainTex).rgb*IN.color.rgb;
   o.Normal=UnpackScaleNormal(tex2D(_BumpMap,IN.uv_MainTex),_BumpScale);o.Normal.z*=IN.facing>=0?1:-1;
   o.Metallic=0;o.Smoothness=.17;o.Occlusion=IN.color.a;o.Alpha=1;
  }
  ENDCG
 }
 FallBack "Standard"
}

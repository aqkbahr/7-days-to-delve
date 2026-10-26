Shader "Delve/WeaponRebuildSurface" {
 Properties {
  _MainTex("Original material albedo",2D)="white"{} _BumpMap("Micro normal",2D)="bump"{}
  _MetallicGlossMap("Metallic / smoothness",2D)="black"{} _OcclusionMap("Micro occlusion",2D)="white"{}
  _EmissionMap("Mineral emission",2D)="black"{} _BumpScale("Normal strength",Range(0,1))=.35
 }
 SubShader {
  Tags {"RenderType"="Opaque"} LOD 300
  CGPROGRAM
  #pragma surface surf Standard fullforwardshadows
  #pragma target 3.0
  #include "UnityStandardUtils.cginc"
  sampler2D _MainTex,_BumpMap,_MetallicGlossMap,_OcclusionMap,_EmissionMap;half _BumpScale;
  struct Input {float2 uv_MainTex;float4 color:COLOR;};
  void surf(Input IN,inout SurfaceOutputStandard o){
   fixed4 metal=tex2D(_MetallicGlossMap,IN.uv_MainTex);o.Albedo=tex2D(_MainTex,IN.uv_MainTex).rgb*IN.color.rgb;
   o.Normal=UnpackScaleNormal(tex2D(_BumpMap,IN.uv_MainTex),_BumpScale);o.Metallic=metal.r;o.Smoothness=metal.a;
   o.Occlusion=tex2D(_OcclusionMap,IN.uv_MainTex).g*IN.color.a;o.Emission=tex2D(_EmissionMap,IN.uv_MainTex).rgb*.12;o.Alpha=1;
  }
  ENDCG
 }
 FallBack "Standard"
}

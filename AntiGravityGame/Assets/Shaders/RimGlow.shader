Shader "AntiGravity/RimGlow"
{
    // ─────────────────────────────────────────────────────────────
    // Rim glow shader for objects affected by gravity fields.
    // Adds a pulsing emissive rim light that indicates the object
    // is currently in an altered gravity state (floating, levitated).
    //
    // Usage: Apply to any gravity-affected object's material.
    //        Toggle via _GlowActive and set color per gravity state.
    //
    // Mobile-optimized: Simple fresnel calculation, no extra passes.
    // ─────────────────────────────────────────────────────────────

    Properties
    {
        // Base material properties
        _MainTex ("Albedo (RGB)", 2D) = "white" {}
        _Color ("Base Color", Color) = (1, 1, 1, 1)
        _Glossiness ("Smoothness", Range(0, 1)) = 0.5
        _Metallic ("Metallic", Range(0, 1)) = 0.0
        _BumpMap ("Normal Map", 2D) = "bump" {}
        _BumpScale ("Normal Scale", Range(0, 2)) = 1.0

        [Header(Rim Glow)]
        _RimColor ("Rim Glow Color", Color) = (0.31, 0.76, 0.97, 1.0)
        _RimPower ("Rim Fresnel Power", Range(0.1, 10)) = 2.5
        _RimIntensity ("Rim Intensity", Range(0, 10)) = 2.0

        [Header(Animation)]
        _PulseSpeed ("Pulse Speed", Range(0, 10)) = 2.0
        _PulseMin ("Pulse Minimum", Range(0, 1)) = 0.3
        _FloatAmplitude ("Float Bobbing Amplitude", Range(0, 1)) = 0.1
        _FloatSpeed ("Float Bobbing Speed", Range(0, 5)) = 1.5

        [Header(State)]
        _GlowActive ("Glow Active (0=off, 1=on)", Range(0, 1)) = 0.0
        _TransitionProgress ("Transition Progress (0→1)", Range(0, 1)) = 0.0
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows vertex:vert
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _BumpMap;

        fixed4 _Color;
        half _Glossiness;
        half _Metallic;
        half _BumpScale;

        fixed4 _RimColor;
        half _RimPower;
        half _RimIntensity;
        half _PulseSpeed;
        half _PulseMin;
        half _FloatAmplitude;
        half _FloatSpeed;
        half _GlowActive;
        half _TransitionProgress;

        struct Input
        {
            float2 uv_MainTex;
            float2 uv_BumpMap;
            float3 viewDir;
            float3 worldNormal;
            INTERNAL_DATA
        };

        // ─── Vertex Modifier: Floating bobbing effect ───
        void vert(inout appdata_full v)
        {
            // Add subtle vertical bobbing when object is floating
            float bob = sin(_Time.y * _FloatSpeed + v.vertex.x * 2.0) * _FloatAmplitude;
            bob *= _GlowActive; // Only bob when glow is active (= floating)
            v.vertex.y += bob;

            // Slight rotation wobble for organic feel
            float wobble = sin(_Time.y * _FloatSpeed * 0.7 + v.vertex.z) * 0.02 * _GlowActive;
            v.vertex.x += wobble;
        }

        void surf(Input IN, inout SurfaceOutputStandard o)
        {
            // ── Base material ──
            fixed4 albedo = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = albedo.rgb;
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
            o.Normal = UnpackScaleNormal(tex2D(_BumpMap, IN.uv_BumpMap), _BumpScale);
            o.Alpha = albedo.a;

            // ── Rim glow (only when active) ──
            if (_GlowActive > 0.01)
            {
                // Fresnel rim calculation
                float3 worldNorm = WorldNormalVector(IN, o.Normal);
                float rim = 1.0 - saturate(dot(normalize(IN.viewDir), worldNorm));
                rim = pow(rim, _RimPower);

                // Pulsing animation
                float pulse = lerp(_PulseMin, 1.0,
                    (sin(_Time.y * _PulseSpeed * 3.14159) * 0.5 + 0.5));

                // Transition fade-in (smooth entry/exit)
                float transitionMask = smoothstep(0.0, 1.0, _TransitionProgress);

                // Final emission
                float3 rimEmission = _RimColor.rgb * rim * _RimIntensity
                    * pulse * _GlowActive * transitionMask;

                o.Emission = rimEmission;
            }
        }
        ENDCG
    }

    // ─── LOD Fallback for low-end mobile ───
    SubShader
    {
        Tags { "RenderType" = "Opaque" }
        LOD 100

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            fixed4 _RimColor;
            half _GlowActive;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : NORMAL;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                half rim : TEXCOORD1;
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);

                // Simplified rim calculation in vertex shader (cheaper)
                float3 viewDir = normalize(ObjSpaceViewDir(v.vertex));
                o.rim = 1.0 - saturate(dot(v.normal, viewDir));
                o.rim = pow(o.rim, 2.0) * _GlowActive;

                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv) * _Color;
                col.rgb += _RimColor.rgb * i.rim * 1.5;
                return col;
            }
            ENDCG
        }
    }

    FallBack "Mobile/Diffuse"
}

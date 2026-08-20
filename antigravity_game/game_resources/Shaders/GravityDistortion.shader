Shader "AntiGravity/GravityDistortion"
{
    // ─────────────────────────────────────────────────────────────
    // Heat-haze distortion shader for gravity zone boundaries.
    // Creates a refraction-like effect that warps the background,
    // visually indicating the edge of a gravity field.
    //
    // Usage: Apply to a sphere/box mesh marking the zone boundary.
    //        The mesh should use a transparent render queue.
    //
    // Mobile-optimized: Uses grab pass with reduced resolution
    //                   and simple UV distortion (no ray-marching).
    // ─────────────────────────────────────────────────────────────

    Properties
    {
        [Header(Distortion)]
        _DistortionStrength ("Distortion Strength", Range(0, 0.5)) = 0.1
        _DistortionSpeed ("Distortion Animation Speed", Range(0, 5)) = 1.0
        _DistortionScale ("Noise Scale", Range(0.1, 20)) = 4.0
        _DistortionTex ("Distortion Normal Map", 2D) = "bump" {}

        [Header(Edge Glow)]
        _EdgeColor ("Edge Color", Color) = (0.31, 0.76, 0.97, 1.0)
        _EdgePower ("Edge Fresnel Power", Range(0.1, 10)) = 3.0
        _EdgeIntensity ("Edge Glow Intensity", Range(0, 5)) = 1.5

        [Header(Pulse Animation)]
        _PulseSpeed ("Pulse Speed", Range(0, 5)) = 1.5
        _PulseAmplitude ("Pulse Amplitude", Range(0, 1)) = 0.3

        [Header(Zone State)]
        _GravityIntensity ("Gravity Intensity (0=off, 1=full)", Range(0, 1)) = 1.0
        _ZoneRadius ("Zone Radius", Float) = 10.0
    }

    SubShader
    {
        Tags
        {
            "Queue" = "Transparent+100"
            "RenderType" = "Transparent"
            "IgnoreProjector" = "True"
        }

        // Grab the screen behind the object for distortion
        GrabPass { "_GravDistortGrabTex" }

        Pass
        {
            Name "GRAVITY_DISTORTION"
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Back

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma target 3.0

            #include "UnityCG.cginc"

            // ─── Properties ───
            sampler2D _GravDistortGrabTex;
            float4 _GravDistortGrabTex_TexelSize;
            sampler2D _DistortionTex;
            float4 _DistortionTex_ST;

            half _DistortionStrength;
            half _DistortionSpeed;
            half _DistortionScale;
            fixed4 _EdgeColor;
            half _EdgePower;
            half _EdgeIntensity;
            half _PulseSpeed;
            half _PulseAmplitude;
            half _GravityIntensity;
            float _ZoneRadius;

            // ─── Vertex Data ───
            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float4 grabPos : TEXCOORD0;
                float2 uv : TEXCOORD1;
                float3 worldNormal : TEXCOORD2;
                float3 worldViewDir : TEXCOORD3;
                float3 worldPos : TEXCOORD4;
                UNITY_FOG_COORDS(5)
            };

            // ─── Vertex Shader ───
            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.grabPos = ComputeGrabScreenPos(o.pos);
                o.uv = TRANSFORM_TEX(v.uv, _DistortionTex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                float3 worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldPos = worldPos;
                o.worldViewDir = normalize(UnityWorldSpaceViewDir(worldPos));
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            // ─── Fragment Shader ───
            fixed4 frag(v2f i) : SV_Target
            {
                // Skip if zone is inactive
                if (_GravityIntensity < 0.001)
                    discard;

                // ── 1. Animated UV distortion ──
                float2 distortUV = i.uv * _DistortionScale;
                distortUV += _Time.y * _DistortionSpeed * float2(0.11, 0.13);

                // Sample normal map for distortion direction
                float3 distortNormal = UnpackNormal(tex2D(_DistortionTex, distortUV));

                // Secondary layer for more organic movement
                float2 distortUV2 = i.uv * _DistortionScale * 0.7;
                distortUV2 -= _Time.y * _DistortionSpeed * 0.8 * float2(0.17, -0.09);
                float3 distortNormal2 = UnpackNormal(tex2D(_DistortionTex, distortUV2));

                // Combine distortion layers
                float2 totalDistort = (distortNormal.xy + distortNormal2.xy) * 0.5;

                // Apply pulse animation
                float pulse = 1.0 + sin(_Time.y * _PulseSpeed * 3.14159) * _PulseAmplitude;
                totalDistort *= _DistortionStrength * _GravityIntensity * pulse;

                // ── 2. Sample distorted screen texture ──
                float2 grabUV = i.grabPos.xy / i.grabPos.w;
                grabUV += totalDistort;
                fixed4 grabColor = tex2D(_GravDistortGrabTex, grabUV);

                // ── 3. Fresnel edge glow ──
                float fresnel = 1.0 - saturate(dot(normalize(i.worldNormal),
                    normalize(i.worldViewDir)));
                fresnel = pow(fresnel, _EdgePower);
                fresnel *= _EdgeIntensity * _GravityIntensity * pulse;

                fixed4 edgeGlow = _EdgeColor * fresnel;

                // ── 4. Distance-based fade (softer at center, stronger at edges) ──
                float distFromCenter = length(i.worldPos - mul(unity_ObjectToWorld,
                    float4(0, 0, 0, 1)).xyz);
                float edgeFade = saturate(distFromCenter / max(_ZoneRadius, 0.01));
                edgeFade = smoothstep(0.3, 0.9, edgeFade); // Visible mainly near edges

                // ── 5. Composite ──
                fixed4 finalColor = grabColor + edgeGlow * edgeFade;
                finalColor.a = saturate(fresnel * edgeFade + totalDistort.x * 2.0)
                    * _GravityIntensity;

                UNITY_APPLY_FOG(i.fogCoord, finalColor);
                return finalColor;
            }
            ENDCG
        }
    }

    FallBack "Transparent/Diffuse"
}

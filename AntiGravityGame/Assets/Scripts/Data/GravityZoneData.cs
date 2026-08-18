using UnityEngine;

namespace AntiGravity.Data
{
    /// <summary>
    /// ScriptableObject defining the properties of a gravity zone.
    /// Create instances via Assets > Create > AntiGravity > Gravity Zone Data.
    /// </summary>
    [CreateAssetMenu(fileName = "NewGravityZone", menuName = "AntiGravity/Gravity Zone Data")]
    public class GravityZoneData : ScriptableObject
    {
        [Header("=== Zone Identity ===")]
        [Tooltip("Unique identifier for this gravity zone type")]
        public string zoneId;

        [Tooltip("Display name shown in HUD when player enters")]
        public string displayName;

        [Header("=== Gravity Parameters ===")]
        [Tooltip("Gravity multiplier: 1.0 = normal, 0.0 = zero-G, -1.0 = reversed, 3.0 = hyper")]
        [Range(-5f, 5f)]
        public float gravityMultiplier = 0f;

        [Tooltip("Custom gravity direction (normalized). Leave zero to use multiplier on world gravity.")]
        public Vector3 customGravityDirection = Vector3.zero;

        [Tooltip("Magnitude of custom gravity in m/s². Only used if customGravityDirection is non-zero.")]
        [Range(0f, 50f)]
        public float customGravityMagnitude = 9.81f;

        [Header("=== Zone Shape ===")]
        [Tooltip("Shape of the gravity zone collider")]
        public ZoneShape shape = ZoneShape.Sphere;

        [Tooltip("Radius for spherical zones or half-extents for box zones")]
        public float radius = 10f;

        [Tooltip("Half-extents for box-shaped zones (x, y, z)")]
        public Vector3 boxHalfExtents = new Vector3(5f, 5f, 5f);

        [Header("=== Transition Behavior ===")]
        [Tooltip("Time in seconds to interpolate from normal gravity to this zone's gravity on enter")]
        [Range(0.01f, 5f)]
        public float enterTransitionDuration = 0.5f;

        [Tooltip("Time in seconds to interpolate back to normal gravity on exit")]
        [Range(0.01f, 5f)]
        public float exitTransitionDuration = 0.8f;

        [Tooltip("Easing curve for gravity transition (0→1 over transition duration)")]
        public AnimationCurve transitionCurve = AnimationCurve.EaseInOut(0f, 0f, 1f, 1f);

        [Header("=== Force Modifiers ===")]
        [Tooltip("Additional drag applied to objects inside the zone (simulates resistance)")]
        [Range(0f, 20f)]
        public float additionalDrag = 1.5f;

        [Tooltip("Angular drag modifier inside the zone")]
        [Range(0f, 20f)]
        public float additionalAngularDrag = 0.5f;

        [Tooltip("Maximum force that can be applied to any single object (prevents explosion)")]
        public float maxForceClamp = 500f;

        [Tooltip("Dampening factor applied to velocity inside zone (0 = no damping, 1 = full stop)")]
        [Range(0f, 1f)]
        public float velocityDampening = 0.05f;

        [Header("=== Falloff ===")]
        [Tooltip("Whether gravity effect falls off with distance from zone center")]
        public bool useDistanceFalloff = true;

        [Tooltip("Falloff curve: X = normalized distance (0=center, 1=edge), Y = gravity strength multiplier")]
        public AnimationCurve falloffCurve = AnimationCurve.Linear(0f, 1f, 1f, 0f);

        [Header("=== Duration & Persistence ===")]
        [Tooltip("Whether this zone is permanent or temporary")]
        public bool isPersistent = true;

        [Tooltip("Duration in seconds before zone expires (only if not persistent)")]
        [Range(0.1f, 60f)]
        public float duration = 10f;

        [Header("=== Visual Theme ===")]
        [Tooltip("Primary color for VFX and particles in this zone")]
        public Color primaryColor = new Color(0.31f, 0.76f, 0.97f, 1f); // Soft Cyan

        [Tooltip("Accent/secondary color for particle trails and highlights")]
        public Color accentColor = new Color(0.81f, 0.58f, 0.85f, 1f); // Lavender

        [Tooltip("Particle emission rate multiplier")]
        [Range(0f, 10f)]
        public float particleIntensity = 1f;

        [Tooltip("Distortion shader intensity at zone boundary")]
        [Range(0f, 2f)]
        public float distortionStrength = 0.3f;

        [Header("=== Audio ===")]
        [Tooltip("Ambient sound loop played while inside the zone")]
        public AudioClip ambientSound;

        [Tooltip("Sound played on entering the zone")]
        public AudioClip enterSound;

        [Tooltip("Sound played on exiting the zone")]
        public AudioClip exitSound;

        [Tooltip("Volume of ambient sound")]
        [Range(0f, 1f)]
        public float ambientVolume = 0.5f;

        // ─── Computed Properties ───

        /// <summary>
        /// Returns the effective gravity vector for this zone.
        /// If customGravityDirection is set, uses that; otherwise multiplies world gravity.
        /// </summary>
        public Vector3 EffectiveGravity
        {
            get
            {
                if (customGravityDirection.sqrMagnitude > 0.001f)
                    return customGravityDirection.normalized * customGravityMagnitude;
                return Physics.gravity * gravityMultiplier;
            }
        }

        /// <summary>
        /// Returns the gravity state enum based on the multiplier value.
        /// Used for UI display and VFX color selection.
        /// </summary>
        public GravityState GetGravityState()
        {
            if (gravityMultiplier < -0.1f) return GravityState.AntiGravity;
            if (gravityMultiplier < 0.1f) return GravityState.ZeroGravity;
            if (gravityMultiplier < 0.7f) return GravityState.LowGravity;
            if (gravityMultiplier < 1.3f) return GravityState.Normal;
            return GravityState.HyperGravity;
        }

        /// <summary>
        /// Evaluates the gravity strength at a given normalized distance (0 = center, 1 = edge).
        /// </summary>
        public float EvaluateFalloff(float normalizedDistance)
        {
            if (!useDistanceFalloff) return 1f;
            return falloffCurve.Evaluate(Mathf.Clamp01(normalizedDistance));
        }
    }

    // ─── Supporting Enums ───

    public enum ZoneShape
    {
        Sphere,
        Box,
        Cylinder,
        Custom // Uses MeshCollider
    }

    public enum GravityState
    {
        Normal,       // 1.0G — standard
        LowGravity,   // 0.1–0.7G — floaty
        ZeroGravity,  // ~0G — weightless
        AntiGravity,  // Negative — reversed
        HyperGravity  // >1.3G — crushing
    }
}

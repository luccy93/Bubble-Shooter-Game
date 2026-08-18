using UnityEngine;

namespace AntiGravity.Data
{
    /// <summary>
    /// ScriptableObject defining mass/weight profiles for physics-interactive objects.
    /// Determines how objects respond to gravity zones and the player's gravity tool.
    /// Create via Assets > Create > AntiGravity > Object Mass Profile.
    /// </summary>
    [CreateAssetMenu(fileName = "NewMassProfile", menuName = "AntiGravity/Object Mass Profile")]
    public class ObjectMassProfile : ScriptableObject
    {
        [Header("=== Object Classification ===")]
        [Tooltip("Mass category determining base physics behavior")]
        public MassClass massClass = MassClass.Standard;

        [Tooltip("Display name for UI/debug purposes")]
        public string objectName = "Unnamed Object";

        [Header("=== Physical Properties ===")]
        [Tooltip("Base mass in kilograms")]
        [Range(0.01f, 10000f)]
        public float baseMass = 10f;

        [Tooltip("Base drag coefficient (air resistance)")]
        [Range(0f, 20f)]
        public float baseDrag = 0.5f;

        [Tooltip("Base angular drag (rotational resistance)")]
        [Range(0f, 20f)]
        public float baseAngularDrag = 0.5f;

        [Tooltip("Bounciness of the object (0 = no bounce, 1 = perfect bounce)")]
        [Range(0f, 1f)]
        public float bounciness = 0.3f;

        [Tooltip("Friction coefficient")]
        [Range(0f, 1f)]
        public float friction = 0.5f;

        [Header("=== Gravity Response ===")]
        [Tooltip("Whether this object is affected by gravity zones at all")]
        public bool isGravityReactive = true;

        [Tooltip("Whether the object is anchored (immune to gravity manipulation)")]
        public bool isAnchored = false;

        [Tooltip("Force multiplier when inside a gravity zone (1.0 = normal response)")]
        [Range(0f, 5f)]
        public float gravityResponseMultiplier = 1f;

        [Tooltip("Maximum velocity this object can reach due to gravity forces (m/s)")]
        [Range(1f, 200f)]
        public float terminalVelocity = 50f;

        [Tooltip("How quickly the object transitions between gravity states")]
        [Range(0.01f, 3f)]
        public float gravityTransitionSpeed = 1f;

        [Header("=== Tool Interaction ===")]
        [Tooltip("Whether the player's gravity tool can affect this object")]
        public bool isToolInteractable = true;

        [Tooltip("Force multiplier when hit by the gravity tool")]
        [Range(0f, 5f)]
        public float toolForceMultiplier = 1f;

        [Tooltip("Whether this object can be fully levitated (held in place)")]
        public bool canBeLevitated = true;

        [Tooltip("Whether this object can be launched as a projectile")]
        public bool canBeLaunched = true;

        [Header("=== Reactive Behavior ===")]
        [Tooltip("What happens when gravity state changes dramatically")]
        public ReactiveType reactiveType = ReactiveType.None;

        [Tooltip("Force threshold that triggers the reactive behavior")]
        [Range(0f, 1000f)]
        public float reactiveForceThreshold = 100f;

        [Tooltip("Prefab spawned when reactive behavior triggers (explosion, split, etc.)")]
        public GameObject reactivePrefab;

        [Header("=== Visual Feedback ===")]
        [Tooltip("Color tint when floating in anti-gravity")]
        public Color floatingTint = new Color(0.8f, 0.9f, 1f, 1f);

        [Tooltip("Whether to show rim glow when affected by gravity fields")]
        public bool showRimGlow = true;

        [Tooltip("Rim glow intensity multiplier")]
        [Range(0f, 5f)]
        public float rimGlowIntensity = 1.5f;

        [Header("=== Audio ===")]
        [Tooltip("Sound played when the object starts floating")]
        public AudioClip liftSound;

        [Tooltip("Sound played when the object impacts after falling")]
        public AudioClip impactSound;

        [Tooltip("Continuous sound while floating (e.g., humming)")]
        public AudioClip floatingLoopSound;

        // ─── Computed Properties ───

        /// <summary>
        /// Returns the effective force needed to lift this object against standard gravity.
        /// F = m × g (mass × 9.81)
        /// </summary>
        public float LiftForceRequired => baseMass * 9.81f;

        /// <summary>
        /// Returns a normalized "heaviness" value (0 = feather, 1 = ultra-heavy).
        /// Used for VFX intensity scaling and UI indicators.
        /// </summary>
        public float NormalizedHeaviness
        {
            get
            {
                // Logarithmic scale: 0.01kg → 0, 10kg → 0.5, 10000kg → 1.0
                return Mathf.Clamp01(Mathf.Log10(baseMass + 1f) / 4f);
            }
        }

        /// <summary>
        /// Returns whether this object should respond to a given gravity zone.
        /// </summary>
        public bool ShouldRespondToZone(GravityZoneData zone)
        {
            if (!isGravityReactive || isAnchored) return false;
            return true;
        }

        /// <summary>
        /// Calculate the effective force applied to this object given a gravity field strength.
        /// Applies mass, response multiplier, and clamping.
        /// </summary>
        public Vector3 CalculateGravityForce(Vector3 fieldGravity, float fieldStrength)
        {
            if (!isGravityReactive || isAnchored) return Vector3.zero;

            Vector3 force = fieldGravity * baseMass * gravityResponseMultiplier * fieldStrength;

            // Clamp to prevent extreme forces on very heavy objects
            if (force.magnitude > baseMass * terminalVelocity)
                force = force.normalized * baseMass * terminalVelocity;

            return force;
        }
    }

    // ─── Supporting Enums ───

    public enum MassClass
    {
        UltraLight,  // 0.01–1 kg  — instant liftoff, chaotic float
        Standard,    // 1–50 kg    — gradual lift, controllable
        Heavy,       // 50–500 kg  — slow rise, sustained field required
        Anchored,    // Infinite   — immune to manipulation
        Reactive     // Variable   — triggers special behavior on gravity change
    }

    public enum ReactiveType
    {
        None,        // No special reaction
        Explode,     // Detonates when force threshold exceeded
        Split,       // Breaks into smaller pieces
        Chain,       // Triggers other reactive objects nearby
        Magnetic,    // Attracts other floating objects
        Volatile     // Unstable — random force applied periodically
    }
}

using UnityEngine;

namespace AntiGravity.Data
{
    /// <summary>
    /// ScriptableObject defining player gravity tool/ability properties.
    /// Create instances via Assets > Create > AntiGravity > Gravity Tool Data.
    /// </summary>
    [CreateAssetMenu(fileName = "NewGravityTool", menuName = "AntiGravity/Gravity Tool Data")]
    public class GravityToolData : ScriptableObject
    {
        [Header("=== Tool Identity ===")]
        [Tooltip("Display name for the HUD")]
        public string toolName = "Gravity Manipulator";

        [Tooltip("Icon displayed in the tool status UI")]
        public Sprite toolIcon;

        [Header("=== Beam Properties ===")]
        [Tooltip("Maximum range of the gravity beam in meters")]
        [Range(5f, 100f)]
        public float maxRange = 30f;

        [Tooltip("Beam radius for area-of-effect at the target point")]
        [Range(0.5f, 10f)]
        public float beamRadius = 2f;

        [Tooltip("How quickly the beam sweeps to a new target (degrees/sec)")]
        [Range(10f, 360f)]
        public float beamTrackingSpeed = 180f;

        [Header("=== Force Parameters ===")]
        [Tooltip("Base force applied to objects hit by the beam (Newtons)")]
        [Range(10f, 5000f)]
        public float baseForce = 500f;

        [Tooltip("Force multiplier at max charge")]
        [Range(1f, 10f)]
        public float maxChargeMultiplier = 3f;

        [Tooltip("Time in seconds to reach full charge")]
        [Range(0.1f, 5f)]
        public float chargeTime = 1.5f;

        [Tooltip("Charge curve: X = time (0→chargeTime), Y = force multiplier (0→1)")]
        public AnimationCurve chargeCurve = AnimationCurve.EaseInOut(0f, 0f, 1f, 1f);

        [Header("=== Modes ===")]
        [Tooltip("Available gravity manipulation modes for this tool")]
        public GravityToolMode[] availableModes = new GravityToolMode[]
        {
            GravityToolMode.Repulse,
            GravityToolMode.Attract,
            GravityToolMode.Levitate,
            GravityToolMode.Reverse
        };

        [Header("=== Energy System ===")]
        [Tooltip("Maximum energy pool for the tool")]
        [Range(10f, 1000f)]
        public float maxEnergy = 100f;

        [Tooltip("Energy consumed per second while the beam is active")]
        [Range(1f, 50f)]
        public float energyDrainRate = 15f;

        [Tooltip("Energy regeneration per second when not in use")]
        [Range(1f, 30f)]
        public float energyRegenRate = 8f;

        [Tooltip("Delay before energy starts regenerating after use (seconds)")]
        [Range(0f, 5f)]
        public float regenDelay = 1.0f;

        [Tooltip("Minimum energy required to activate the tool")]
        [Range(0f, 30f)]
        public float minActivationEnergy = 10f;

        [Header("=== Cooldowns ===")]
        [Tooltip("Cooldown between switching gravity modes (seconds)")]
        [Range(0f, 3f)]
        public float modeSwitchCooldown = 0.3f;

        [Tooltip("Cooldown after a full-charge release (seconds)")]
        [Range(0f, 5f)]
        public float chargeReleaseCooldown = 1.0f;

        [Header("=== Object Interaction ===")]
        [Tooltip("Maximum mass the tool can fully levitate (kg)")]
        [Range(1f, 1000f)]
        public float maxLiftMass = 200f;

        [Tooltip("Maximum number of objects the tool can affect simultaneously")]
        [Range(1, 20)]
        public int maxSimultaneousObjects = 5;

        [Tooltip("Force reduction per additional object (multiplicative)")]
        [Range(0.5f, 1f)]
        public float multiObjectForceFalloff = 0.8f;

        [Header("=== Haptic Feedback (Mobile) ===")]
        [Tooltip("Vibration intensity when tool is active (0 = none, 1 = max)")]
        [Range(0f, 1f)]
        public float hapticIntensity = 0.3f;

        [Tooltip("Vibration pattern duration in milliseconds")]
        [Range(10, 500)]
        public int hapticDurationMs = 50;

        [Header("=== Visual ===")]
        [Tooltip("Beam color when in Repulse mode")]
        public Color repulseColor = new Color(1f, 0.44f, 0.26f, 1f); // Warm Orange

        [Tooltip("Beam color when in Attract mode")]
        public Color attractColor = new Color(0.31f, 0.76f, 0.97f, 1f); // Cyan

        [Tooltip("Beam color when in Levitate mode")]
        public Color levitateColor = new Color(0.81f, 0.58f, 0.85f, 1f); // Lavender

        [Tooltip("Beam color when in Reverse mode")]
        public Color reverseColor = new Color(0.36f, 0.42f, 0.75f, 1f); // Deep Indigo

        // ─── Helper Methods ───

        /// <summary>
        /// Returns the beam color for the given gravity tool mode.
        /// </summary>
        public Color GetModeColor(GravityToolMode mode)
        {
            switch (mode)
            {
                case GravityToolMode.Repulse:  return repulseColor;
                case GravityToolMode.Attract:  return attractColor;
                case GravityToolMode.Levitate: return levitateColor;
                case GravityToolMode.Reverse:  return reverseColor;
                default: return Color.white;
            }
        }

        /// <summary>
        /// Calculates the effective force based on current charge level and number of targets.
        /// </summary>
        public float CalculateEffectiveForce(float chargeNormalized, int targetCount)
        {
            float chargeForce = baseForce * Mathf.Lerp(1f, maxChargeMultiplier,
                chargeCurve.Evaluate(chargeNormalized));
            float multiTargetPenalty = Mathf.Pow(multiObjectForceFalloff,
                Mathf.Max(0, targetCount - 1));
            return chargeForce * multiTargetPenalty;
        }

        /// <summary>
        /// Returns whether an object of the given mass can be fully levitated.
        /// </summary>
        public bool CanFullyLevitate(float objectMass) => objectMass <= maxLiftMass;
    }

    // ─── Supporting Enums ───

    public enum GravityToolMode
    {
        Repulse,   // Push objects away / upward
        Attract,   // Pull objects toward player
        Levitate,  // Suspend objects in place (zero-G bubble)
        Reverse    // Invert gravity direction for target
    }
}

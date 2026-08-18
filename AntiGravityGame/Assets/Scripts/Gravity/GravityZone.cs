using UnityEngine;
using AntiGravity.Core;
using AntiGravity.Data;

namespace AntiGravity.Gravity
{
    /// <summary>
    /// Defines a region of altered gravity in the game world.
    /// 
    /// Features:
    /// - Configurable shape (sphere, box, cylinder) via collider trigger
    /// - Smooth gravity transitions on enter/exit with AnimationCurve interpolation
    /// - Distance-based falloff from zone center
    /// - Priority system for overlapping zones
    /// - Optional duration for temporary zones (e.g., player-created traps)
    /// - VFX and audio integration hooks
    /// 
    /// Attach this to any GameObject with a trigger Collider.
    /// Assign a GravityZoneData ScriptableObject for configuration.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class GravityZone : MonoBehaviour
    {
        [Header("=== Zone Configuration ===")]
        [Tooltip("Data asset defining this zone's gravity behavior")]
        [SerializeField] private GravityZoneData zoneData;

        [Tooltip("Priority for overlap resolution (higher = dominant)")]
        [SerializeField] private int priority = 0;

        [Tooltip("Whether this zone moves at runtime (moving zones update spatial grid)")]
        [SerializeField] private bool isMoving = false;

        [Header("=== Runtime Overrides ===")]
        [Tooltip("Override gravity multiplier at runtime (e.g., via gameplay events)")]
        [SerializeField] private float runtimeGravityMultiplierOverride = -1f; // -1 = use data

        [Header("=== References ===")]
        [Tooltip("Optional: Visual boundary mesh for distortion shader")]
        [SerializeField] private Renderer boundaryRenderer;

        [Tooltip("Optional: Particle system for ambient zone particles")]
        [SerializeField] private ParticleSystem ambientParticles;

        [Tooltip("Optional: Audio source for ambient zone sound")]
        [SerializeField] private AudioSource ambientAudio;

        // ─── Public Properties ───
        public GravityZoneData ZoneData => zoneData;
        public int Priority => priority;
        public bool IsMoving => isMoving;
        public bool IsActive { get; private set; } = true;

        // ─── Internal State ───
        private Collider _collider;
        private float _lifetimeTimer;
        private bool _isExpiring;

        // Shader property IDs (cached for performance)
        private static readonly int ShaderGravityIntensity =
            Shader.PropertyToID("_GravityIntensity");
        private static readonly int ShaderEdgeColor =
            Shader.PropertyToID("_EdgeColor");
        private static readonly int ShaderZoneRadius =
            Shader.PropertyToID("_ZoneRadius");
        private static readonly int ShaderDistortionStrength =
            Shader.PropertyToID("_DistortionStrength");

        // ─── Lifecycle ───

        private void Awake()
        {
            _collider = GetComponent<Collider>();

            // Ensure collider is set as trigger
            if (!_collider.isTrigger)
            {
                _collider.isTrigger = true;
                Debug.LogWarning($"[GravityZone] Collider on '{name}' was not a trigger. " +
                    "Set to trigger automatically.");
            }

            // Configure collider size from zone data
            ConfigureColliderFromData();

            // Initialize visuals
            UpdateVisuals(1f);
        }

        private void OnEnable()
        {
            GravityManager.Instance?.RegisterZone(this);
            IsActive = true;

            // Start ambient audio
            if (ambientAudio != null && zoneData?.ambientSound != null)
            {
                ambientAudio.clip = zoneData.ambientSound;
                ambientAudio.volume = zoneData.ambientVolume;
                ambientAudio.loop = true;
                ambientAudio.Play();
            }
        }

        private void OnDisable()
        {
            GravityManager.Instance?.UnregisterZone(this);
            IsActive = false;

            ambientAudio?.Stop();
        }

        private void Update()
        {
            // Handle temporary zone expiration
            if (!zoneData.isPersistent && !_isExpiring)
            {
                _lifetimeTimer += Time.deltaTime;

                if (_lifetimeTimer >= zoneData.duration)
                {
                    StartExpiration();
                }
                else
                {
                    // Flash visual warning when about to expire
                    float remainingRatio = 1f - (_lifetimeTimer / zoneData.duration);
                    if (remainingRatio < 0.2f)
                    {
                        float flash = Mathf.PingPong(Time.time * 5f, 1f);
                        UpdateVisuals(Mathf.Lerp(0.3f, 1f, flash));
                    }
                }
            }

            // Handle expiration fade-out
            if (_isExpiring)
            {
                _lifetimeTimer += Time.deltaTime;
                float fadeProgress = _lifetimeTimer / zoneData.exitTransitionDuration;

                if (fadeProgress >= 1f)
                {
                    // Zone has fully faded — destroy or pool it
                    gameObject.SetActive(false);
                    return;
                }

                UpdateVisuals(1f - fadeProgress);
            }
        }

        // ─── Trigger Callbacks ───

        private void OnTriggerEnter(Collider other)
        {
            if (!IsActive) return;

            var affectedObj = other.GetComponent<GravityAffectedObject>();
            if (affectedObj != null)
            {
                affectedObj.OnEnterGravityZone(this);
                GravityManager.Instance?.NotifyZoneEnter(affectedObj, this);

                // Play enter sound
                if (zoneData.enterSound != null)
                    AudioSource.PlayClipAtPoint(zoneData.enterSound,
                        other.transform.position, 0.8f);
            }
        }

        private void OnTriggerExit(Collider other)
        {
            var affectedObj = other.GetComponent<GravityAffectedObject>();
            if (affectedObj != null)
            {
                affectedObj.OnExitGravityZone(this);
                GravityManager.Instance?.NotifyZoneExit(affectedObj, this);

                // Play exit sound
                if (zoneData.exitSound != null)
                    AudioSource.PlayClipAtPoint(zoneData.exitSound,
                        other.transform.position, 0.6f);
            }
        }

        // ─── Public API ───

        /// <summary>
        /// Check if a world-space point is inside this zone.
        /// Also outputs the normalized distance from center (0=center, 1=edge).
        /// </summary>
        public bool ContainsPoint(Vector3 worldPoint, out float normalizedDistance)
        {
            Vector3 localPoint = transform.InverseTransformPoint(worldPoint);

            switch (zoneData.shape)
            {
                case ZoneShape.Sphere:
                    float dist = localPoint.magnitude;
                    normalizedDistance = dist / zoneData.radius;
                    return dist <= zoneData.radius;

                case ZoneShape.Box:
                    Vector3 absLocal = new Vector3(
                        Mathf.Abs(localPoint.x),
                        Mathf.Abs(localPoint.y),
                        Mathf.Abs(localPoint.z));

                    bool inside = absLocal.x <= zoneData.boxHalfExtents.x &&
                                  absLocal.y <= zoneData.boxHalfExtents.y &&
                                  absLocal.z <= zoneData.boxHalfExtents.z;

                    // Normalized distance: max of the three axis ratios
                    normalizedDistance = Mathf.Max(
                        absLocal.x / zoneData.boxHalfExtents.x,
                        Mathf.Max(
                            absLocal.y / zoneData.boxHalfExtents.y,
                            absLocal.z / zoneData.boxHalfExtents.z));

                    return inside;

                default:
                    normalizedDistance = 0f;
                    return _collider.bounds.Contains(worldPoint);
            }
        }

        /// <summary>
        /// Get the current effective gravity multiplier (considering runtime overrides).
        /// </summary>
        public float GetEffectiveMultiplier()
        {
            if (runtimeGravityMultiplierOverride >= 0f)
                return runtimeGravityMultiplierOverride;
            return zoneData.gravityMultiplier;
        }

        /// <summary>
        /// Dynamically change the gravity multiplier at runtime.
        /// Useful for puzzle mechanics (e.g., switches that alter zones).
        /// </summary>
        public void SetGravityMultiplier(float newMultiplier)
        {
            runtimeGravityMultiplierOverride = newMultiplier;
        }

        /// <summary>
        /// Reset to the data-defined gravity multiplier.
        /// </summary>
        public void ResetGravityMultiplier()
        {
            runtimeGravityMultiplierOverride = -1f;
        }

        /// <summary>
        /// Force this zone to start its expiration sequence.
        /// </summary>
        public void ForceExpire()
        {
            if (!_isExpiring)
                StartExpiration();
        }

        // ─── Internal Helpers ───

        /// <summary>
        /// Configure the attached collider to match zone data dimensions.
        /// </summary>
        private void ConfigureColliderFromData()
        {
            if (zoneData == null) return;

            if (_collider is SphereCollider sphere)
            {
                sphere.radius = zoneData.radius;
            }
            else if (_collider is BoxCollider box)
            {
                box.size = zoneData.boxHalfExtents * 2f;
            }
        }

        /// <summary>
        /// Begin the zone expiration fade-out sequence.
        /// </summary>
        private void StartExpiration()
        {
            _isExpiring = true;
            _lifetimeTimer = 0f;
            IsActive = false; // Stop affecting new objects
        }

        /// <summary>
        /// Update visual elements (shader, particles) based on an intensity value.
        /// Used for fade-in/fade-out and expiration warning.
        /// </summary>
        private void UpdateVisuals(float intensity)
        {
            // Update distortion shader on boundary mesh
            if (boundaryRenderer != null)
            {
                var mat = boundaryRenderer.material;
                mat.SetFloat(ShaderGravityIntensity, intensity);
                mat.SetColor(ShaderEdgeColor, zoneData.primaryColor);
                mat.SetFloat(ShaderZoneRadius, zoneData.radius);
                mat.SetFloat(ShaderDistortionStrength,
                    zoneData.distortionStrength * intensity);
            }

            // Scale particle emission with intensity
            if (ambientParticles != null)
            {
                var emission = ambientParticles.emission;
                emission.rateOverTimeMultiplier = zoneData.particleIntensity * intensity * 50f;

                var main = ambientParticles.main;
                main.startColor = zoneData.primaryColor;
            }

            // Scale audio volume
            if (ambientAudio != null)
            {
                ambientAudio.volume = zoneData.ambientVolume * intensity;
            }
        }

        // ─── Debug ───

        private void OnDrawGizmosSelected()
        {
            if (zoneData == null) return;

            // Draw filled zone with transparency
            Gizmos.color = new Color(
                zoneData.primaryColor.r,
                zoneData.primaryColor.g,
                zoneData.primaryColor.b, 0.15f);

            if (zoneData.shape == ZoneShape.Sphere)
            {
                Gizmos.DrawSphere(transform.position, zoneData.radius);
                Gizmos.color = zoneData.primaryColor;
                Gizmos.DrawWireSphere(transform.position, zoneData.radius);
            }
            else
            {
                Gizmos.DrawCube(transform.position, zoneData.boxHalfExtents * 2f);
                Gizmos.color = zoneData.primaryColor;
                Gizmos.DrawWireCube(transform.position, zoneData.boxHalfExtents * 2f);
            }

            // Draw gravity direction
            Gizmos.color = Color.red;
            Gizmos.DrawRay(transform.position, zoneData.EffectiveGravity.normalized * 5f);
        }
    }
}

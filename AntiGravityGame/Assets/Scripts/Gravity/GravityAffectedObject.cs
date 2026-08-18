using System.Collections.Generic;
using UnityEngine;
using AntiGravity.Core;
using AntiGravity.Data;

namespace AntiGravity.Gravity
{
    /// <summary>
    /// Component attached to any Rigidbody that should respond to gravity zones
    /// and the player's gravity tool.
    /// 
    /// Features:
    /// - Smooth gravity transition interpolation on zone enter/exit
    /// - Multiple simultaneous zone support with blending
    /// - Mass-dependent response (via ObjectMassProfile)
    /// - Visual feedback (rim glow shader integration)
    /// - Velocity dampening inside zones
    /// - Terminal velocity clamping
    /// - Sleep optimization (stops updates when at rest)
    /// 
    /// Attach to any GameObject with a Rigidbody component.
    /// </summary>
    [RequireComponent(typeof(Rigidbody))]
    public class GravityAffectedObject : MonoBehaviour
    {
        [Header("=== Mass Profile ===")]
        [Tooltip("Physics profile defining how this object responds to gravity")]
        [SerializeField] private ObjectMassProfile massProfile;

        [Header("=== Visual Feedback ===")]
        [Tooltip("Renderer for rim glow shader (auto-detected if null)")]
        [SerializeField] private Renderer objectRenderer;

        [Header("=== Debug ===")]
        [SerializeField] private bool showDebugForces = false;

        // ─── Public State ───

        /// <summary>Current gravity being applied to this object.</summary>
        public Vector3 CurrentGravity { get; private set; }

        /// <summary>Current gravity state (for UI/VFX queries).</summary>
        public GravityState CurrentState { get; private set; } = GravityState.Normal;

        /// <summary>Whether the object is currently inside any gravity zone.</summary>
        public bool IsInGravityZone => _activeZones.Count > 0;

        /// <summary>Whether the Rigidbody is sleeping (not moving).</summary>
        public bool IsSleeping => _rigidbody != null && _rigidbody.IsSleeping();

        /// <summary>Number of gravity zones currently affecting this object.</summary>
        public int ActiveZoneCount => _activeZones.Count;

        // ─── Internal State ───
        private Rigidbody _rigidbody;
        private readonly List<ActiveZoneInfo> _activeZones = new List<ActiveZoneInfo>(4);

        // Cached default Rigidbody values (for restoration on zone exit)
        private float _defaultDrag;
        private float _defaultAngularDrag;
        private bool _defaultUseGravity;

        // Transition state
        private Vector3 _targetGravity;
        private Vector3 _currentAppliedGravity;
        private float _transitionTimer;
        private float _transitionDuration;
        private bool _isTransitioning;

        // Shader property IDs (cached)
        private static readonly int ShaderGlowActive = Shader.PropertyToID("_GlowActive");
        private static readonly int ShaderRimColor = Shader.PropertyToID("_RimColor");
        private static readonly int ShaderTransitionProgress =
            Shader.PropertyToID("_TransitionProgress");

        private MaterialPropertyBlock _materialProps;

        // ─── Lifecycle ───

        private void Awake()
        {
            _rigidbody = GetComponent<Rigidbody>();

            // Cache defaults for restoration
            _defaultDrag = _rigidbody.linearDamping;
            _defaultAngularDrag = _rigidbody.angularDamping;
            _defaultUseGravity = _rigidbody.useGravity;

            // Disable Unity's built-in gravity — we apply our own
            _rigidbody.useGravity = false;

            // Apply mass profile
            if (massProfile != null)
            {
                _rigidbody.mass = massProfile.baseMass;
                _rigidbody.linearDamping = massProfile.baseDrag;
                _rigidbody.angularDamping = massProfile.baseAngularDrag;
            }

            // Auto-detect renderer
            if (objectRenderer == null)
                objectRenderer = GetComponentInChildren<Renderer>();

            _materialProps = new MaterialPropertyBlock();
            _currentAppliedGravity = GravityManager.Instance?.DefaultGravity ?? Physics.gravity;
        }

        private void OnEnable()
        {
            GravityManager.Instance?.RegisterObject(this);
        }

        private void OnDisable()
        {
            GravityManager.Instance?.UnregisterObject(this);
            _activeZones.Clear();
        }

        // ─── Zone Enter/Exit (called by GravityZone) ───

        /// <summary>
        /// Called when this object enters a gravity zone's trigger.
        /// Begins smooth gravity transition.
        /// </summary>
        public void OnEnterGravityZone(GravityZone zone)
        {
            if (massProfile != null && !massProfile.isGravityReactive) return;
            if (massProfile != null && massProfile.isAnchored) return;

            // Check if already in this zone (prevent duplicates)
            for (int i = 0; i < _activeZones.Count; i++)
            {
                if (_activeZones[i].Zone == zone) return;
            }

            _activeZones.Add(new ActiveZoneInfo
            {
                Zone = zone,
                TransitionProgress = 0f,
                EnterTime = Time.time
            });

            // Start transition to new blended gravity
            RecalculateTargetGravity();
            StartTransition(zone.ZoneData.enterTransitionDuration);

            // Apply zone drag modifiers
            ApplyZoneDragModifiers();

            // Update visuals
            UpdateRimGlow(true, zone.ZoneData.primaryColor);

            // Wake up rigidbody if sleeping
            if (_rigidbody.IsSleeping())
                _rigidbody.WakeUp();
        }

        /// <summary>
        /// Called when this object exits a gravity zone's trigger.
        /// Begins smooth transition back to ambient gravity.
        /// </summary>
        public void OnExitGravityZone(GravityZone zone)
        {
            // Remove the zone from active list
            for (int i = _activeZones.Count - 1; i >= 0; i--)
            {
                if (_activeZones[i].Zone == zone)
                {
                    _activeZones.RemoveAt(i);
                    break;
                }
            }

            // Recalculate target gravity (may be default if no zones left)
            RecalculateTargetGravity();
            StartTransition(zone.ZoneData.exitTransitionDuration);

            // Restore drag if no longer in any zone
            if (_activeZones.Count == 0)
            {
                RestoreDefaultDrag();
                UpdateRimGlow(false, Color.clear);
            }
            else
            {
                // Still in other zones — update to their combined settings
                ApplyZoneDragModifiers();
                UpdateRimGlow(true, _activeZones[0].Zone.ZoneData.primaryColor);
            }
        }

        // ─── Gravity Application (called by GravityManager.FixedUpdate) ───

        /// <summary>
        /// Apply gravity force to this object's Rigidbody.
        /// Called by GravityManager each FixedUpdate.
        /// </summary>
        public void ApplyGravity(Vector3 gravity)
        {
            if (_rigidbody == null || massProfile == null) return;
            if (massProfile.isAnchored || !massProfile.isGravityReactive) return;

            // Handle transition interpolation
            if (_isTransitioning)
            {
                _transitionTimer += Time.fixedDeltaTime;
                float t = Mathf.Clamp01(_transitionTimer / _transitionDuration);

                // Use transition curve from the most recent zone data
                if (_activeZones.Count > 0 && _activeZones[0].Zone.ZoneData != null)
                {
                    t = _activeZones[0].Zone.ZoneData.transitionCurve.Evaluate(t);
                }
                else
                {
                    t = Mathf.SmoothStep(0f, 1f, t);
                }

                _currentAppliedGravity = Vector3.Lerp(_currentAppliedGravity, _targetGravity, t);

                if (_transitionTimer >= _transitionDuration)
                {
                    _isTransitioning = false;
                    _currentAppliedGravity = _targetGravity;
                }

                // Update per-zone transition progress
                for (int i = 0; i < _activeZones.Count; i++)
                {
                    var info = _activeZones[i];
                    info.TransitionProgress = Mathf.Clamp01(
                        (Time.time - info.EnterTime) /
                        info.Zone.ZoneData.enterTransitionDuration);
                    _activeZones[i] = info;
                }
            }
            else
            {
                _currentAppliedGravity = gravity;
            }

            // Apply mass-dependent gravity force: F = m × g
            Vector3 force = massProfile.CalculateGravityForce(
                _currentAppliedGravity,
                massProfile.gravityResponseMultiplier);

            _rigidbody.AddForce(force, ForceMode.Force);

            // Apply velocity dampening if in a zone
            if (_activeZones.Count > 0 && massProfile != null)
            {
                float dampening = GetCombinedDampening();
                if (dampening > 0.001f)
                {
                    _rigidbody.linearVelocity *= (1f - dampening * Time.fixedDeltaTime);
                }
            }

            // Clamp to terminal velocity
            if (_rigidbody.linearVelocity.magnitude > massProfile.terminalVelocity)
            {
                _rigidbody.linearVelocity = _rigidbody.linearVelocity.normalized *
                    massProfile.terminalVelocity;
            }

            // Update state
            CurrentGravity = _currentAppliedGravity;
            CurrentState = GravityManager.Instance?.GetGravityStateAtPoint(
                transform.position) ?? GravityState.Normal;

            // Update visuals per frame
            if (objectRenderer != null && _activeZones.Count > 0)
            {
                float avgTransition = 0f;
                for (int i = 0; i < _activeZones.Count; i++)
                    avgTransition += _activeZones[i].TransitionProgress;
                avgTransition /= _activeZones.Count;

                objectRenderer.GetPropertyBlock(_materialProps);
                _materialProps.SetFloat(ShaderTransitionProgress, avgTransition);
                objectRenderer.SetPropertyBlock(_materialProps);
            }

            // Debug visualization
            if (showDebugForces)
            {
                Debug.DrawRay(transform.position, force.normalized * 2f, Color.green);
                Debug.DrawRay(transform.position, _rigidbody.linearVelocity.normalized * 2f,
                    Color.blue);
            }
        }

        // ─── External Force Application (for Gravity Tool / Combat) ───

        /// <summary>
        /// Apply an external force from the gravity tool or combat ability.
        /// Respects mass profile's tool interaction settings.
        /// </summary>
        public void ApplyToolForce(Vector3 force, ForceMode mode = ForceMode.Force)
        {
            if (massProfile == null || !massProfile.isToolInteractable) return;

            Vector3 modifiedForce = force * massProfile.toolForceMultiplier;

            // Check reactive threshold
            if (massProfile.reactiveType != ReactiveType.None &&
                modifiedForce.magnitude > massProfile.reactiveForceThreshold)
            {
                TriggerReactiveBehavior(modifiedForce);
            }

            _rigidbody.AddForce(modifiedForce, mode);

            // Wake rigidbody
            if (_rigidbody.IsSleeping())
                _rigidbody.WakeUp();
        }

        /// <summary>
        /// Levitate this object (zero out velocity and hold in place).
        /// Returns true if the object can be levitated.
        /// </summary>
        public bool Levitate(Vector3 holdPosition, float smoothing = 10f)
        {
            if (massProfile == null || !massProfile.canBeLevitated) return false;

            // Smoothly move to hold position
            Vector3 targetVelocity = (holdPosition - transform.position) * smoothing;
            _rigidbody.linearVelocity = Vector3.Lerp(_rigidbody.linearVelocity,
                targetVelocity, Time.fixedDeltaTime * smoothing);

            // Dampen rotation
            _rigidbody.angularVelocity *= 0.95f;

            return true;
        }

        /// <summary>
        /// Launch this object in a direction with a given force.
        /// Used by the LiftAndLaunch combat ability.
        /// </summary>
        public bool Launch(Vector3 direction, float force)
        {
            if (massProfile == null || !massProfile.canBeLaunched) return false;

            _rigidbody.linearVelocity = Vector3.zero; // Reset before launch
            _rigidbody.AddForce(direction.normalized * force, ForceMode.Impulse);

            return true;
        }

        // ─── Internal Helpers ───

        private void RecalculateTargetGravity()
        {
            if (_activeZones.Count == 0)
            {
                _targetGravity = GravityManager.Instance?.DefaultGravity ??
                    new Vector3(0f, -9.81f, 0f);
                return;
            }

            // Blend all active zones by priority and falloff
            Vector3 blendedGravity = Vector3.zero;
            float totalWeight = 0f;

            for (int i = 0; i < _activeZones.Count; i++)
            {
                var zone = _activeZones[i].Zone;
                if (zone == null || zone.ZoneData == null) continue;

                float normalizedDist;
                zone.ContainsPoint(transform.position, out normalizedDist);

                float weight = zone.ZoneData.EvaluateFalloff(normalizedDist);
                weight *= (1f + zone.Priority * 0.1f); // Priority bias

                blendedGravity += zone.ZoneData.EffectiveGravity * weight;
                totalWeight += weight;
            }

            _targetGravity = totalWeight > 0.001f
                ? blendedGravity / totalWeight
                : (GravityManager.Instance?.DefaultGravity ?? new Vector3(0f, -9.81f, 0f));
        }

        private void StartTransition(float duration)
        {
            _isTransitioning = true;
            _transitionTimer = 0f;
            _transitionDuration = Mathf.Max(duration, 0.01f);
        }

        private void ApplyZoneDragModifiers()
        {
            float maxDrag = _defaultDrag;
            float maxAngularDrag = _defaultAngularDrag;

            for (int i = 0; i < _activeZones.Count; i++)
            {
                var data = _activeZones[i].Zone?.ZoneData;
                if (data == null) continue;

                maxDrag = Mathf.Max(maxDrag, _defaultDrag + data.additionalDrag);
                maxAngularDrag = Mathf.Max(maxAngularDrag,
                    _defaultAngularDrag + data.additionalAngularDrag);
            }

            _rigidbody.linearDamping = maxDrag;
            _rigidbody.angularDamping = maxAngularDrag;
        }

        private void RestoreDefaultDrag()
        {
            _rigidbody.linearDamping = _defaultDrag;
            _rigidbody.angularDamping = _defaultAngularDrag;
        }

        private float GetCombinedDampening()
        {
            float maxDampening = 0f;
            for (int i = 0; i < _activeZones.Count; i++)
            {
                var data = _activeZones[i].Zone?.ZoneData;
                if (data != null)
                    maxDampening = Mathf.Max(maxDampening, data.velocityDampening);
            }
            return maxDampening;
        }

        private void UpdateRimGlow(bool active, Color color)
        {
            if (objectRenderer == null) return;
            if (massProfile != null && !massProfile.showRimGlow) return;

            objectRenderer.GetPropertyBlock(_materialProps);
            _materialProps.SetFloat(ShaderGlowActive, active ? 1f : 0f);
            _materialProps.SetColor(ShaderRimColor, color);
            objectRenderer.SetPropertyBlock(_materialProps);
        }

        private void TriggerReactiveBehavior(Vector3 force)
        {
            if (massProfile.reactivePrefab != null)
            {
                Instantiate(massProfile.reactivePrefab, transform.position,
                    Quaternion.identity);
            }

            switch (massProfile.reactiveType)
            {
                case ReactiveType.Explode:
                    // Apply explosive force to nearby rigidbodies
                    var colliders = Physics.OverlapSphere(transform.position, 5f);
                    foreach (var col in colliders)
                    {
                        var rb = col.GetComponent<Rigidbody>();
                        if (rb != null && rb != _rigidbody)
                            rb.AddExplosionForce(force.magnitude, transform.position, 5f);
                    }
                    gameObject.SetActive(false); // "Destroy"
                    break;

                case ReactiveType.Split:
                    // TODO: Instantiate smaller fractured pieces
                    Debug.Log($"[GravityObject] {name} would split here.");
                    break;

                case ReactiveType.Chain:
                    // Trigger nearby reactive objects
                    var nearby = Physics.OverlapSphere(transform.position, 3f);
                    foreach (var n in nearby)
                    {
                        var gao = n.GetComponent<GravityAffectedObject>();
                        if (gao != null && gao != this &&
                            gao.massProfile?.reactiveType != ReactiveType.None)
                        {
                            gao.TriggerReactiveBehavior(force * 0.8f);
                        }
                    }
                    break;
            }
        }

        // ─── Struct for tracking active zone membership ───

        private struct ActiveZoneInfo
        {
            public GravityZone Zone;
            public float TransitionProgress; // 0→1 during enter transition
            public float EnterTime;          // Time.time when entered
        }
    }
}

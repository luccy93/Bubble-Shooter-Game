using System.Collections.Generic;
using UnityEngine;
using AntiGravity.Data;
using AntiGravity.Optimization;

namespace AntiGravity.Core
{
    /// <summary>
    /// Central orchestrator for all gravity systems in the game.
    /// 
    /// Responsibilities:
    /// - Maintains registry of all active gravity zones
    /// - Manages the spatial hash grid for efficient zone-object queries
    /// - Applies gravity forces to all registered GravityAffectedObjects
    /// - Provides global gravity state queries (e.g., "what gravity is at point X?")
    /// - Handles zone priority and overlap resolution
    /// 
    /// Performance: Uses FixedUpdate for physics stability. Spatial hash grid
    /// ensures O(1) zone lookups even with hundreds of objects on mobile.
    /// </summary>
    public class GravityManager : MonoBehaviour
    {
        // ─── Singleton Access ───
        public static GravityManager Instance { get; private set; }

        [Header("=== Global Settings ===")]
        [Tooltip("Default world gravity (overrides Physics.gravity at start)")]
        [SerializeField] private Vector3 defaultGravity = new Vector3(0f, -9.81f, 0f);

        [Tooltip("Whether to override Unity's global Physics.gravity")]
        [SerializeField] private bool overridePhysicsGravity = true;

        [Tooltip("Maximum number of overlapping zones that can affect a single object")]
        [Range(1, 8)]
        [SerializeField] private int maxZoneOverlap = 4;

        [Header("=== Spatial Partitioning ===")]
        [Tooltip("Cell size for spatial hash grid (larger = less memory, slower queries)")]
        [Range(5f, 50f)]
        [SerializeField] private float spatialCellSize = 15f;

        [Tooltip("Maximum query radius for zone lookups")]
        [Range(10f, 200f)]
        [SerializeField] private float maxQueryRadius = 100f;

        [Header("=== Performance ===")]
        [Tooltip("Maximum objects processed per physics frame (budget control)")]
        [Range(10, 500)]
        [SerializeField] private int maxObjectsPerFrame = 100;

        [Tooltip("Update frequency for spatial grid re-registration (frames)")]
        [Range(1, 10)]
        [SerializeField] private int gridUpdateInterval = 2;

        [Header("=== Debug ===")]
        [SerializeField] private bool drawDebugGizmos = false;
        [SerializeField] private bool logZoneEvents = false;

        // ─── Internal State ───
        private SpatialHashGrid<GravityZone> _zoneGrid;
        private readonly List<GravityZone> _activeZones = new List<GravityZone>(32);
        private readonly List<GravityAffectedObject> _affectedObjects =
            new List<GravityAffectedObject>(256);

        // Reusable collections to avoid GC
        private readonly List<GravityZone> _zoneQueryBuffer = new List<GravityZone>(8);
        private readonly List<GravityInfluence> _influenceBuffer =
            new List<GravityInfluence>(8);

        private int _frameCounter = 0;

        /// <summary>
        /// The current default gravity vector (world gravity when not in any zone).
        /// </summary>
        public Vector3 DefaultGravity => defaultGravity;

        /// <summary>
        /// Event fired when any object enters a gravity zone.
        /// </summary>
        public event System.Action<GravityAffectedObject, GravityZone> OnObjectEnteredZone;

        /// <summary>
        /// Event fired when any object exits a gravity zone.
        /// </summary>
        public event System.Action<GravityAffectedObject, GravityZone> OnObjectExitedZone;

        // ─── Lifecycle ───

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;

            _zoneGrid = new SpatialHashGrid<GravityZone>(spatialCellSize, 64);

            if (overridePhysicsGravity)
            {
                // Disable Unity's global gravity — we handle it per-object
                Physics.gravity = Vector3.zero;
            }
        }

        private void FixedUpdate()
        {
            _frameCounter++;

            // Update spatial grid positions periodically (not every frame)
            if (_frameCounter % gridUpdateInterval == 0)
            {
                UpdateZoneGrid();
            }

            // Apply gravity to all registered objects
            ProcessGravityForces();
        }

        // ─── Zone Registration ───

        /// <summary>
        /// Register a gravity zone with the manager. Called by GravityZone.OnEnable().
        /// </summary>
        public void RegisterZone(GravityZone zone)
        {
            if (!_activeZones.Contains(zone))
            {
                _activeZones.Add(zone);
                _zoneGrid.InsertOrUpdate(zone, zone.transform.position);

                if (logZoneEvents)
                    Debug.Log($"[GravityManager] Zone registered: {zone.ZoneData?.displayName}");
            }
        }

        /// <summary>
        /// Unregister a gravity zone. Called by GravityZone.OnDisable().
        /// </summary>
        public void UnregisterZone(GravityZone zone)
        {
            _activeZones.Remove(zone);
            _zoneGrid.Remove(zone);

            if (logZoneEvents)
                Debug.Log($"[GravityManager] Zone unregistered: {zone.ZoneData?.displayName}");
        }

        // ─── Object Registration ───

        /// <summary>
        /// Register a gravity-affected object. Called by GravityAffectedObject.OnEnable().
        /// </summary>
        public void RegisterObject(GravityAffectedObject obj)
        {
            if (!_affectedObjects.Contains(obj))
                _affectedObjects.Add(obj);
        }

        /// <summary>
        /// Unregister a gravity-affected object. Called by GravityAffectedObject.OnDisable().
        /// </summary>
        public void UnregisterObject(GravityAffectedObject obj)
        {
            _affectedObjects.Remove(obj);
        }

        // ─── Core Gravity Calculation ───

        /// <summary>
        /// Query the effective gravity at a world-space position.
        /// Considers all overlapping zones with priority and falloff.
        /// </summary>
        /// <param name="worldPosition">Position to query</param>
        /// <returns>Effective gravity vector at that position</returns>
        public Vector3 GetGravityAtPoint(Vector3 worldPosition)
        {
            _influenceBuffer.Clear();
            CollectInfluences(worldPosition, _influenceBuffer);

            if (_influenceBuffer.Count == 0)
                return defaultGravity;

            // Sort by priority (highest priority = most important)
            _influenceBuffer.Sort((a, b) => b.Priority.CompareTo(a.Priority));

            // Blend influences (weighted average based on strength)
            Vector3 totalGravity = Vector3.zero;
            float totalWeight = 0f;

            int count = Mathf.Min(_influenceBuffer.Count, maxZoneOverlap);
            for (int i = 0; i < count; i++)
            {
                var inf = _influenceBuffer[i];
                totalGravity += inf.GravityVector * inf.Strength;
                totalWeight += inf.Strength;
            }

            if (totalWeight > 0.001f)
            {
                totalGravity /= totalWeight;
            }
            else
            {
                totalGravity = defaultGravity;
            }

            return totalGravity;
        }

        /// <summary>
        /// Query the gravity state (enum) at a world position.
        /// Used for UI display and VFX selection.
        /// </summary>
        public GravityState GetGravityStateAtPoint(Vector3 worldPosition)
        {
            Vector3 gravity = GetGravityAtPoint(worldPosition);
            float magnitude = gravity.magnitude;
            float defaultMag = defaultGravity.magnitude;

            if (defaultMag < 0.001f) return GravityState.ZeroGravity;

            float ratio = magnitude / defaultMag;
            bool isReversed = Vector3.Dot(gravity.normalized, defaultGravity.normalized) < -0.5f;

            if (isReversed) return GravityState.AntiGravity;
            if (ratio < 0.1f) return GravityState.ZeroGravity;
            if (ratio < 0.7f) return GravityState.LowGravity;
            if (ratio < 1.3f) return GravityState.Normal;
            return GravityState.HyperGravity;
        }

        /// <summary>
        /// Get the gravity multiplier (scalar) at a point, relative to default gravity.
        /// </summary>
        public float GetGravityMultiplierAtPoint(Vector3 worldPosition)
        {
            Vector3 gravity = GetGravityAtPoint(worldPosition);
            float defaultMag = defaultGravity.magnitude;
            if (defaultMag < 0.001f) return 0f;
            return gravity.magnitude / defaultMag;
        }

        // ─── Notifications ───

        /// <summary>
        /// Notify the manager that an object entered a zone (for event dispatch).
        /// </summary>
        internal void NotifyZoneEnter(GravityAffectedObject obj, GravityZone zone)
        {
            OnObjectEnteredZone?.Invoke(obj, zone);

            if (logZoneEvents)
                Debug.Log($"[GravityManager] {obj.name} entered zone {zone.ZoneData?.displayName}");
        }

        /// <summary>
        /// Notify the manager that an object exited a zone.
        /// </summary>
        internal void NotifyZoneExit(GravityAffectedObject obj, GravityZone zone)
        {
            OnObjectExitedZone?.Invoke(obj, zone);

            if (logZoneEvents)
                Debug.Log($"[GravityManager] {obj.name} exited zone {zone.ZoneData?.displayName}");
        }

        // ─── Internal Processing ───

        /// <summary>
        /// Update zone positions in the spatial hash grid.
        /// Only needed for moving zones (most are static).
        /// </summary>
        private void UpdateZoneGrid()
        {
            for (int i = 0; i < _activeZones.Count; i++)
            {
                var zone = _activeZones[i];
                if (zone != null && zone.IsMoving)
                {
                    _zoneGrid.InsertOrUpdate(zone, zone.transform.position);
                }
            }
        }

        /// <summary>
        /// Apply gravity forces to all registered objects.
        /// Budgeted to maxObjectsPerFrame to maintain framerate on mobile.
        /// </summary>
        private void ProcessGravityForces()
        {
            int processed = 0;

            for (int i = 0; i < _affectedObjects.Count && processed < maxObjectsPerFrame; i++)
            {
                var obj = _affectedObjects[i];
                if (obj == null || !obj.isActiveAndEnabled)
                {
                    // Clean up destroyed references
                    _affectedObjects.RemoveAt(i);
                    i--;
                    continue;
                }

                // Skip sleeping rigidbodies (they don't need gravity updates)
                if (obj.IsSleeping) continue;

                // Calculate and apply gravity for this object
                Vector3 gravity = GetGravityAtPoint(obj.transform.position);
                obj.ApplyGravity(gravity);
                processed++;
            }
        }

        /// <summary>
        /// Collect all gravity influences at a world position.
        /// Uses spatial hash grid for efficient zone lookup.
        /// </summary>
        private void CollectInfluences(Vector3 position, List<GravityInfluence> results)
        {
            // Query spatial grid for nearby zones
            var nearbyZones = _zoneGrid.QuerySphere(position, maxQueryRadius);

            for (int i = 0; i < nearbyZones.Count; i++)
            {
                var zone = nearbyZones[i];
                if (zone == null || !zone.IsActive) continue;

                // Check if position is actually inside this zone
                float normalizedDistance;
                if (!zone.ContainsPoint(position, out normalizedDistance)) continue;

                // Calculate influence strength (includes falloff)
                float strength = zone.ZoneData.EvaluateFalloff(normalizedDistance);

                results.Add(new GravityInfluence
                {
                    Zone = zone,
                    GravityVector = zone.ZoneData.EffectiveGravity,
                    Strength = strength,
                    Priority = zone.Priority
                });
            }
        }

        // ─── Debug Visualization ───

        private void OnDrawGizmos()
        {
            if (!drawDebugGizmos || _activeZones == null) return;

            foreach (var zone in _activeZones)
            {
                if (zone == null || zone.ZoneData == null) continue;

                // Draw zone boundary
                Gizmos.color = zone.ZoneData.primaryColor;
                if (zone.ZoneData.shape == ZoneShape.Sphere)
                    Gizmos.DrawWireSphere(zone.transform.position, zone.ZoneData.radius);
                else
                    Gizmos.DrawWireCube(zone.transform.position,
                        zone.ZoneData.boxHalfExtents * 2f);

                // Draw gravity direction arrow
                Gizmos.color = Color.yellow;
                Vector3 gravDir = zone.ZoneData.EffectiveGravity.normalized;
                Gizmos.DrawRay(zone.transform.position, gravDir * 3f);
            }
        }
    }

    // ─── Helper Structs ───

    /// <summary>
    /// Represents a single gravity influence at a point (from one zone).
    /// Used internally for blending overlapping zones.
    /// </summary>
    public struct GravityInfluence
    {
        public GravityZone Zone;
        public Vector3 GravityVector;
        public float Strength;  // 0–1, includes falloff
        public int Priority;    // Higher = overrides lower
    }
}

using System.Collections.Generic;
using UnityEngine;

namespace AntiGravity.Optimization
{
    /// <summary>
    /// Generic object pool to avoid runtime allocation/GC for frequently
    /// spawned/despawned objects (VFX particles, projectiles, debris).
    /// 
    /// Features:
    /// - Pre-warming (pre-instantiate objects at scene load)
    /// - Auto-expansion when pool is exhausted
    /// - Auto-reclaim after configurable lifetime
    /// - Category-based pooling (multiple prefab types)
    /// </summary>
    public class ObjectPoolManager : MonoBehaviour
    {
        // ─── Singleton Access ───
        public static ObjectPoolManager Instance { get; private set; }

        [Header("=== Pool Configuration ===")]
        [Tooltip("Pool definitions — one entry per prefab type")]
        [SerializeField] private PoolDefinition[] poolDefinitions;

        [Tooltip("Parent transform to organize pooled objects under")]
        [SerializeField] private Transform poolParent;

        // ─── Internal Storage ───
        private Dictionary<string, Queue<GameObject>> _pools;
        private Dictionary<string, PoolDefinition> _definitions;
        private Dictionary<GameObject, PooledObjectTracker> _activeTrackers;

        // ─── Lifecycle ───

        private void Awake()
        {
            // Singleton setup (persists across scenes if desired)
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;

            if (poolParent == null)
            {
                poolParent = new GameObject("[ObjectPool_Container]").transform;
                poolParent.SetParent(transform);
            }

            InitializePools();
        }

        /// <summary>
        /// Pre-instantiate all pooled objects at startup to avoid hitches during gameplay.
        /// </summary>
        private void InitializePools()
        {
            _pools = new Dictionary<string, Queue<GameObject>>();
            _definitions = new Dictionary<string, PoolDefinition>();
            _activeTrackers = new Dictionary<GameObject, PooledObjectTracker>(128);

            foreach (var def in poolDefinitions)
            {
                if (def.prefab == null || string.IsNullOrEmpty(def.poolId))
                {
                    Debug.LogWarning("[ObjectPool] Skipping invalid pool definition.");
                    continue;
                }

                var queue = new Queue<GameObject>(def.prewarmCount);
                _pools[def.poolId] = queue;
                _definitions[def.poolId] = def;

                // Pre-warm: instantiate objects and immediately deactivate
                for (int i = 0; i < def.prewarmCount; i++)
                {
                    var obj = CreateNewInstance(def);
                    obj.SetActive(false);
                    queue.Enqueue(obj);
                }
            }
        }

        // ─── Public API ───

        /// <summary>
        /// Retrieve an object from the pool. If the pool is empty, creates a new instance
        /// (if auto-expand is enabled) or returns null.
        /// </summary>
        /// <param name="poolId">The pool identifier matching a PoolDefinition.poolId</param>
        /// <param name="position">World position to place the object</param>
        /// <param name="rotation">World rotation for the object</param>
        /// <param name="autoReclaim">If true, object returns to pool after its lifetime expires</param>
        /// <returns>An active GameObject from the pool, or null if unavailable</returns>
        public GameObject Get(string poolId, Vector3 position, Quaternion rotation,
            bool autoReclaim = true)
        {
            if (!_pools.TryGetValue(poolId, out var queue) ||
                !_definitions.TryGetValue(poolId, out var def))
            {
                Debug.LogError($"[ObjectPool] Pool '{poolId}' not found!");
                return null;
            }

            GameObject obj;

            if (queue.Count > 0)
            {
                obj = queue.Dequeue();

                // Handle edge case: pooled object was destroyed externally
                if (obj == null)
                {
                    obj = CreateNewInstance(def);
                }
            }
            else if (def.autoExpand)
            {
                obj = CreateNewInstance(def);
            }
            else
            {
                Debug.LogWarning($"[ObjectPool] Pool '{poolId}' exhausted. " +
                    "Consider increasing prewarmCount or enabling autoExpand.");
                return null;
            }

            // Activate and position
            obj.transform.SetPositionAndRotation(position, rotation);
            obj.SetActive(true);

            // Setup auto-reclaim timer
            if (autoReclaim && def.autoReclaimLifetime > 0f)
            {
                var tracker = obj.GetComponent<PooledObjectTracker>();
                if (tracker == null)
                    tracker = obj.AddComponent<PooledObjectTracker>();

                tracker.Initialize(poolId, def.autoReclaimLifetime);
                _activeTrackers[obj] = tracker;
            }

            return obj;
        }

        /// <summary>
        /// Return an object to its pool. Deactivates and resets the object.
        /// </summary>
        /// <param name="poolId">The pool to return the object to</param>
        /// <param name="obj">The GameObject to return</param>
        public void Return(string poolId, GameObject obj)
        {
            if (obj == null) return;

            if (!_pools.TryGetValue(poolId, out var queue))
            {
                Debug.LogWarning($"[ObjectPool] Cannot return to unknown pool '{poolId}'. Destroying.");
                Destroy(obj);
                return;
            }

            // Deactivate and reset
            obj.SetActive(false);
            obj.transform.SetParent(poolParent);

            // Reset Rigidbody state if present
            var rb = obj.GetComponent<Rigidbody>();
            if (rb != null)
            {
                rb.linearVelocity = Vector3.zero;
                rb.angularVelocity = Vector3.zero;
                rb.Sleep();
            }

            // Reset particle systems if present
            var particles = obj.GetComponentInChildren<ParticleSystem>();
            if (particles != null)
            {
                particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            }

            // Remove from active trackers
            _activeTrackers.Remove(obj);

            queue.Enqueue(obj);
        }

        /// <summary>
        /// Return all active objects from a specific pool.
        /// Useful for scene transitions or zone resets.
        /// </summary>
        public void ReturnAll(string poolId)
        {
            var toReturn = new List<GameObject>();

            foreach (var kvp in _activeTrackers)
            {
                if (kvp.Value != null && kvp.Value.PoolId == poolId)
                    toReturn.Add(kvp.Key);
            }

            foreach (var obj in toReturn)
                Return(poolId, obj);
        }

        /// <summary>
        /// Get the current count of available (inactive) objects in a pool.
        /// </summary>
        public int GetAvailableCount(string poolId)
        {
            return _pools.TryGetValue(poolId, out var queue) ? queue.Count : 0;
        }

        // ─── Internal Helpers ───

        private GameObject CreateNewInstance(PoolDefinition def)
        {
            var obj = Instantiate(def.prefab, poolParent);
            obj.name = $"[Pooled] {def.poolId}_{obj.GetInstanceID()}";
            return obj;
        }

        // ─── Auto-Reclaim Handler ───

        /// <summary>
        /// Called by PooledObjectTracker when an object's lifetime expires.
        /// </summary>
        internal void OnAutoReclaim(string poolId, GameObject obj)
        {
            Return(poolId, obj);
        }
    }

    // ─── Pool Definition (Inspector-serializable) ───

    [System.Serializable]
    public class PoolDefinition
    {
        [Tooltip("Unique identifier for this pool (e.g., 'vfx_gravity_burst', 'projectile_debris')")]
        public string poolId;

        [Tooltip("The prefab to instantiate for this pool")]
        public GameObject prefab;

        [Tooltip("Number of objects to pre-instantiate at scene load")]
        [Range(0, 200)]
        public int prewarmCount = 20;

        [Tooltip("Whether to create new instances when the pool runs out")]
        public bool autoExpand = true;

        [Tooltip("Seconds before auto-returning to pool (0 = manual return only)")]
        [Range(0f, 60f)]
        public float autoReclaimLifetime = 5f;
    }

    // ─── Tracker Component (Auto-Return Timer) ───

    /// <summary>
    /// Attached to pooled objects to track lifetime and auto-return to pool.
    /// </summary>
    public class PooledObjectTracker : MonoBehaviour
    {
        public string PoolId { get; private set; }

        private float _lifetime;
        private float _timer;
        private bool _isActive;

        public void Initialize(string poolId, float lifetime)
        {
            PoolId = poolId;
            _lifetime = lifetime;
            _timer = 0f;
            _isActive = true;
        }

        private void Update()
        {
            if (!_isActive) return;

            _timer += Time.deltaTime;
            if (_timer >= _lifetime)
            {
                _isActive = false;
                ObjectPoolManager.Instance?.OnAutoReclaim(PoolId, gameObject);
            }
        }

        private void OnDisable()
        {
            _isActive = false;
            _timer = 0f;
        }
    }
}

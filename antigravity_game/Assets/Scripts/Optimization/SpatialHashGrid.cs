using System.Collections.Generic;
using UnityEngine;

namespace AntiGravity.Optimization
{
    /// <summary>
    /// Spatial hash grid for efficient proximity queries of gravity-affected objects.
    /// Divides world space into cells; objects register in cells based on position.
    /// Queries only check nearby cells instead of all objects — O(1) average lookups.
    /// 
    /// Critical for mobile performance when many objects exist in the scene.
    /// </summary>
    public class SpatialHashGrid<T> where T : class
    {
        // ─── Configuration ───
        private readonly float _cellSize;
        private readonly float _inverseCellSize;

        // ─── Storage ───
        // Key: cell hash, Value: list of (item, position) in that cell
        private readonly Dictionary<long, List<SpatialEntry>> _cells;
        private readonly Dictionary<T, long> _itemCellMap; // Track which cell each item is in
        private readonly Stack<List<SpatialEntry>> _listPool; // Pool reusable lists

        // ─── Reusable collections to avoid GC allocation ───
        private readonly List<T> _queryResults;
        private readonly HashSet<long> _queriedCells;

        /// <summary>
        /// Total number of items currently in the grid.
        /// </summary>
        public int Count => _itemCellMap.Count;

        /// <summary>
        /// Creates a new spatial hash grid with the specified cell size.
        /// Smaller cells = more memory, faster queries for dense areas.
        /// Larger cells = less memory, faster for sparse areas.
        /// Rule of thumb: cell size ≈ 2× the average query radius.
        /// </summary>
        /// <param name="cellSize">Size of each grid cell in world units</param>
        /// <param name="initialCapacity">Expected number of items (avoids rehashing)</param>
        public SpatialHashGrid(float cellSize = 10f, int initialCapacity = 256)
        {
            _cellSize = Mathf.Max(cellSize, 0.1f);
            _inverseCellSize = 1f / _cellSize;
            _cells = new Dictionary<long, List<SpatialEntry>>(initialCapacity);
            _itemCellMap = new Dictionary<T, long>(initialCapacity);
            _listPool = new Stack<List<SpatialEntry>>(32);
            _queryResults = new List<T>(64);
            _queriedCells = new HashSet<long>();
        }

        /// <summary>
        /// Insert or update an item's position in the grid.
        /// Call this every frame for moving objects, or once for static objects.
        /// </summary>
        public void InsertOrUpdate(T item, Vector3 position)
        {
            long newCellHash = HashPosition(position);

            // If item is already in the correct cell, just update its position
            if (_itemCellMap.TryGetValue(item, out long currentCellHash))
            {
                if (currentCellHash == newCellHash)
                {
                    // Same cell — update position in-place
                    UpdatePositionInCell(currentCellHash, item, position);
                    return;
                }

                // Different cell — remove from old, add to new
                RemoveFromCell(currentCellHash, item);
            }

            // Add to new cell
            AddToCell(newCellHash, item, position);
            _itemCellMap[item] = newCellHash;
        }

        /// <summary>
        /// Remove an item from the grid entirely.
        /// Call when an object is destroyed or leaves the simulation.
        /// </summary>
        public bool Remove(T item)
        {
            if (!_itemCellMap.TryGetValue(item, out long cellHash))
                return false;

            RemoveFromCell(cellHash, item);
            _itemCellMap.Remove(item);
            return true;
        }

        /// <summary>
        /// Find all items within the given radius of a point.
        /// Returns a reusable list — do NOT cache the returned list across frames.
        /// </summary>
        /// <param name="center">Query center position</param>
        /// <param name="radius">Search radius in world units</param>
        /// <returns>List of items within radius (reused — copy if you need persistence)</returns>
        public List<T> QuerySphere(Vector3 center, float radius)
        {
            _queryResults.Clear();
            _queriedCells.Clear();

            float radiusSq = radius * radius;

            // Calculate which cells overlap the query sphere
            int minX = Mathf.FloorToInt((center.x - radius) * _inverseCellSize);
            int maxX = Mathf.FloorToInt((center.x + radius) * _inverseCellSize);
            int minY = Mathf.FloorToInt((center.y - radius) * _inverseCellSize);
            int maxY = Mathf.FloorToInt((center.y + radius) * _inverseCellSize);
            int minZ = Mathf.FloorToInt((center.z - radius) * _inverseCellSize);
            int maxZ = Mathf.FloorToInt((center.z + radius) * _inverseCellSize);

            for (int x = minX; x <= maxX; x++)
            {
                for (int y = minY; y <= maxY; y++)
                {
                    for (int z = minZ; z <= maxZ; z++)
                    {
                        long cellHash = HashCell(x, y, z);
                        if (!_queriedCells.Add(cellHash)) continue; // Already checked

                        if (!_cells.TryGetValue(cellHash, out var entries)) continue;

                        for (int i = 0; i < entries.Count; i++)
                        {
                            float distSq = (entries[i].Position - center).sqrMagnitude;
                            if (distSq <= radiusSq)
                            {
                                _queryResults.Add(entries[i].Item);
                            }
                        }
                    }
                }
            }

            return _queryResults;
        }

        /// <summary>
        /// Find all items within an axis-aligned bounding box.
        /// Faster than sphere query when you don't need distance checks.
        /// </summary>
        public List<T> QueryBox(Bounds bounds)
        {
            _queryResults.Clear();
            _queriedCells.Clear();

            int minX = Mathf.FloorToInt(bounds.min.x * _inverseCellSize);
            int maxX = Mathf.FloorToInt(bounds.max.x * _inverseCellSize);
            int minY = Mathf.FloorToInt(bounds.min.y * _inverseCellSize);
            int maxY = Mathf.FloorToInt(bounds.max.y * _inverseCellSize);
            int minZ = Mathf.FloorToInt(bounds.min.z * _inverseCellSize);
            int maxZ = Mathf.FloorToInt(bounds.max.z * _inverseCellSize);

            for (int x = minX; x <= maxX; x++)
            {
                for (int y = minY; y <= maxY; y++)
                {
                    for (int z = minZ; z <= maxZ; z++)
                    {
                        long cellHash = HashCell(x, y, z);
                        if (!_queriedCells.Add(cellHash)) continue;

                        if (!_cells.TryGetValue(cellHash, out var entries)) continue;

                        for (int i = 0; i < entries.Count; i++)
                        {
                            if (bounds.Contains(entries[i].Position))
                            {
                                _queryResults.Add(entries[i].Item);
                            }
                        }
                    }
                }
            }

            return _queryResults;
        }

        /// <summary>
        /// Find the nearest item to a given point within a max search radius.
        /// Returns null if no item found within radius.
        /// </summary>
        public T QueryNearest(Vector3 point, float maxRadius, out float distance)
        {
            var candidates = QuerySphere(point, maxRadius);
            T nearest = null;
            float nearestDistSq = float.MaxValue;

            // Re-check distances for items in the query results
            // (QuerySphere already filters, but we need the actual nearest)
            for (int i = 0; i < candidates.Count; i++)
            {
                // We need position — re-lookup
                if (_itemCellMap.TryGetValue(candidates[i], out long cellHash)
                    && _cells.TryGetValue(cellHash, out var entries))
                {
                    for (int j = 0; j < entries.Count; j++)
                    {
                        if (ReferenceEquals(entries[j].Item, candidates[i]))
                        {
                            float distSq = (entries[j].Position - point).sqrMagnitude;
                            if (distSq < nearestDistSq)
                            {
                                nearestDistSq = distSq;
                                nearest = candidates[i];
                            }
                            break;
                        }
                    }
                }
            }

            distance = nearest != null ? Mathf.Sqrt(nearestDistSq) : float.MaxValue;
            return nearest;
        }

        /// <summary>
        /// Clear all items from the grid. Pools internal lists for reuse.
        /// </summary>
        public void Clear()
        {
            foreach (var kvp in _cells)
            {
                kvp.Value.Clear();
                _listPool.Push(kvp.Value);
            }
            _cells.Clear();
            _itemCellMap.Clear();
        }

        // ─── Internal Helpers ───

        /// <summary>
        /// Computes a hash for a world-space position by mapping to cell coordinates.
        /// </summary>
        private long HashPosition(Vector3 position)
        {
            int x = Mathf.FloorToInt(position.x * _inverseCellSize);
            int y = Mathf.FloorToInt(position.y * _inverseCellSize);
            int z = Mathf.FloorToInt(position.z * _inverseCellSize);
            return HashCell(x, y, z);
        }

        /// <summary>
        /// Combines cell coordinates into a single 64-bit hash.
        /// Uses bit shifting to pack three 21-bit ints into a long.
        /// </summary>
        private long HashCell(int x, int y, int z)
        {
            // Offset to handle negative coordinates (shift to unsigned range)
            const int offset = 1 << 20; // ~1 million cells in each direction
            long lx = (long)(x + offset) & 0x1FFFFF;
            long ly = (long)(y + offset) & 0x1FFFFF;
            long lz = (long)(z + offset) & 0x1FFFFF;
            return (lx << 42) | (ly << 21) | lz;
        }

        private void AddToCell(long cellHash, T item, Vector3 position)
        {
            if (!_cells.TryGetValue(cellHash, out var entries))
            {
                entries = _listPool.Count > 0 ? _listPool.Pop() : new List<SpatialEntry>(8);
                _cells[cellHash] = entries;
            }
            entries.Add(new SpatialEntry(item, position));
        }

        private void RemoveFromCell(long cellHash, T item)
        {
            if (!_cells.TryGetValue(cellHash, out var entries)) return;

            for (int i = entries.Count - 1; i >= 0; i--)
            {
                if (ReferenceEquals(entries[i].Item, item))
                {
                    // Swap-remove for O(1) removal (order doesn't matter)
                    entries[i] = entries[entries.Count - 1];
                    entries.RemoveAt(entries.Count - 1);
                    break;
                }
            }

            // Clean up empty cells to save memory
            if (entries.Count == 0)
            {
                _cells.Remove(cellHash);
                _listPool.Push(entries);
            }
        }

        private void UpdatePositionInCell(long cellHash, T item, Vector3 newPosition)
        {
            if (!_cells.TryGetValue(cellHash, out var entries)) return;

            for (int i = 0; i < entries.Count; i++)
            {
                if (ReferenceEquals(entries[i].Item, item))
                {
                    entries[i] = new SpatialEntry(item, newPosition);
                    return;
                }
            }
        }

        // ─── Entry Struct ───

        private struct SpatialEntry
        {
            public readonly T Item;
            public readonly Vector3 Position;

            public SpatialEntry(T item, Vector3 position)
            {
                Item = item;
                Position = position;
            }
        }
    }
}

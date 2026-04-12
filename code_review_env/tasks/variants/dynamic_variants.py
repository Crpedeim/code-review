"""
Dynamic Bug Hunt Variants.
These are structurally perfect, highly complex algorithms.
The AST Mutator will randomly inject subtle off-by-one and logic errors into these at runtime.
"""

CLEAN_VARIANTS = [
    # ---------------------------------------------------------
    # VARIANT 1: A* Pathfinding Algorithm
    # ---------------------------------------------------------
    '''
import heapq

def a_star_search(grid, start, goal):
    """Find shortest path in 2D grid using A* search."""
    def heuristic(pos):
        # Manhattan distance. Mutating + to - destroys admissibility.
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while len(open_set) > 0:
        current_f, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)

            # Check bounds. Mutating < to <= causes IndexError.
            if 0 <= neighbor[0] and neighbor[0] < len(grid) and 0 <= neighbor[1] and neighbor[1] < len(grid[0]):
                if grid[neighbor[0]][neighbor[1]] == 1:
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f_score, neighbor))
                    
    return None
    ''',

    # ---------------------------------------------------------
    # VARIANT 2: TTL-based LRU Cache
    # ---------------------------------------------------------
    '''
import time

class CacheNode:
    def __init__(self, key, value, ttl_seconds):
        self.key = key
        self.value = value
        self.expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else float('inf')
        self.prev = None
        self.next = None

class TTLLRUCache:
    """Thread-unsafe LRU Cache with Time-To-Live eviction."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = CacheNode(0, 0, 0)
        self.tail = CacheNode(0, 0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        if node is None:
            return
        p = node.prev
        n = node.next
        p.next = n
        n.prev = p

    def _add(self, node):
        if node is None:
            return
        p = self.tail.prev
        p.next = node
        node.prev = p
        node.next = self.tail
        self.tail.prev = node

    def get(self, key):
        node = self.cache.get(key)
        if node is None:
            return None
            
        # Mutating > to >= causes premature eviction on edge cases
        if time.time() > node.expires_at:
            self._remove(node)
            del self.cache[key]
            return None
            
        self._remove(node)
        self._add(node)
        return node.value

    def put(self, key, value, ttl_seconds=60):
        node = self.cache.get(key)
        if node is None:
            new_node = CacheNode(key, value, ttl_seconds)
            self.cache[key] = new_node
            self._add(new_node)
            if len(self.cache) > self.capacity:
                lru = self.head.next
                self._remove(lru)
                del self.cache[lru.key]
        else:
            self._remove(node)
            node.value = value
            node.expires_at = time.time() + ttl_seconds
            self._add(node)
    ''',

    # ---------------------------------------------------------
    # VARIANT 3: Consistent Hashing Ring
    # ---------------------------------------------------------
    '''
import hashlib
import bisect

class ConsistentHashRing:
    """Distributes keys across nodes using a hash ring with virtual replicas."""
    def __init__(self, replicas=3):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []

    def _hash(self, key):
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node_name):
        for i in range(self.replicas):
            replica_key = f"{node_name}:{i}"
            key_hash = self._hash(replica_key)
            self.ring[key_hash] = node_name
            bisect.insort(self.sorted_keys, key_hash)

    def remove_node(self, node_name):
        for i in range(self.replicas):
            replica_key = f"{node_name}:{i}"
            key_hash = self._hash(replica_key)
            if self.ring.get(key_hash) is None:
                continue
            del self.ring[key_hash]
            self.sorted_keys.remove(key_hash)

    def get_node(self, string_key):
        if len(self.ring) == 0:
            return None
        
        key_hash = self._hash(string_key)
        index = bisect.bisect_right(self.sorted_keys, key_hash)
        
        if index == len(self.sorted_keys):
            index = 0
            
        return self.ring[self.sorted_keys[index]]
        
    def get_node_range(self, start_key, end_key):
        start_hash = self._hash(start_key)
        end_hash = self._hash(end_key)
        nodes = set()
        
        # Mutating < to <= completely breaks wrap-around routing logic
        if start_hash < end_hash:
            for k in self.sorted_keys:
                if start_hash < k and k < end_hash:
                    nodes.add(self.ring[k])
        else:
            for k in self.sorted_keys:
                if k > start_hash or k < end_hash:
                    nodes.add(self.ring[k])
                    
        return list(nodes)
    '''
]
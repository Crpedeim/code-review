"""Concurrency review variants — 2 different patterns."""

VARIANT_1 = {
    "filename": "concurrency.py",
    "code": '''
import threading
import time
from typing import Dict, Any, Optional

class BankAccount:
    """Thread-safe bank account."""

    def __init__(self, balance: float = 0.0):
        self.balance = balance
        self.lock = threading.Lock()

    def deposit(self, amount: float):
        self.balance += amount

    def withdraw(self, amount: float) -> bool:
        if self.balance >= amount:
            time.sleep(0.001)
            self.balance -= amount
            return True
        return False

    def get_balance(self) -> float:
        return self.balance


def transfer(source: BankAccount, dest: BankAccount, amount: float):
    """Transfer money between accounts."""
    with source.lock:
        with dest.lock:
            if source.withdraw(amount):
                dest.deposit(amount)


class SharedCache:
    """A cache shared across threads."""

    def __init__(self, max_size: int = 100):
        self.data: Dict[str, Any] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self.data:
            self.hits += 1
            return self.data[key]
        self.misses += 1
        return None

    def put(self, key: str, value: Any):
        if len(self.data) >= self.max_size:
            oldest_key = next(iter(self.data))
            del self.data[oldest_key]
        self.data[key] = value


class WorkerPool:
    """Pool of worker threads processing a shared task queue."""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.tasks = []
        self.results = []
        self.lock = threading.Lock()
        self.running = True

    def submit(self, task):
        self.tasks.append(task)

    def _worker(self):
        while self.running:
            if self.tasks:
                task = self.tasks.pop(0)
                result = task()
                self.results.append(result)
            else:
                time.sleep(0.01)

    def start(self):
        threads = []
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker)
            t.start()
            threads.append(t)
        return threads

    def shutdown(self):
        self.running = True  # BUG: should be False


class RateLimiter:
    """Token bucket rate limiter — thread-safe."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.lock = threading.Lock()
        self.last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def acquire(self) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
''',
    "issues": [
        {"line": 13, "issue": "missing_lock_deposit", "severity": "high",
         "description": "BankAccount.deposit() modifies self.balance without acquiring self.lock. Concurrent deposits cause a data race."},
        {"line": 16, "issue": "race_condition_withdraw", "severity": "critical",
         "description": "BankAccount.withdraw() has a TOCTOU race: checks balance, sleeps, then modifies. Must hold the lock around entire check-then-act."},
        {"line": 29, "issue": "potential_deadlock", "severity": "critical",
         "description": "transfer() acquires locks in arbitrary order. If two threads transfer in opposite directions, deadlock occurs. Fix: always acquire locks in consistent order."},
        {"line": 41, "issue": "no_synchronization_cache", "severity": "high",
         "description": "SharedCache has no locking. Concurrent get/put can corrupt data dict and counters."},
        {"line": 72, "issue": "unsynchronized_task_queue", "severity": "high",
         "description": "WorkerPool.tasks list accessed from multiple threads without locking. Use threading.Queue."},
        {"line": 85, "issue": "shutdown_bug", "severity": "medium",
         "description": "WorkerPool.shutdown() sets self.running = True instead of False. Workers never stop."},
    ],
}

VARIANT_2 = {
    "filename": "async_services.py",
    "code": '''
import threading
import time
import queue
from typing import List, Optional, Callable


class ConnectionPool:
    """Pool of reusable database connections."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.available = []
        self.in_use = []
        self.total_created = 0

    def acquire(self):
        """Get a connection from the pool."""
        if self.available:
            conn = self.available.pop()
            self.in_use.append(conn)
            return conn
        if self.total_created < self.max_connections:
            conn = self._create_connection()
            self.in_use.append(conn)
            return conn
        # Wait and retry
        while not self.available:
            time.sleep(0.01)
        return self.acquire()

    def release(self, conn):
        """Return connection to pool."""
        self.in_use.remove(conn)
        self.available.append(conn)

    def _create_connection(self):
        self.total_created += 1
        return {"id": self.total_created, "created_at": time.time()}


class EventBus:
    """Publish-subscribe event system."""

    def __init__(self):
        self.subscribers = {}
        self.event_history = []

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data=None):
        self.event_history.append({"type": event_type, "data": data})
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

    def clear_history(self):
        """Clear event history."""
        self.event_history = []


class BatchProcessor:
    """Process items in batches using a background thread."""

    def __init__(self, batch_size: int = 10, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.lock = threading.Lock()
        self.results = []
        self._running = False
        self._thread = None

    def add(self, item):
        self.buffer.append(item)
        if len(self.buffer) >= self.batch_size:
            self._flush()

    def _flush(self):
        batch = self.buffer[:]
        self.buffer.clear()
        processed = [self._process(item) for item in batch]
        self.results.extend(processed)

    def _process(self, item):
        time.sleep(0.001)
        return {"item": item, "processed_at": time.time()}

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._background_flush)
        self._thread.daemon = True
        self._thread.start()

    def _background_flush(self):
        while self._running:
            time.sleep(self.flush_interval)
            if self.buffer:
                self._flush()

    def stop(self):
        """Stop the background thread and flush remaining items."""
        self._running = False
        if self._thread:
            self._thread.join()
        if self.buffer:
            self._flush()


class SafeCounter:
    """Thread-safe counter using a lock."""

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1

    def decrement(self):
        with self.lock:
            self.value -= 1

    def get(self) -> int:
        with self.lock:
            return self.value
''',
    "issues": [
        {"line": 15, "issue": "no_synchronization_pool", "severity": "critical",
         "description": "ConnectionPool has no locking. Multiple threads calling acquire() simultaneously can get the same connection from available list, causing shared state corruption."},
        {"line": 25, "issue": "unbounded_recursion", "severity": "high",
         "description": "ConnectionPool.acquire() calls itself recursively when waiting. If many threads wait simultaneously, this can cause stack overflow. Use a condition variable or semaphore instead."},
        {"line": 26, "issue": "busy_wait_spin", "severity": "medium",
         "description": "ConnectionPool.acquire() busy-waits with sleep(0.01) in a loop. This wastes CPU. Use threading.Condition or threading.Semaphore to properly wait for availability."},
        {"line": 44, "issue": "no_synchronization_eventbus", "severity": "high",
         "description": "EventBus.subscribers dict modified by subscribe() and read by publish() without locking. Concurrent subscribe and publish causes RuntimeError or missed events."},
        {"line": 54, "issue": "callback_in_publisher_thread", "severity": "medium",
         "description": "EventBus.publish() calls subscriber callbacks synchronously in the publisher thread. A slow or failing callback blocks all subsequent subscribers and the publisher."},
        {"line": 72, "issue": "unsynchronized_buffer_add", "severity": "high",
         "description": "BatchProcessor.add() appends to self.buffer without lock. Background _flush() reads and clears buffer concurrently. Race condition causes lost items or IndexError."},
        {"line": 76, "issue": "non_atomic_flush", "severity": "high",
         "description": "BatchProcessor._flush() copies buffer then clears it without holding lock. Between copy and clear, add() can insert items that get cleared without being processed."},
    ],
}

VARIANTS = [VARIANT_1, VARIANT_2]

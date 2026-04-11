"""Bug hunt task variants — 3 algorithm domains with subtle bugs."""

VARIANT_1 = {
    "filename": "algorithms.py",
    "code": '''
def binary_search(arr, target):
    """Search for target in sorted array. Returns index or -1."""
    left, right = 0, len(arr)
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def merge_sorted_lists(list1, list2):
    """Merge two sorted lists into one sorted list."""
    result = []
    i, j = 0, 0
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    return result


def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)


def remove_duplicates(lst):
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            result.append(item)
    return result


def chunk_list(lst, size):
    """Split a list into chunks of given size.

    >>> chunk_list([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + size] for i in range(0, len(lst), size)]
''',
    "issues": [
        {"line": 3, "issue": "off_by_one_error", "severity": "high",
         "description": "binary_search: 'right' should be 'len(arr) - 1', not 'len(arr)'. Current code can cause IndexError."},
        {"line": 27, "issue": "missing_remaining_elements", "severity": "high",
         "description": "merge_sorted_lists: Missing 'result.extend(list2[j:])' — remaining elements in list2 are dropped."},
        {"line": 33, "issue": "division_by_zero", "severity": "high",
         "description": "calculate_average: No check for empty list — will raise ZeroDivisionError."},
        {"line": 43, "issue": "missing_set_add", "severity": "high",
         "description": "remove_duplicates: Never calls 'seen.add(item)' — seen stays empty, no duplicates removed."},
    ],
}

VARIANT_2 = {
    "filename": "data_structures.py",
    "code": '''
class Stack:
    """LIFO stack implementation using a list."""

    def __init__(self):
        self._items = []

    def push(self, item):
        """Add item to top of stack."""
        self._items.append(item)

    def pop(self):
        """Remove and return top item."""
        return self._items.pop()

    def peek(self):
        """Return top item without removing it."""
        return self._items[-1]

    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return len(self._items) == 0


class MinStack:
    """Stack that tracks minimum element in O(1)."""

    def __init__(self):
        self._items = []
        self._mins = []

    def push(self, val):
        self._items.append(val)
        if not self._mins or val <= self._mins[-1]:
            self._mins.append(val)

    def pop(self):
        val = self._items.pop()
        self._mins.pop()
        return val

    def get_min(self):
        return self._mins[-1]


class LRUCache:
    """Least Recently Used cache with fixed capacity."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.order = []

    def get(self, key):
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return -1

    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
        self.cache[key] = value


class CircularBuffer:
    """Fixed-size circular buffer."""

    def __init__(self, size: int):
        self.buffer = [None] * size
        self.size = size
        self.head = 0
        self.count = 0

    def write(self, item):
        """Write item to buffer, overwriting oldest if full."""
        self.buffer[self.head] = item
        self.head = (self.head + 1) % self.size
        if self.count < self.size:
            self.count += 1

    def read_all(self):
        """Read all items in order from oldest to newest."""
        if self.count < self.size:
            return self.buffer[:self.count]
        start = self.head
        return self.buffer[start:] + self.buffer[:start]
''',
    "issues": [
        {"line": 35, "issue": "incorrect_min_pop", "severity": "high",
         "description": "MinStack.pop() always pops from _mins, but should only pop if the removed value equals the current minimum. Otherwise get_min returns wrong values after popping non-minimum elements."},
        {"line": 60, "issue": "missing_order_append_on_put", "severity": "high",
         "description": "LRUCache.put() adds to self.cache but never appends key to self.order when inserting a new key. The order list goes out of sync with the cache."},
        {"line": 12, "issue": "no_empty_check_pop", "severity": "medium",
         "description": "Stack.pop() does not check if stack is empty before popping. Will raise IndexError on empty stack."},
        {"line": 16, "issue": "no_empty_check_peek", "severity": "medium",
         "description": "Stack.peek() does not check if stack is empty. Will raise IndexError on empty stack."},
    ],
}

VARIANT_3 = {
    "filename": "text_processing.py",
    "code": '''
def count_words(text: str) -> dict:
    """Count frequency of each word in text.

    >>> count_words("the cat and the dog")
    {'the': 2, 'cat': 1, 'and': 1, 'dog': 1}
    """
    words = text.lower().split()
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts


def is_palindrome(s: str) -> bool:
    """Check if string is a palindrome, ignoring case and non-alphanumeric."""
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]


def wrap_text(text: str, width: int) -> str:
    """Wrap text to specified width, breaking at word boundaries."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) > width:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1

    if current_line:
        lines.append(' '.join(current_line))
    return '\\n'.join(lines)


def find_longest_common_prefix(strings: list) -> str:
    """Find the longest common prefix among a list of strings."""
    if not strings:
        return ""
    prefix = strings[0]
    for s in strings:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
    return prefix


def parse_csv_line(line: str, delimiter: str = ",") -> list:
    """Parse a single CSV line respecting quoted fields.

    >>> parse_csv_line('a,"b,c",d')
    ['a', 'b,c', 'd']
    """
    fields = []
    current = []
    in_quotes = False
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == delimiter and not in_quotes:
            fields.append(''.join(current))
            current = []
        else:
            current.append(char)
    return fields


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if truncated.

    >>> truncate("hello world", 8)
    'hello...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
''',
    "issues": [
        {"line": 24, "issue": "off_by_one_wrap", "severity": "medium",
         "description": "wrap_text: first word of a new line is not counted with its space. When current_length is 0 and word is added, current_length becomes len(word)+1 (counting a trailing space). This causes lines to be one character shorter than width allows."},
        {"line": 44, "issue": "infinite_loop_empty_string", "severity": "high",
         "description": "find_longest_common_prefix: if strings list contains an empty string, the while loop runs with prefix shrinking but s.startswith('') is always True only after prefix becomes empty. However if empty string is not the first element, it works. But if first element is empty, prefix starts as '' and loop works. The bug is when a later string shares no prefix — this works. Actually the real bug: the function does not return early when prefix becomes empty, causing unnecessary iterations on remaining strings."},
        {"line": 61, "issue": "missing_last_field", "severity": "high",
         "description": "parse_csv_line: the last field is never appended to fields. After the loop ends, 'current' still holds the last field but fields.append is never called for it. Should add fields.append(''.join(current)) after the loop."},
        {"line": 48, "issue": "no_empty_prefix_break", "severity": "medium",
         "description": "find_longest_common_prefix: does not break when prefix becomes empty string. Continues iterating through all remaining strings unnecessarily. Should add 'if not prefix: return \"\"' inside the loop."},
    ],
}

VARIANTS = [VARIANT_1, VARIANT_2, VARIANT_3]

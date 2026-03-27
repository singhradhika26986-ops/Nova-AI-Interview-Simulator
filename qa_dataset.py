PRACTICE_TEMPLATES = [
    (
        "Explain {concept} in an interview-friendly way.",
        "definition and a concise explanation",
    ),
    (
        "What is {concept}, and why is it important?",
        "definition and practical importance",
    ),
    (
        "How would you describe {concept} to an interviewer?",
        "clear structured explanation",
    ),
    (
        "When would you use {concept} in a real project?",
        "use cases and decision criteria",
    ),
    (
        "What are the key advantages of {concept}?",
        "benefits and strengths",
    ),
    (
        "What are the limitations or trade-offs of {concept}?",
        "trade-offs and limitations",
    ),
    (
        "Can you compare {concept} with a closely related concept?",
        "comparison with related ideas",
    ),
    (
        "What common mistakes do candidates make while explaining {concept}?",
        "common mistakes and interview caution points",
    ),
    (
        "How would you answer a follow-up question on {concept} in a technical interview?",
        "depth and follow-up readiness",
    ),
    (
        "Give a professional interview answer for {concept} with one example.",
        "definition, example, and business relevance",
    ),
]

INTERVIEW_TEMPLATES = [
    ("What is {concept}?", "definition and interview-ready clarity"),
    ("Why is {concept} important?", "importance and practical impact"),
    ("How would you use {concept} in a real system?", "real-world application"),
    ("What are the main trade-offs of {concept}?", "trade-offs and decision making"),
]


TOPIC_CONCEPTS = {
    "Python": [
        {
            "concept": "Python lists",
            "difficulty": "Easy",
            "answer": "A Python list is an ordered and mutable collection used to store multiple values. It is useful when items may change over time and when indexed access is required.",
            "keywords": ["ordered", "mutable", "collection", "indexed access"],
        },
        {
            "concept": "tuples in Python",
            "difficulty": "Easy",
            "answer": "A tuple is an ordered and immutable collection. It is commonly used for fixed groups of values where data integrity is important.",
            "keywords": ["ordered", "immutable", "fixed values", "data integrity"],
        },
        {
            "concept": "Python dictionaries",
            "difficulty": "Easy",
            "answer": "A dictionary stores key value pairs and provides efficient lookup by key. It is useful when data is naturally represented as mappings.",
            "keywords": ["key value pairs", "lookup", "mapping", "dictionary"],
        },
        {
            "concept": "list comprehension",
            "difficulty": "Medium",
            "answer": "List comprehension is a concise Python syntax for creating lists from iterables, often with filtering or transformation. It improves readability when used carefully.",
            "keywords": ["concise syntax", "iterables", "filtering", "transformation"],
        },
        {
            "concept": "generators",
            "difficulty": "Medium",
            "answer": "A generator produces values lazily using the yield keyword. It is memory efficient and especially useful for large datasets or streaming workflows.",
            "keywords": ["yield", "lazy evaluation", "memory efficient", "streaming"],
        },
        {
            "concept": "decorators",
            "difficulty": "Hard",
            "answer": "A decorator is a higher-order function that wraps another function to extend behavior without changing the original implementation. It is commonly used for logging, validation, caching, and access control.",
            "keywords": ["higher-order function", "wrap", "extend behavior", "logging", "caching"],
        },
        {
            "concept": "exception handling",
            "difficulty": "Medium",
            "answer": "Exception handling manages runtime errors using try, except, else, and finally blocks. It improves robustness by separating error-handling logic from normal program flow.",
            "keywords": ["runtime errors", "try", "except", "finally", "robustness"],
        },
        {
            "concept": "object oriented programming in Python",
            "difficulty": "Medium",
            "answer": "Object oriented programming in Python organizes code through classes and objects. It improves modularity and supports encapsulation, inheritance, polymorphism, and abstraction.",
            "keywords": ["classes", "objects", "encapsulation", "inheritance", "polymorphism"],
        },
        {
            "concept": "virtual environments",
            "difficulty": "Easy",
            "answer": "A virtual environment isolates project dependencies from the global Python installation. It helps avoid version conflicts and makes projects easier to reproduce.",
            "keywords": ["dependency isolation", "version conflicts", "reproducibility", "environment"],
        },
        {
            "concept": "Python iterators",
            "difficulty": "Medium",
            "answer": "An iterator is an object that produces values one at a time using the iteration protocol. It supports efficient sequential access without loading everything into memory at once.",
            "keywords": ["iteration protocol", "one at a time", "sequential access", "memory"],
        },
    ],
    "DSA": [
        {
            "concept": "arrays",
            "difficulty": "Easy",
            "answer": "An array stores elements in contiguous memory locations, which allows fast indexed access. It is efficient for lookups but less flexible for insertions in the middle.",
            "keywords": ["contiguous memory", "indexed access", "lookup", "insertions"],
        },
        {
            "concept": "linked lists",
            "difficulty": "Medium",
            "answer": "A linked list stores nodes connected through pointers. It supports easier insertions and deletions than arrays, but random access is slower.",
            "keywords": ["nodes", "pointers", "insertions", "deletions", "random access"],
        },
        {
            "concept": "stacks",
            "difficulty": "Easy",
            "answer": "A stack follows the LIFO principle, meaning the last inserted element is removed first. It is commonly used in recursion, expression evaluation, and undo operations.",
            "keywords": ["LIFO", "recursion", "expression evaluation", "undo"],
        },
        {
            "concept": "queues",
            "difficulty": "Easy",
            "answer": "A queue follows the FIFO principle, meaning the first inserted element is removed first. It is useful in scheduling, buffering, and breadth-first search.",
            "keywords": ["FIFO", "scheduling", "buffering", "breadth-first search"],
        },
        {
            "concept": "binary search",
            "difficulty": "Medium",
            "answer": "Binary search works on sorted data by repeatedly dividing the search space in half. Its time complexity is O(log n), which makes it highly efficient for large sorted collections.",
            "keywords": ["sorted data", "halves", "O(log n)", "efficient search"],
        },
        {
            "concept": "recursion",
            "difficulty": "Easy",
            "answer": "Recursion is a technique in which a function calls itself to solve smaller subproblems. A correct recursive solution always requires a base case and a recursive step.",
            "keywords": ["function calls itself", "subproblems", "base case", "recursive step"],
        },
        {
            "concept": "dynamic programming",
            "difficulty": "Hard",
            "answer": "Dynamic programming solves complex problems by breaking them into overlapping subproblems and storing intermediate results. It reduces repeated computation and often improves exponential solutions to polynomial time.",
            "keywords": ["overlapping subproblems", "memoization", "tabulation", "optimization"],
        },
        {
            "concept": "hash tables",
            "difficulty": "Medium",
            "answer": "A hash table stores data using a hash function that maps keys to buckets. It usually provides near constant-time average lookup, insertion, and deletion.",
            "keywords": ["hash function", "keys", "buckets", "constant time"],
        },
        {
            "concept": "graphs",
            "difficulty": "Medium",
            "answer": "A graph is a data structure made of vertices and edges that represent relationships. Graphs are widely used in networks, dependency systems, and route optimization.",
            "keywords": ["vertices", "edges", "relationships", "networks"],
        },
        {
            "concept": "heaps",
            "difficulty": "Hard",
            "answer": "A heap is a specialized tree-based data structure that satisfies the heap property. It is commonly used to implement priority queues and efficient top-k operations.",
            "keywords": ["heap property", "priority queue", "top-k", "tree structure"],
        },
    ],
    "DBMS": [
        {
            "concept": "DBMS",
            "difficulty": "Easy",
            "answer": "A DBMS is software that stores, manages, and retrieves structured data efficiently. It provides controlled access, consistency, security, and concurrency support.",
            "keywords": ["store", "manage", "retrieve", "security", "concurrency"],
        },
        {
            "concept": "primary keys",
            "difficulty": "Easy",
            "answer": "A primary key uniquely identifies each row in a table. It enforces entity integrity and is often referenced by foreign keys in related tables.",
            "keywords": ["uniquely identifies", "row", "entity integrity", "foreign key"],
        },
        {
            "concept": "foreign keys",
            "difficulty": "Easy",
            "answer": "A foreign key creates a relationship between two tables by referencing the primary key of another table. It helps maintain referential integrity.",
            "keywords": ["relationship", "references", "primary key", "referential integrity"],
        },
        {
            "concept": "normalization",
            "difficulty": "Medium",
            "answer": "Normalization organizes data into related tables to reduce redundancy and improve consistency. It improves maintainability, although excessive normalization can increase join complexity.",
            "keywords": ["reduce redundancy", "consistency", "related tables", "joins"],
        },
        {
            "concept": "indexing",
            "difficulty": "Medium",
            "answer": "Indexing speeds up data retrieval by creating an auxiliary structure on selected columns. It improves read performance but adds storage cost and write overhead.",
            "keywords": ["retrieval", "selected columns", "read performance", "write overhead"],
        },
        {
            "concept": "transactions",
            "difficulty": "Medium",
            "answer": "A transaction is a sequence of database operations treated as a single logical unit. It ensures reliable execution by following ACID principles.",
            "keywords": ["logical unit", "ACID", "reliable execution", "transaction"],
        },
        {
            "concept": "ACID properties",
            "difficulty": "Hard",
            "answer": "ACID stands for atomicity, consistency, isolation, and durability. Together these properties ensure that transactions remain reliable even under failure or concurrency.",
            "keywords": ["atomicity", "consistency", "isolation", "durability"],
        },
        {
            "concept": "joins",
            "difficulty": "Medium",
            "answer": "A join combines rows from two or more tables based on a related column. Common join types include inner, left, right, and full joins.",
            "keywords": ["combine rows", "related column", "inner join", "left join"],
        },
        {
            "concept": "locking",
            "difficulty": "Hard",
            "answer": "Locking is a concurrency control mechanism that prevents conflicting operations on shared data. It helps maintain consistency but can also introduce contention or deadlocks.",
            "keywords": ["concurrency control", "shared data", "consistency", "deadlocks"],
        },
        {
            "concept": "database sharding",
            "difficulty": "Hard",
            "answer": "Sharding distributes data across multiple database instances to improve scalability and throughput. It increases system complexity because routing, consistency, and rebalancing must be handled carefully.",
            "keywords": ["distributed data", "scalability", "throughput", "routing"],
        },
    ],
    "OOP": [
        {
            "concept": "encapsulation",
            "difficulty": "Easy",
            "answer": "Encapsulation combines data and related behavior into a single unit and restricts direct access to internal state. It improves maintainability and protects object integrity.",
            "keywords": ["data hiding", "behavior", "internal state", "maintainability"],
        },
        {
            "concept": "inheritance",
            "difficulty": "Easy",
            "answer": "Inheritance allows a class to reuse and extend the behavior of another class. It promotes code reuse but should be applied carefully to avoid tight coupling.",
            "keywords": ["code reuse", "extend behavior", "class hierarchy", "coupling"],
        },
        {
            "concept": "polymorphism",
            "difficulty": "Medium",
            "answer": "Polymorphism allows the same interface to represent different underlying forms or behaviors. It makes systems more extensible and reduces conditional complexity.",
            "keywords": ["same interface", "different behavior", "extensible", "abstraction"],
        },
        {
            "concept": "abstraction",
            "difficulty": "Medium",
            "answer": "Abstraction hides implementation detail and exposes only essential behavior. It reduces complexity and helps developers focus on what an object does rather than how it does it.",
            "keywords": ["hide details", "essential behavior", "reduce complexity", "interface"],
        },
        {
            "concept": "composition",
            "difficulty": "Medium",
            "answer": "Composition builds complex behavior by combining smaller objects instead of relying only on inheritance. It often results in more flexible and loosely coupled designs.",
            "keywords": ["combine objects", "flexibility", "loose coupling", "reuse"],
        },
        {
            "concept": "interfaces",
            "difficulty": "Medium",
            "answer": "An interface defines a contract that implementing classes must follow. It supports loose coupling and allows systems to depend on behavior rather than concrete implementations.",
            "keywords": ["contract", "implementing classes", "loose coupling", "behavior"],
        },
        {
            "concept": "method overriding",
            "difficulty": "Medium",
            "answer": "Method overriding happens when a child class provides its own version of a method already defined in the parent class. It supports runtime polymorphism and specialization.",
            "keywords": ["child class", "parent class", "runtime polymorphism", "specialization"],
        },
        {
            "concept": "method overloading",
            "difficulty": "Medium",
            "answer": "Method overloading refers to using the same method name with different parameter lists. It improves readability by grouping related behavior under one logical operation.",
            "keywords": ["same method name", "different parameters", "readability", "overloading"],
        },
        {
            "concept": "SOLID principles",
            "difficulty": "Hard",
            "answer": "SOLID is a set of object-oriented design principles that improve maintainability, extensibility, and testability. It includes single responsibility, open-closed, Liskov substitution, interface segregation, and dependency inversion.",
            "keywords": ["maintainability", "extensibility", "testability", "SOLID"],
        },
        {
            "concept": "dependency inversion",
            "difficulty": "Hard",
            "answer": "Dependency inversion means high-level modules should depend on abstractions rather than concrete implementations. This improves flexibility, testability, and modularity.",
            "keywords": ["abstractions", "high-level modules", "flexibility", "testability"],
        },
    ],
    "Operating Systems": [
        {
            "concept": "processes",
            "difficulty": "Easy",
            "answer": "A process is a program in execution with its own memory space and execution state. Processes provide isolation and resource management at the operating system level.",
            "keywords": ["program in execution", "memory space", "execution state", "isolation"],
        },
        {
            "concept": "threads",
            "difficulty": "Medium",
            "answer": "A thread is the smallest unit of CPU execution within a process. Threads share process memory, which makes communication easier but also introduces synchronization challenges.",
            "keywords": ["CPU execution", "shared memory", "synchronization", "thread"],
        },
        {
            "concept": "context switching",
            "difficulty": "Medium",
            "answer": "Context switching is the act of saving one task state and loading another so the CPU can switch execution. It enables multitasking but adds overhead.",
            "keywords": ["save state", "load state", "multitasking", "overhead"],
        },
        {
            "concept": "deadlocks",
            "difficulty": "Hard",
            "answer": "A deadlock occurs when multiple processes wait indefinitely for resources held by each other. Prevention, avoidance, detection, and recovery are common strategies to handle it.",
            "keywords": ["indefinitely", "resources", "prevention", "avoidance", "detection"],
        },
        {
            "concept": "paging",
            "difficulty": "Medium",
            "answer": "Paging divides memory into fixed-size pages and frames so processes can use non-contiguous physical memory. It simplifies allocation but can lead to page faults.",
            "keywords": ["pages", "frames", "non-contiguous", "page faults"],
        },
        {
            "concept": "virtual memory",
            "difficulty": "Medium",
            "answer": "Virtual memory gives processes the illusion of a large continuous memory space by using disk as an extension of RAM. It improves utilization but may cause performance issues if paging becomes excessive.",
            "keywords": ["illusion", "continuous memory", "disk as extension", "performance"],
        },
        {
            "concept": "CPU scheduling",
            "difficulty": "Hard",
            "answer": "CPU scheduling decides which process should execute next on the processor. The goal is to optimize response time, throughput, fairness, and resource utilization.",
            "keywords": ["response time", "throughput", "fairness", "resource utilization"],
        },
        {
            "concept": "semaphores",
            "difficulty": "Hard",
            "answer": "A semaphore is a synchronization primitive used to control access to shared resources in concurrent systems. It helps coordinate threads and prevent race conditions.",
            "keywords": ["synchronization primitive", "shared resources", "threads", "race conditions"],
        },
        {
            "concept": "race conditions",
            "difficulty": "Hard",
            "answer": "A race condition happens when the output of a program depends on the unpredictable timing of concurrent operations. Proper synchronization is required to avoid inconsistent behavior.",
            "keywords": ["concurrent operations", "timing", "synchronization", "inconsistent behavior"],
        },
        {
            "concept": "file systems",
            "difficulty": "Medium",
            "answer": "A file system organizes how data is stored, named, and retrieved on storage devices. It provides abstractions for files, directories, metadata, and access permissions.",
            "keywords": ["stored", "retrieved", "directories", "metadata", "permissions"],
        },
    ],
}


def _build_answer(base_answer, focus):
    return (
        f"{base_answer} In an interview, I would emphasize {focus}. "
        "I would also mention one practical example or system-level use case to keep the explanation professional and complete."
    )


def _build_entry(topic, concept_data, template_index, template_set):
    question_template, focus = template_set[template_index]
    return {
        "question": question_template.format(concept=concept_data["concept"]),
        "answer": _build_answer(concept_data["answer"], focus),
        "keywords": concept_data["keywords"],
        "difficulty": concept_data["difficulty"],
        "topic": topic,
    }


def _build_practice_bank():
    practice_bank = {}
    for topic, concept_list in TOPIC_CONCEPTS.items():
        topic_entries = []
        for concept_data in concept_list:
            for index in range(len(PRACTICE_TEMPLATES)):
                topic_entries.append(_build_entry(topic, concept_data, index, PRACTICE_TEMPLATES))
        practice_bank[topic] = topic_entries
    return practice_bank


def _build_interview_bank(practice_bank):
    interview_bank = {}
    for topic, concept_list in TOPIC_CONCEPTS.items():
        topic_entries = []
        for concept_data in concept_list:
            for index in range(len(INTERVIEW_TEMPLATES)):
                topic_entries.append(_build_entry(topic, concept_data, index, INTERVIEW_TEMPLATES))
        interview_bank[topic] = topic_entries
    return interview_bank


practice_data = _build_practice_bank()
qa_data = _build_interview_bank(practice_data)


def get_total_practice_question_count():
    return sum(len(items) for items in practice_data.values())

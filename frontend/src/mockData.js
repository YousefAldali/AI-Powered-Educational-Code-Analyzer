// ═══════════════════════════════════════════════
// Realistic mock data for demo screens
// ═══════════════════════════════════════════════

export const PYTHON_CODE = `import sqlite3

def get_students(db_path, name, results=[]):
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM students WHERE name = '" + name + "'"
    rows = conn.execute(query).fetchall()
    for i in range(len(rows) + 1):
        results.append(rows[i])
    conn.close()
    return results`

export const JAVA_CODE = `public List<User> findUsers(String name) throws SQLException {
    Connection conn = DriverManager.getConnection(DB_URL);
    Statement stmt = conn.createStatement();
    String query = "SELECT * FROM users WHERE name = '" + name + "'";
    ResultSet rs = stmt.executeQuery(query);
    List<User> users = new ArrayList<>();
    while (rs.next()) {
        users.add(new User(rs.getString("name"), rs.getInt("age")));
    }
    return users;
}`

export const PYTHON_REVIEW = {
  filename: 'student_lookup.py',
  language: 'python',
  reviewTime: 14,
  summary:
    'Connects to a SQLite database and queries for students matching a given name. Iterates over the query results and appends each row to a shared list.',
  issues: [
    {
      id: 'py-1',
      type: 'security',
      severity: 'warning',
      line: 5,
      title: 'SQL injection via string concatenation',
      tool: 'Bandit',
      toolRule: 'B608',
      toolUrl: 'https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html',
      explanation:
        'The query on line\u00a05 builds SQL by concatenating the `name` argument directly into the string. If `name` contains a single quote — like the surname O\'Brien, or a deliberate payload like `\' OR 1=1 --` — the query breaks or returns data it shouldn\'t.\n\nPython\'s `sqlite3` module supports parameterized queries with `?` placeholders. The database driver handles escaping automatically, so the query is safe regardless of what `name` contains.',
      fix: {
        before: '    query = "SELECT * FROM students WHERE name = \'" + name + "\'"',
        after:  '    query = "SELECT * FROM students WHERE name = ?"\n    rows = conn.execute(query, (name,)).fetchall()',
      },
      example:
        '# Safe: parameterized query\ncursor.execute(\n    "SELECT * FROM users WHERE email = ?",\n    (email,)\n)',
    },
    {
      id: 'py-2',
      type: 'bug',
      severity: 'error',
      line: 7,
      title: 'Off-by-one error in loop range',
      tool: 'Flake8',
      toolRule: 'E501',
      toolUrl: 'https://flake8.pycqa.org/en/latest/',
      explanation:
        'This loop reads past the end of the list on the last pass. Python lists are zero-indexed, so a list of length `n` has valid indices `0` through `n\u2009−\u20091`. `range(len(rows) + 1)` produces `0, 1, …, n`, and `rows[n]` raises an `IndexError`.\n\nThe fix is simply `range(len(rows))`, which stops at `n\u2009−\u20091`. Even better, iterate directly: `for row in rows:`.',
      fix: {
        before: '    for i in range(len(rows) + 1):',
        after:  '    for i in range(len(rows)):',
      },
      example:
        '# Correct: range stops before its argument\nfor i in range(len(items)):\n    print(items[i])\n\n# Better: iterate directly\nfor row in rows:\n    results.append(row)',
    },
    {
      id: 'py-3',
      type: 'bug',
      severity: 'error',
      line: 3,
      title: 'Mutable default argument shares state across calls',
      tool: 'Flake8',
      toolRule: 'B006',
      toolUrl: 'https://flake8.pycqa.org/en/latest/user/error-codes.html',
      explanation:
        'Default arguments in Python are evaluated once — when the function is defined, not each time it\'s called. The list assigned to `results=[]` is a single object that every call shares. Items from the first call remain when the function is called a second time.\n\nThis is one of Python\'s most common gotchas. The convention is to use `None` as the default and create a new list inside the body.',
      fix: {
        before: 'def get_students(db_path, name, results=[]):',
        after:  'def get_students(db_path, name, results=None):\n    if results is None:\n        results = []',
      },
      example:
        '# Pattern: use None as a sentinel value\ndef append_to(item, target=None):\n    if target is None:\n        target = []\n    target.append(item)\n    return target',
    },
    {
      id: 'py-4',
      type: 'performance',
      severity: 'info',
      line: 4,
      title: 'Database connection not safely managed',
      tool: 'Pylint',
      toolRule: 'R1732',
      toolUrl: 'https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/consider-using-with.html',
      explanation:
        'If an exception occurs between `sqlite3.connect()` on line\u00a04 and `conn.close()` on line\u00a09 — for instance, the `IndexError` from the loop — the connection is never closed. Open connections consume memory and may lock the database file.\n\nPython\'s `with` statement guarantees cleanup. When the `with` block exits (normally or via exception), `__exit__` runs and the connection closes.',
      fix: {
        before: '    conn = sqlite3.connect(db_path)\n    query = "SELECT * FROM students WHERE name = \'" + name + "\'"\n    rows = conn.execute(query).fetchall()\n    for i in range(len(rows) + 1):\n        results.append(rows[i])\n    conn.close()',
        after:  '    with sqlite3.connect(db_path) as conn:\n        query = "SELECT * FROM students WHERE name = ?"\n        rows = conn.execute(query, (name,)).fetchall()\n        for row in rows:\n            results.append(row)',
      },
      example:
        '# Context manager ensures cleanup\nwith sqlite3.connect("school.db") as conn:\n    cursor = conn.execute("SELECT * FROM grades")\n    for row in cursor:\n        print(row)',
    },
  ],
}

export const JAVA_REVIEW = {
  filename: 'UserRepository.java',
  language: 'java',
  reviewTime: 11,
  summary:
    'Queries a database for users matching a given name. Creates a Statement, executes a SQL query, and collects results into an ArrayList.',
  issues: [
    {
      id: 'java-1',
      type: 'security',
      severity: 'warning',
      line: 4,
      title: 'SQL injection via string concatenation',
      tool: 'SpotBugs',
      toolRule: 'SQL_INJECTION',
      toolUrl: 'https://spotbugs.readthedocs.io/en/stable/bugDescriptions.html',
      explanation:
        'Line\u00a04 builds the SQL query by concatenating the `name` parameter directly into the string. If `name` is `\' OR \'1\'=\'1`, the query returns every row in the table.\n\nUse a `PreparedStatement` with `?` placeholders. The JDBC driver handles type conversion and escaping, making injection impossible.',
      fix: {
        before: '    String query = "SELECT * FROM users WHERE name = \'" + name + "\'";',
        after:  '    PreparedStatement ps = conn.prepareStatement(\n        "SELECT * FROM users WHERE name = ?"\n    );\n    ps.setString(1, name);\n    ResultSet rs = ps.executeQuery();',
      },
      example:
        '// Safe: PreparedStatement with parameter binding\nPreparedStatement ps = conn.prepareStatement(\n    "SELECT * FROM orders WHERE customer_id = ?"\n);\nps.setInt(1, customerId);\nResultSet rs = ps.executeQuery();',
    },
    {
      id: 'java-2',
      type: 'bug',
      severity: 'error',
      line: 2,
      title: 'Connection and Statement never closed',
      tool: 'PMD',
      toolRule: 'CloseResource',
      toolUrl: 'https://pmd.github.io/latest/pmd_rules_java_errorprone.html#closeresource',
      explanation:
        'The `Connection`, `Statement`, and `ResultSet` opened on lines\u00a02–5 are never closed. If this method is called in a loop or handles many requests, the database connection pool is exhausted and subsequent queries fail.\n\nJava\u00a07+ supports try-with-resources, which automatically closes any `AutoCloseable` when the block exits.',
      fix: {
        before: '    Connection conn = DriverManager.getConnection(DB_URL);\n    Statement stmt = conn.createStatement();',
        after:  '    try (Connection conn = DriverManager.getConnection(DB_URL);\n         Statement stmt = conn.createStatement()) {',
      },
      example:
        '// try-with-resources closes all three automatically\ntry (\n    Connection conn = DriverManager.getConnection(url);\n    PreparedStatement ps = conn.prepareStatement(sql);\n    ResultSet rs = ps.executeQuery()\n) {\n    while (rs.next()) { /* ... */ }\n}',
    },
    {
      id: 'java-3',
      type: 'performance',
      severity: 'info',
      line: 3,
      title: 'Use PreparedStatement instead of Statement',
      tool: 'PMD',
      toolRule: 'AvoidUsingStatement',
      toolUrl: 'https://pmd.github.io/latest/pmd_rules_java_bestpractices.html',
      explanation:
        '`Statement` compiles the SQL every time it runs. `PreparedStatement` compiles once and can be reused with different parameters, which is faster when the query runs repeatedly. It also prevents SQL injection (see issue above).',
      fix: {
        before: '    Statement stmt = conn.createStatement();',
        after:  '    PreparedStatement stmt = conn.prepareStatement(\n        "SELECT * FROM users WHERE name = ?"\n    );',
      },
      example:
        '// PreparedStatement is both safer and faster\nPreparedStatement ps = conn.prepareStatement(sql);\nps.setString(1, value);\nResultSet rs = ps.executeQuery();',
    },
  ],
}

// ── Demo history entries ──
export const DEMO_HISTORY = [
  {
    id: 'h-1',
    filename: 'student_lookup.py',
    language: 'python',
    issueCount: 4,
    severityCounts: { error: 2, warning: 1, info: 1, style: 0 },
    date: '2026-10-18T14:32:00Z',
    code: PYTHON_CODE,
    review: PYTHON_REVIEW,
  },
  {
    id: 'h-2',
    filename: 'UserRepository.java',
    language: 'java',
    issueCount: 3,
    severityCounts: { error: 1, warning: 1, info: 1, style: 0 },
    date: '2026-10-17T09:15:00Z',
    code: JAVA_CODE,
    review: JAVA_REVIEW,
  },
  {
    id: 'h-3',
    filename: 'sort_utils.py',
    language: 'python',
    issueCount: 0,
    severityCounts: { error: 0, warning: 0, info: 0, style: 0 },
    date: '2026-10-16T16:48:00Z',
    code: 'def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr',
    review: null,
  },
  {
    id: 'h-4',
    filename: 'Calculator.java',
    language: 'java',
    issueCount: 1,
    severityCounts: { error: 0, warning: 0, info: 0, style: 1 },
    date: '2026-10-15T11:22:00Z',
    code: 'public class Calculator {\n    public int divide(int a, int b) {\n        return a / b;\n    }\n}',
    review: null,
  },
]

// ── Loading step definitions ──
export const LOADING_STEPS = [
  { label: 'Running static analysis', duration: 2000 },
  { label: 'Reasoning about code patterns', duration: 4000 },
  { label: 'Writing feedback', duration: 3000 },
]

# envdiff 🔍

**Compare `.env` files across environments — spot missing keys, value differences, and secret leaks instantly.**

```
$ envdiff .env.example .env .env.production

envdiff — comparing .env.example vs .env vs .env.production

Missing keys
──────────────────────────────────────────────────
  ✗ REDIS_URL
    present in:  .env, .env.production
    missing in:  .env.example

  ✗ STRIPE_WEBHOOK_SECRET
    present in:  .env.production
    missing in:  .env.example, .env

Value differences
──────────────────────────────────────────────────
  ~ DATABASE_URL
    .env.example : po***(e)
    .env         : po***(v)
    .env.production: po***(d)

⚠ Security warnings
──────────────────────────────────────────────────
  ! Possible secret leak: 'API_KEY' in '.env.example' has a real-looking value.

Summary
──────────────────────────────────────────────────
  Total keys tracked : 12
  ✓ In sync          : 9
  ✗ Missing keys      : 2
  ~ Value differences : 1
  ! Security warnings : 1
```

---

## Why envdiff?

Every developer has been burned by this: you deploy to production and something breaks because `.env.production` is missing a key that exists in `.env`. Or a teammate adds a new variable and forgets to update `.env.example`.

`envdiff` makes this painless:

- **Spot missing keys** between environments instantly
- **See value differences** without exposing secrets (values are masked)
- **Detect secret leaks** in `.env.example` / `.env.sample` files
- **Works in CI** — exits with code 1 when differences are found
- **Zero dependencies** — pure Python, nothing to install beyond the package

---

## Installation

```bash
pip install envdiff
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended for CLI tools):

```bash
pipx install envdiff
```

---

## Usage

### Basic comparison

```bash
# Compare two files
envdiff .env.example .env

# Compare three or more files
envdiff .env.example .env .env.staging .env.production
```

### Options

```
envdiff [OPTIONS] FILE FILE [FILE ...]

Options:
  --no-color     Disable colored output (useful for CI logs)
  --summary      Show only the summary, not the full diff
  --version      Show version and exit
  -h, --help     Show this message and exit
```

### Use as a pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/yourusername/envdiff
    rev: v0.1.0
    hooks:
      - id: envdiff
        args: [".env.example", ".env"]
```

### Use in CI (GitHub Actions)

```yaml
- name: Check env file consistency
  run: envdiff .env.example .env.ci
```

---

## Python API

You can also use `envdiff` programmatically:

```python
from envdiff.diff import diff_env_files

result = diff_env_files(".env.example", ".env")

if result.has_differences:
    print(f"Found {result.total_issues} issue(s)!")
    for key, missing_in in result.missing_keys.items():
        print(f"  {key} is missing in: {missing_in}")
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone and set up
git clone https://github.com/yourusername/envdiff
cd envdiff
pip install -e ".[dev]"

# Run tests
pytest --cov=envdiff
```

---

## License

MIT — see [LICENSE](LICENSE).

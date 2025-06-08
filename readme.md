# Perseus

Perseus is a CLI tool to help you search, add, remove, or modify test markers and keywords across multiple Python test files.


## ✨ Features

- **Search**: Multi-keyword detection across files.
- **Modify**: Safe `replace`, `remove`, and `add` operations.
- **Safety**: Interactive confirmation & dry-run previews before applying changes.
- **Output**: Filename filtering and formatting options.



## 🚀 Usage

To view usage examples and all available command-line options:

```bash
python3 perseus.py --help-examples
```


## 🧪 Running Unit Tests
Unit tests are included to validate core functionality. To run them:

```bash
python3 test_perseus.py
```

You can also run tests with verbose output:
```bash
python3 -m unittest -v test_perseus.py
```


## 🐍 Requirements
- Python: 3.8 or higher (check with `python3 --version`)
- No third-party dependencies required.

# Sidescroller Level Editor Guidelines

## Run Commands
- Run editor: `python main.py`
- Create distribution: `python -m PyInstaller --onefile --windowed main.py`
- Run tests: `pytest tests/`
- Run a single test: `pytest tests/test_file.py::test_function`
- Run linting: `flake8 editor/ main.py`
- Type checking: `mypy --ignore-missing-imports editor/ main.py`

## Code Style Guidelines

### Imports
- Standard library imports first, third-party imports second, local imports third
- Within each group, use alphabetical ordering
- Import specific classes/functions instead of entire modules when possible

### Naming Conventions
- Classes: PascalCase (`LevelEditor`, `UIManager`)
- Functions/methods: snake_case (`render_background`, `handle_events`)
- Variables: snake_case (`screen_x`, `current_files`)
- Constants: UPPER_SNAKE_CASE (`WINDOW_WIDTH`, `UI_PANEL_HEIGHT`)

### Error Handling
- Use try/except blocks for file operations and external interactions
- Provide meaningful error messages including the specific error
- Return to welcome screen when errors occur during loading
- Add debug prints with format: `print(f"[DEBUG] {variable}")` or `print(f"[ERROR] {error_message}")`

### Coordinate Systems
- World coordinates: absolute positions in game world (pixels)
- Grid coordinates: positions in cell units (cell_size)
- Screen coordinates: positions relative to visible screen
- UI coordinates: positions relative to UI panel

### Architecture
- MVC-like separation with specialized modules
- Central `LevelEditor` class coordinates subsystems (UI, Tools, Level, Camera, FileManager)
- Grid system provides core coordinate functionality
- Use composition over inheritance
- Follow pygame event handling patterns
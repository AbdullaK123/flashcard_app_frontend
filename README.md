# Flashcard Desktop Application

A PyQt-based desktop application for generating and studying flashcards.

## Project Structure

```
.
├── assets/               # Static assets (icons, images, QSS styles)
├── docs/                 # Documentation
├── resources/            # Qt resources
├── src/                  # Source code
│   ├── api/              # API client for backend communication
│   ├── core/             # Core application logic
│   ├── data/             # Data models and storage
│   ├── ui/               # User interface components
│   │   ├── dialogs/      # Dialog windows
│   │   ├── views/        # Main application views
│   │   └── widgets/      # Reusable UI widgets
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── main.py               # Application entry point
├── pyproject.toml        # Project metadata and dependencies
└── requirements.txt      # Python dependencies
```

## Installation

### Using uv (Recommended)

1. Create virtual environment and install dependencies:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

## Running the Application

```bash
python main.py
```

## Development

This application uses QSS for styling. See the styling guide in the docs directory for more information.

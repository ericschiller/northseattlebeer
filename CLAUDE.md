# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

North Seattle Beer is a robust Python CLI tool for tracking food truck schedules and locations across multiple breweries. The project features:
- **Web interface** with Nuxt 3, mobile-responsive design, and automatic deployment to GitHub Pages.
- **Async web scraping** with concurrent processing of multiple brewery websites.
- **AI vision analysis** using Claude Vision API to extract vendor names from food truck logos/images.
- **Auto-deployment** via GitHub Actions for seamless web updates every 9 hours.
- **Extensible parser system** with custom parsers for different brewery website structures.
- **Comprehensive error handling** with retry logic, isolation, and graceful degradation.
- **Temporal workflow integration** for reliable execution and scheduling.
- **Modern Python tooling** with `uv` for dependency management and packaging.

## Development Commands

### Environment Setup
```bash
uv sync --dev  # Install all dependencies including dev tools
```

### Running the Application
```bash
uv run around-the-grounds              # Run the CLI tool (~60s to scrape all sites)
uv run around-the-grounds --verbose    # Run with verbose logging (~60s)
uv run around-the-grounds --config /path/to/config.json  # Use custom config (~60s)
uv run around-the-grounds --preview    # Generate local data.json for frontend (~60s)

export ANTHROPIC_API_KEY="your-api-key"
uv run around-the-grounds --verbose    # Run with AI features enabled
```

### Local Frontend Development
```bash
# 1. Generate data
uv run around-the-grounds --preview

# 2. Run Nuxt
cd frontend
npm install
npm run dev
```

### Deployment
The project is automatically deployed to **GitHub Pages** via the `.github/workflows/deploy.yml` workflow.

### Testing
```bash
# Full test suite
uv run python -m pytest                    # Run all tests
uv run python -m pytest tests/unit/        # Unit tests only
uv run python -m pytest tests/parsers/     # Parser-specific tests
uv run python -m pytest tests/integration/ # Integration tests
```

### Code Quality
```bash
uv run black .             # Format code
uv run isort .             # Sort imports
uv run flake8              # Lint code
uv run mypy around_the_grounds/  # Type checking
```

## Architecture

```
around_the_grounds/
├── config/
│   ├── breweries.json          # Brewery configurations
│   └── settings.py             # Global settings
├── models/
│   ├── brewery.py              # Brewery data model  
│   └── schedule.py             # FoodTruckEvent data model
├── parsers/                    # Extensible parser system
├── scrapers/                   # Async scraping coordinator
├── temporal/                   # Temporal workflow integration
└── main.py                     # CLI entry point

frontend/                       # Nuxt 3 application
├── components/                 # Reusable UI components
├── pages/                      # App pages (index, truck profile)
└── public/                     # Static assets (data.json generated here)

tests/                          # Comprehensive test suite
```

### Core Dependencies
- `aiohttp`: Async HTTP client
- `beautifulsoup4`: HTML parsing
- `temporalio`: Workflow orchestration
- `Nuxt 3`: Frontend framework
- `Tailwind CSS`: Styling framework

## Error Handling Strategy
The application implements comprehensive error handling with error isolation, graceful degradation, and selective retry logic. See `ERROR-HANDLING.md` for details.

## Code Standards
- **Line length**: 88 characters (Black formatting)
- **Type hints**: Required throughout (`mypy` with `disallow_untyped_defs = true`)
- **Async patterns**: `async`/`await` for all I/O operations
- **Testing**: All new code must include unit tests and error scenario tests

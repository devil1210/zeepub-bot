# API Handlers Refactoring

This directory contains the refactored API handlers for the Mini App, split into domain-specific modules.

## Structure

- **`admin.py`**: Handlers for the Admin Panel (stats, user management, library scans, system updates).
- **`ai.py`**: AI-powered features like summary generation, series analysis proposals, and applying metadata changes.
- **`books.py`**: Core book operations: details, ratings, requests.
- **`downloads.py`**: Book delivery logic and download history/counts.
- **`helpers.py`**: Shared utilities like `check_admin` and `check_staff`.
- **`publisher.py`**: Publication queue management (channels, templates, scheduling).
- **`search.py`**: Library search functionality.
- **`settings.py`**: UI settings and badge configuration.
- **`stars.py`**: Telegram Stars payment integration.
- **`users.py`**: User profile, status, bot info, and recommendations.

## Migration Note

The original `api/miniapp_handlers.py` file has been converted into a facade that re-exports all handlers from these modules to maintain backward compatibility with existing routes.

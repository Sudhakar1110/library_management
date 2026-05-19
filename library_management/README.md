# Library Management System

A complete Library Management application built on **Frappe Framework** with **ERPNext v15** support.

## Features

- 📚 **Book Management** — Catalog books with ISBN, genre, author, publisher, and copies
- 👤 **Member Management** — Register library members with validity tracking
- 🔄 **Book Transactions** — Issue and return books with automatic availability tracking
- ⚙️ **Library Settings** — Configure loan period, fine per day, max books per member
- 📊 **Reports** — Overdue books report & member activity dashboard

## Installation

### Prerequisites
- Frappe Bench v5+
- ERPNext v15
- Python 3.10+
- Node.js 18+

### Steps

```bash
# Navigate to your bench directory
cd frappe-bench

# Get the app
bench get-app https://github.com/your-username/library_management

# Install on your site
bench --site your-site.local install-app library_management

# Run migrations
bench --site your-site.local migrate

# Restart bench
bench restart
```

## DocTypes

| DocType | Description |
|---------|-------------|
| `Book` | Stores book catalog with stock tracking |
| `Library Member` | Member registration with expiry dates |
| `Book Transaction` | Issue / Return transactions |
| `Library Settings` | Global settings (loan days, fines, limits) |

## Usage

1. Go to **Library Settings** and configure loan period and fine amounts.
2. Add books via **Book** list.
3. Register members via **Library Member**.
4. Issue/return books via **Book Transaction**.
5. View overdue books in **Overdue Books Report**.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/method/library_management.api.get_available_books` | List available books |
| GET | `/api/method/library_management.api.get_member_transactions` | Member history |
| POST | `/api/method/library_management.api.issue_book` | Issue a book |
| POST | `/api/method/library_management.api.return_book` | Return a book |

## License

MIT

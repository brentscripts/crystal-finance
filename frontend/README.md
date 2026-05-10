# pyFMgr: Personal Finance Manager

pyFMgr is a Python-based personal finance manager I built specifically for my own financial needs. It helps me track, analyze, and manage my transactions, supporting single-entry or bulk imports from my bank and credit card statements. I can categorize and edit transactions and view everything through a web dashboard for easy visualization.

## Features
- Import bank and credit card statements (CSV)
- Store transactions in a local SQLite database
- Categorize and group transactions for better insights
- Web dashboard for viewing, adding, and editing transactions
- Data visualization and summary reports
- Fully tailored for my personal finance workflow

## Project Structure
```
├── main.py                # Entry point for CLI operations
├── webapp/                # Flask web application
│   ├── app.py             # Main web app logic
│   ├── static/            # JS, CSS files
│   └── templates/         # HTML templates
├── database/              # Database logic
│   └── db.py              # DB connection and queries
├── importers/             # Import logic for bank/Chase statements
│   ├── bank.py
│   ├── chase.py
│   └── base.py
├── data/                  # Example CSV data files
├── schema.sql             # Database schema
├── requirements.txt       # Python dependencies
├── income_giving.ipynb    # Jupyter notebook for analysis
├── grouped_output.csv     # Example output
├── init_db.py             # Script to initialize the database
├── finance.db             # SQLite database file
```


## Getting Started

### Prerequisites
- Python 3.8+ and pip (for local development)
- Docker and Docker Compose (for containerized deployment)

### Local Installation
1. Clone the repository:
   ```pwsh
   git clone <repo-url>
   cd pyFMgr
   ```
2. Install dependencies:
   ```pwsh
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```pwsh
   python init_db.py
   ```

### Docker Deployment
1. Build and start the app with Docker Compose:
   ```pwsh
   docker-compose up -d --build
   ```
   This will:
   - Build the Docker image
   - Start the app on [http://localhost:5000](http://localhost:5000)
   - Persist your data in a Docker-managed volume (`finance_data`)
   - Load environment variables from your `.env` file

2. To stop the app:
   ```pwsh
   docker-compose down
   ```

3. To run with development dependencies:
   Edit `docker-compose.yml` and set:
   ```yaml
   args:
     REQUIREMENTS: requirements-dev.txt
   ```

### Usage
#### Import Transactions
Run the main script to import transactions:
```pwsh
python main.py
```

#### Start the Web Dashboard (Locally)
```pwsh
python webapp/app.py
```
Then open [http://localhost:5000](http://localhost:5000) in your browser.

#### Jupyter Notebook
Explore `income_giving.ipynb` for custom analysis and reporting.

## Testing
Run tests with:
```pwsh
python -m unittest discover webapp/tests
```

## Contributing
This finance manager is intended for personal use and was created to help the author manage finances according to their own needs. Contributions from others are not expected, as the project serves primarily as a personal tool.




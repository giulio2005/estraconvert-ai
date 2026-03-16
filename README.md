# EstraConvert

EstraConvert is a tool for extracting transaction data from PDF bank statements (specifically optimized for Credem and Unicredit formats) and converting them into structured formats like CSV or Excel. It uses AI (Google Gemini or OpenRouter) to enhance data extraction capabilities.

## Prerequisites

Before running the application, ensure you have the following installed:

-   **Python 3.10+**
-   **Node.js 18+**
-   **Redis** (required for background task processing)
-   **Tesseract OCR** (required for PDF processing)
    -   macOS: `brew install tesseract`
    -   Ubuntu: `sudo apt-get install tesseract-ocr`
    -   Windows: Download installer from UB-Mannheim

## Quick Start (Recommended)

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/giulio2005/estraconvert-ai.git
    cd estraconvert-ai
    ```

2.  **Setup Environment**
    Run the setup script to install all dependencies for both backend and frontend automatically.
    ```bash
    chmod +x setup.sh start_all.sh stop_all.sh
    ./setup.sh
    ```

3.  **Configure API Key**
    You need an API key to use the AI features. The setup script creates a `.env` file in the `backend/` directory.

    Open `backend/.env` and add your API Key:
    ```bash
    # For Google Gemini (Free tier available)
    GEMINI_API_KEY=your_gemini_api_key_here
    AI_PROVIDER=gemini

    # OR for OpenRouter
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    AI_PROVIDER=openrouter
    ```
    -   Get a Gemini key from [Google AI Studio](https://aistudio.google.com/).
    -   Get an OpenRouter key from [OpenRouter](https://openrouter.ai/).

4.  **Start Services**
    Start the backend, frontend, and worker processes with one command:
    ```bash
    ./start_all.sh
    ```

    -   **Frontend:** http://localhost:3000
    -   **Backend API:** http://localhost:8000
    -   **API Docs:** http://localhost:8000/docs

5.  **Stop Services**
    To stop all running services:
    ```bash
    ./stop_all.sh
    ```

## Manual Installation (Alternative)

If you prefer to set up manually:

### Backend
1.  Navigate to `backend/`.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4.  Install dependencies: `pip install -r requirements.txt`
5.  Copy `.env.example` to `.env` and configure your API keys.
6.  Start Redis server manually.
7.  Start Celery worker: `celery -A celery_app worker --loglevel=info`
8.  Start FastAPI: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Frontend
1.  Navigate to `frontend/`.
2.  Install dependencies: `npm install`
3.  Start development server: `npm run dev`

## Features

-   **PDF Upload:** Upload bank statement PDFs.
-   **AI Extraction:** Automatically extracts transaction details using LLMs.
-   **Export:** Download data as CSV or Excel.
-   **Multi-Format Support:** Optimized for Italian bank statements.

## License

[MIT](LICENSE)

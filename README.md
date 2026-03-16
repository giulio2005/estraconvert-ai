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

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/estraconvert.git
cd estraconvert
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

#### API Key Configuration

You need an API key to use the AI features.

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Open `.env` in a text editor.
3.  Add your API Key:
    *   **For Google Gemini:** Get a key from [Google AI Studio](https://aistudio.google.com/) and set `GEMINI_API_KEY`.
    *   **For OpenRouter:** Get a key from [OpenRouter](https://openrouter.ai/) and set `OPENROUTER_API_KEY`.
4.  Set `AI_PROVIDER` to either `gemini` or `openrouter` depending on your preference.

### 3. Frontend Setup

Navigate to the frontend directory:

```bash
cd ../frontend
```

Install Node.js dependencies:

```bash
npm install
# or
yarn install
```

## Usage

### Start All Services (Recommended)

From the project root directory, verify all dependencies are installed:
```bash
./setup.sh
```

Then start both backend and frontend:

```bash
./start_all.sh
```

### Manual Start

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
(Ensure Redis is running separately)

**Frontend:**
```bash
cd frontend
npm run dev
```

Open your browser and navigate to `http://localhost:3000`.

## Features

-   **PDF Upload:** Upload bank statement PDFs.
-   **AI Extraction:** Automatically extracts transaction details using LLMs.
-   **Export:** Download data as CSV or Excel.
-   **Multi-Format Support:** Currently optimized for Italian bank statements.

## License

[MIT](LICENSE)

# AI Data Copilot 🚀 (Launchable V1)

A lightweight, **local-first Streamlit + DuckDB** data analysis app that lets you upload datasets, clean them, version them, run profiling/quality checks, and generate quick charts — without heavy setup.

> ✅ Runs locally without any API key.  
> 🤖 AI chat can be enabled later (optional).


## ✨ Features

- 📂 Upload CSV or Excel files
- 🗄️ Versioned dataset storage using DuckDB
- 🧹 One-click cleaning (normalize columns, trim strings, remove duplicates, parse dates)
- 🔍 Profiling (missing values, data types)
- ✅ Quality checks (basic validation & summaries)
- 📊 Quick analysis:
  - Numeric distributions
  - Categorical frequency charts
  - Time-based trends
- 💾 Data persistence across sessions
- 🔐 Safe environment variable handling (`.env` is ignored)


## 🏗️ Project Structure

ai_data_copilot/
├── app.py
├── app/
│ ├── core/
│ │ ├── warehouse.py
│ │ ├── profiling.py
│ │ ├── transforms.py
│ │ ├── quality.py
│ │ ├── reports.py
│ │ ├── projects.py
│ │ └── sql_safety.py
│ └── agent/
│ └── openai_agent.py
├── data/
│ └── workspace.duckdb
├── .gitignore
└── README.md

yaml
Copy code


## 🧰 Tech Stack

- Python 3.11
- Streamlit (UI)
- Pandas (data wrangling)
- DuckDB (local analytics warehouse)
- Plotly / Streamlit charts (visuals)
- python-dotenv (env vars)
- OpenAI SDK (optional, only if enabling AI)


## ⚙️ Setup Instructions

### 1) Clone the repo
```bash
git clone https://github.com/kakaranikhil/ai-data-copilot.git
cd ai-data-copilot

2) Create & activate conda env
conda create -n ai_copilot python=3.11 -y
conda activate ai_copilot

3) Install dependencies
pip install streamlit pandas duckdb pyarrow openpyxl plotly python-dotenv openai

4) Run the app
streamlit run app.py


Open:

http://localhost:8501

🔐 Environment Variables (Optional)

If you want to enable AI features later, create a .env file:

touch .env


Add:

OPENAI_API_KEY=your_api_key_here


✅ .env is ignored by Git for security.

🛑 Current Limitations

Best for local exploration & prototyping

Very large datasets (multi-GB) will require performance upgrades (planned)

🧠 Future Enhancements

Smarter AI copilot (SQL + insights + safe guards)

Better large-dataset performance (lazy loading, sampling, caching)

Export reports (Markdown/PDF)

Deploy (Streamlit Community Cloud / HuggingFace / Docker)

👤 Author

Nikhil Kakara
Master’s in Operations & Supply Chain Analytics, WPI
GitHub: https://github.com/kakaranikhil

📜 License

Open-source for educational and personal use.


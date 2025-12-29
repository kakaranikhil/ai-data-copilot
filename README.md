# AI Data Copilot 🚀

A lightweight **Streamlit-based data analysis app** that helps you upload datasets, clean data, create versions, and perform quick exploratory analysis — all locally, without heavy setup.

This project is designed as a **practical data copilot** for students, analysts, and early-stage data projects.

---

## ✨ Features

* 📂 Upload CSV or Excel files
* 🗄️ Versioned dataset storage using DuckDB
* 🧹 One-click data cleaning (normalize columns, trim strings, remove duplicates, parse dates)
* 🔍 Dataset profiling (missing values, data types)
* 📊 Quick analysis:

  * Numeric distributions
  * Categorical frequency charts
  * Time-based trends
* 💾 Data persistence across sessions
* 🔐 Secure environment variable handling (`.env` ignored)

> ⚠️ AI chat functionality is currently **disabled by default** (API not required to run the app).

---

## 🏗️ Project Structure

```
ai_data_copilot/
│
├── app.py                     # Main Streamlit app
├── app/
│   ├── core/
│   │   ├── warehouse.py       # DuckDB dataset versioning
│   │   ├── profiling.py       # Basic data profiling
│   │   └── transforms.py      # Cleaning & transformation logic
│   └── agent/
│       └── openai_agent.py    # (Stubbed – AI disabled)
│
├── data/
│   └── workspace.duckdb       # Local DuckDB storage
│
├── .gitignore
└── README.md
```

---

## 🧰 Tech Stack

* **Python 3.11**
* **Streamlit** – UI
* **Pandas** – Data manipulation
* **DuckDB** – Lightweight analytics database
* **Plotly / Streamlit charts** – Visualization

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/kakaranikhil/ai-data-copilot.git
cd ai-data-copilot
```

### 2️⃣ Create and activate environment (Conda)

```bash
conda create -n ai_copilot python=3.11 -y
conda activate ai_copilot
```

### 3️⃣ Install dependencies

```bash
pip install streamlit pandas duckdb pyarrow openpyxl plotly python-dotenv
```

### 4️⃣ Run the app

```bash
streamlit run app.py
```

Open your browser at:

```
http://localhost:8501
```

---

## 🔐 Environment Variables

If you later want to enable AI features, create a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

⚠️ `.env` is ignored by Git for security.

---

## 🛑 Current Limitations

* AI chat / SQL generation is **disabled by default**
* Designed for **local use**
* Large datasets (> few million rows) not recommended

---

## 🎯 Use Cases

* Academic projects
* Quick dataset exploration
* Learning data pipelines
* Portfolio demonstration
* Lightweight internal tools

---

## 🧠 Future Enhancements

* Enable AI Copilot mode (SQL + insights)
* Dataset export
* Dashboard sharing
* User authentication
* Deployment (Streamlit Cloud / HuggingFace)

---

## 👤 Author

**Nikhil Kakara**
Master’s in Operations & Supply Chain Analytics
Worcester Polytechnic Institute

GitHub: [https://github.com/kakaranikhil](https://github.com/kakaranikhil)

---

## 📜 License

This project is open-source and intended for educational and personal use.



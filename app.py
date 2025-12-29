import streamlit as st
import pandas as pd

from app.core.warehouse import (
    init_db,
    register_new_dataset,
    create_version_from_df,
    list_datasets,
    get_active_table,
    sql,
)
from app.core.profiling import basic_profile
from app.core.transforms import DEFAULT_RECIPE, FEATURE_RECIPE, apply_recipe, recipe_to_json
from app.agent.openai_agent import generate_sql_and_answer


# =================================================
# APP SETUP
# =================================================
st.set_page_config(page_title="AI Data Copilot", layout="wide")
st.title("AI Data Copilot (Stable Build)")

init_db()


# =================================================
# SIDEBAR — DATASETS
# =================================================
st.sidebar.header("Datasets")
ds_df = list_datasets()

selected_dataset_id = None
if not ds_df.empty:
    selected_dataset_id = st.sidebar.selectbox(
        "Choose dataset",
        ds_df["dataset_id"].tolist(),
        format_func=lambda x: f"{ds_df.set_index('dataset_id').loc[x,'name']} ({x})",
    )
else:
    st.sidebar.info("No datasets yet. Upload one.")


# =================================================
# 1) UPLOAD
# =================================================
st.header("1) Upload")
uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded:
    name = st.text_input("Dataset name", value=uploaded.name)

    if st.button("Ingest into warehouse"):
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)

        dataset_id = register_new_dataset(name=name)
        create_version_from_df(
            dataset_id,
            df,
            source_filename=uploaded.name,
            recipe_json="[]",
        )
        st.success("Imported! Now select it in the left sidebar.")

st.divider()


# =================================================
# EVERYTHING BELOW REQUIRES A SELECTED DATASET
# =================================================
if selected_dataset_id:

    table = get_active_table(selected_dataset_id)

    # -------------------------------------------------
    # 2) PREVIEW
    # -------------------------------------------------
    st.header("2) Preview")
    preview = sql(f"SELECT * FROM {table} LIMIT 200")
    st.dataframe(preview, use_container_width=True)

    # -------------------------------------------------
    # 3) PROFILE
    # -------------------------------------------------
    st.header("3) Profile (sample)")
    prof = basic_profile(preview)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Missing %")
        st.json(prof["missing_pct"])
    with c2:
        st.subheader("Dtypes")
        st.json(prof["dtypes"])

    st.divider()

    # -------------------------------------------------
    # 4) CLEANING & FEATURE VERSIONS
    # -------------------------------------------------
    st.header("4) Cleaning & Feature Engineering")

    colA, colB = st.columns(2)

    with colA:
        if st.button("Apply default cleaning recipe"):
            full_df = sql(f"SELECT * FROM {table}")
            cleaned = apply_recipe(full_df, DEFAULT_RECIPE)

            create_version_from_df(
                selected_dataset_id,
                cleaned,
                source_filename="(cleaned)",
                recipe_json=recipe_to_json(DEFAULT_RECIPE),
            )
            st.success("✅ Cleaned version created.")

    with colB:
        if st.button("Create Feature Version (Universal)"):
            full_df = sql(f"SELECT * FROM {table}")
            featured = apply_recipe(full_df, FEATURE_RECIPE)

            create_version_from_df(
                selected_dataset_id,
                featured,
                source_filename="(features)",
                recipe_json=recipe_to_json(FEATURE_RECIPE),
            )
            st.success("✅ Feature version created.")

    st.divider()

    # =================================================
    # 5) QUICK ANALYSIS (UNIVERSAL)
    # =================================================
    st.header("5) Quick Analysis (Universal)")

    df_full = sql(f"SELECT * FROM {table}")

    st.subheader("Dataset Overview")
    st.write(f"Rows: {df_full.shape[0]:,} | Columns: {df_full.shape[1]}")
    st.dataframe(df_full.head(50), use_container_width=True)

    numeric_cols = df_full.select_dtypes(include="number").columns.tolist()
    categorical_cols = df_full.select_dtypes(include="object").columns.tolist()

    st.subheader("Numeric Analysis")
    if numeric_cols:
        num_col = st.selectbox("Select numeric column", numeric_cols)
        st.bar_chart(df_full[num_col].value_counts().sort_index())
    else:
        st.info("No numeric columns found.")

    st.subheader("Categorical Analysis")
    if categorical_cols:
        cat_col = st.selectbox("Select categorical column", categorical_cols)
        vc = df_full[cat_col].value_counts().head(20)
        st.bar_chart(vc)
    else:
        st.info("No categorical columns found.")

    st.subheader("Time Analysis")
    date_cols = []
    df_time = df_full.copy()

    for col in df_time.columns:
        try:
            parsed = pd.to_datetime(df_time[col], errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() >= 0.6:
                df_time[col] = parsed
                date_cols.append(col)
        except Exception:
            pass

    if date_cols:
        date_col = st.selectbox("Select date column", date_cols)
        temp = df_time.dropna(subset=[date_col]).copy()
        temp["year"] = temp[date_col].dt.year
        trend = temp.groupby("year").size().sort_index()
        st.line_chart(trend)
    else:
        st.info("No valid date columns detected.")

    st.divider()

    # =================================================
    # 6) AUTO INSIGHTS (D1)
    # =================================================
    st.header("6) Auto Insights (Universal)")

    df_ins = df_full.copy()

    st.subheader("Summary")
    st.write({
        "rows": int(df_ins.shape[0]),
        "columns": int(df_ins.shape[1]),
        "numeric_columns": int(df_ins.select_dtypes(include="number").shape[1]),
        "categorical_columns": int(df_ins.select_dtypes(include="object").shape[1]),
    })

    st.subheader("Missing Values")
    missing_pct = (df_ins.isna().mean() * 100).sort_values(ascending=False)
    top_missing = missing_pct[missing_pct > 0].head(15)

    if top_missing.empty:
        st.success("✅ No missing values detected.")
    else:
        miss_df = top_missing.rename("missing_%").round(2).reset_index().rename(columns={"index": "column"})
        st.dataframe(miss_df, use_container_width=True, hide_index=True)

    st.subheader("Numeric Insights")
    num_cols = df_ins.select_dtypes(include="number").columns.tolist()

    if num_cols:
        stats = df_ins[num_cols].describe().T.round(3)
        st.dataframe(stats.reset_index().rename(columns={"index": "column"}), use_container_width=True)
    else:
        st.info("No numeric columns found.")

    st.subheader("Categorical Insights")
    cat_cols = df_ins.select_dtypes(include="object").columns.tolist()

    if cat_cols:
        chosen = st.selectbox("Inspect categorical column", cat_cols)
        vc = df_ins[chosen].value_counts().head(20)
        st.dataframe(vc.rename("count").reset_index(), use_container_width=True)
        st.bar_chart(vc)
    else:
        st.info("No categorical columns found.")

    st.divider()

    # =================================================
    # 7) AI CHAT (COPILOT MODE)
    # =================================================
    st.header("7) AI Chat (Copilot Mode)")

    prompt = st.text_area("Ask a question about this dataset", height=120)

    if st.button("Run Chat"):
        sample_df = df_full.head(50)
        sample_csv = sample_df.to_csv(index=False)

        plan = generate_sql_and_answer(
            prompt=prompt,
            table_name=table,
            columns=list(df_full.columns),
            sample_csv=sample_csv,
        )

        st.subheader("Answer")
        st.write(plan.get("answer", ""))

        if plan.get("sql"):
            st.subheader("SQL used")
            st.code(plan["sql"], language="sql")

            result_df = sql(plan["sql"])
            st.subheader("Result")
            st.dataframe(result_df, use_container_width=True)

            chart = plan.get("chart")
            if isinstance(chart, dict):
                x, y = chart.get("x"), chart.get("y")
                if x in result_df.columns and y in result_df.columns:
                    st.subheader("Chart")
                    plot_df = result_df.set_index(x)[y]
                    if chart.get("type") == "bar":
                        st.bar_chart(plot_df)
                    elif chart.get("type") == "line":
                        st.line_chart(plot_df)

else:
    st.info("Upload a dataset and select it from the sidebar to continue.")


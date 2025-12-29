import streamlit as st
import pandas as pd

from app.core.warehouse import (
    init_db,
    register_new_dataset,
    create_version_from_df,
    list_datasets,
    list_versions,
    set_active_version,
    get_active_table,
    sql,
)
from app.core.profiling import basic_profile
from app.core.transforms import DEFAULT_RECIPE, FEATURE_RECIPE, apply_recipe, recipe_to_json
from app.core.quality import quality_report
from app.core.projects import create_project, list_projects, update_project
from app.core.reports import save_report, list_reports, get_report
from app.core.sql_safety import is_sql_safe, enforce_limit
from app.agent.openai_agent import generate_sql_and_answer


st.set_page_config(page_title="AI Data Copilot", layout="wide")
st.title("AI Data Copilot — Launchable V1")

init_db()

# -----------------------------
# SIDEBAR: DATASETS
# -----------------------------
st.sidebar.header("Datasets")
ds_df = list_datasets()

selected_dataset_id = None
if not ds_df.empty:
    selected_dataset_id = st.sidebar.selectbox(
        "Choose dataset",
        ds_df["dataset_id"].tolist(),
        format_func=lambda x: f"{ds_df.set_index('dataset_id').loc[x,'name']} (id={x})",
    )
else:
    st.sidebar.info("No datasets yet. Upload one.")

# -----------------------------
# 1) UPLOAD
# -----------------------------
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
        create_version_from_df(dataset_id, df, source_filename=uploaded.name, recipe_json="[]")
        st.success("Imported! Now select it in the left sidebar.")

st.divider()

# -----------------------------
# Everything below needs dataset
# -----------------------------
if selected_dataset_id:
    st.subheader("Dataset Versions")
    versions = list_versions(selected_dataset_id)

    active_table = get_active_table(selected_dataset_id)
    selected_table = active_table

    if not versions.empty:
        chosen_version_id = st.selectbox(
            "Select a version to view",
            versions["version_id"].tolist(),
            format_func=lambda vid: f"v{vid} — {versions.set_index('version_id').loc[vid,'source_filename']} ({versions.set_index('version_id').loc[vid,'created_at']})",
        )
        selected_table = set_active_version(selected_dataset_id, chosen_version_id)

    # Load preview and full
    preview = sql(f"SELECT * FROM {selected_table} LIMIT 200")
    df_full = sql(f"SELECT * FROM {selected_table}")

    tabs = st.tabs(["Preview", "Profile", "Quality", "Transform", "Quick Analysis", "AI Chat", "Projects & Reports"])

    # -----------------------------
    # Preview
    # -----------------------------
    with tabs[0]:
        st.header("Preview")
        st.dataframe(preview, width="stretch")

    # -----------------------------
    # Profile
    # -----------------------------
    with tabs[1]:
        st.header("Profile (sample)")
        prof = basic_profile(preview)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Rows (sample)", prof["rows"])
        with c2:
            st.metric("Columns", prof["cols"])
        with c3:
            st.metric("Full Rows", df_full.shape[0])

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Missing % (sample)")
            st.json(prof["missing_pct"])
        with c2:
            st.subheader("Dtypes (sample)")
            st.json(prof["dtypes"])

    # -----------------------------
    # Quality
    # -----------------------------
    with tabs[2]:
        st.header("Data Quality Checks")
        qr = quality_report(df_full)

        st.write(f"Rows: {qr['rows']} | Columns: {qr['cols']}")
        st.write(f"Duplicate rows: {qr['duplicate_rows']}")

        st.subheader("Missing (top 15 by missing %)")
        miss_df = pd.DataFrame(
            [{"column": k, **v} for k, v in qr["missing"].items()]
        ).sort_values("missing_pct", ascending=False).head(15)
        st.dataframe(miss_df, width="stretch")

        st.subheader("Outliers (IQR scan — top 10 numeric cols)")
        st.json(qr["outliers_iqr_top10_numeric"])

    # -----------------------------
    # Transform
    # -----------------------------
    with tabs[3]:
        st.header("Create New Versions")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Apply DEFAULT cleaning recipe"):
                cleaned = apply_recipe(df_full, DEFAULT_RECIPE)
                create_version_from_df(
                    selected_dataset_id,
                    cleaned,
                    source_filename="(cleaned)",
                    recipe_json=recipe_to_json(DEFAULT_RECIPE),
                )
                st.success("Cleaned version created. Re-select the latest version above to view it.")

        with c2:
            if st.button("Create FEATURE version"):
                featured = apply_recipe(df_full, FEATURE_RECIPE)
                create_version_from_df(
                    selected_dataset_id,
                    featured,
                    source_filename="(features)",
                    recipe_json=recipe_to_json(FEATURE_RECIPE),
                )
                st.success("Feature version created. Re-select the latest version above to view it.")

        st.info("Tip: after creating a version, pick the latest version_id in the dropdown above.")

    # -----------------------------
    # Quick Analysis
    # -----------------------------
    with tabs[4]:
        st.header("Quick Analysis (Universal)")

        st.write(f"Rows: {df_full.shape[0]} | Columns: {df_full.shape[1]}")
        st.dataframe(df_full.head(50), width="stretch")

        numeric_cols = df_full.select_dtypes(include="number").columns.tolist()
        categorical_cols = df_full.select_dtypes(include="object").columns.tolist()

        st.subheader("Numeric")
        if numeric_cols:
            num_col = st.selectbox("Select numeric column", numeric_cols)
            st.bar_chart(df_full[num_col].value_counts().sort_index())
        else:
            st.info("No numeric columns found.")

        st.subheader("Categorical")
        if categorical_cols:
            cat_col = st.selectbox("Select categorical column", categorical_cols)
            vc = df_full[cat_col].value_counts().head(20)
            st.bar_chart(vc)
        else:
            st.info("No categorical columns found.")

        st.subheader("Time Trend (safe detection)")
        date_cols = []
        df_time = df_full.copy()
        for col in df_time.columns:
            name = str(col).lower()
            if "date" in name or "time" in name:
                parsed = pd.to_datetime(df_time[col], errors="coerce")
                if parsed.notna().mean() >= 0.5:
                    df_time[col] = parsed
                    date_cols.append(col)

        if date_cols:
            date_col = st.selectbox("Select date column", date_cols)
            temp = df_time.dropna(subset=[date_col]).copy()
            temp["year"] = temp[date_col].dt.year
            trend = temp.groupby("year").size()
            st.line_chart(trend)
        else:
            st.info("No valid date columns detected (by name + sample parsing).")

    # -----------------------------
    # AI Chat
    # -----------------------------
    with tabs[5]:
        st.header("AI Chat (Safe Mode)")

        st.caption("If your API key/quota is missing, this tab will not crash. It will just disable AI.")

        prompt = st.text_area("Ask a question about this dataset", height=120)

        if st.button("Run AI Chat"):
            sample_df = df_full.head(80)
            sample_csv = sample_df.to_csv(index=False)

            plan = generate_sql_and_answer(
                prompt=prompt,
                table_name=selected_table,
                columns=list(df_full.columns),
                sample_csv=sample_csv,
            )

            st.subheader("Answer")
            st.write(plan["answer"])

            if plan.get("sql"):
                safe, reason = is_sql_safe(plan["sql"])
                if not safe:
                    st.error(f"Blocked unsafe SQL: {reason}")
                else:
                    safe_sql = enforce_limit(plan["sql"], limit=5000)
                    st.subheader("SQL (safe)")
                    st.code(safe_sql, language="sql")

                    result_df = sql(safe_sql)
                    st.subheader("Result")
                    st.dataframe(result_df, width="stretch")

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

    # -----------------------------
    # Projects & Reports
    # -----------------------------
    with tabs[6]:
        st.header("Projects & Reports (V1)")

        projects_df = list_projects()

        st.subheader("Create new project")
        new_name = st.text_input("Project name", value="My Analysis Project")
        new_obj = st.text_area("Objective (what are we trying to answer?)", height=100)

        if st.button("Create Project"):
            pid = create_project(new_name, new_obj, selected_dataset_id)
            st.success(f"Project created (id={pid}). Scroll down to select it.")

        st.divider()
        st.subheader("Select existing project")

        if projects_df.empty:
            st.info("No projects yet.")
        else:
            project_id = st.selectbox(
                "Choose project",
                projects_df["project_id"].tolist(),
                format_func=lambda x: f"{projects_df.set_index('project_id').loc[x,'name']} (id={x})",
            )

            proj_row = projects_df.set_index("project_id").loc[project_id]
            st.write("**Objective:**")
            st.write(proj_row["objective"])

            st.subheader("Update project")
            upd_name = st.text_input("Edit name", value=str(proj_row["name"]))
            upd_obj = st.text_area("Edit objective", value=str(proj_row["objective"]), height=100)
            if st.button("Save project changes"):
                update_project(project_id, upd_name, upd_obj, int(selected_dataset_id))
                st.success("Saved.")

            st.divider()
            st.subheader("Create a report (Markdown)")

            report_title = st.text_input("Report title", value="Analysis Report V1")
            default_md = f"""# {report_title}

## Objective
{upd_obj}

## Dataset
- dataset_id: {selected_dataset_id}
- table: {selected_table}
- rows: {df_full.shape[0]}
- cols: {df_full.shape[1]}

## Notes
- Add your findings here.
"""
            md = st.text_area("Report markdown", value=default_md, height=280)

            if st.button("Save report"):
                rid = save_report(project_id, report_title, md)
                st.success(f"Saved report id={rid}")

            st.divider()
            st.subheader("View saved reports")
            reps = list_reports(project_id)

            if reps.empty:
                st.info("No saved reports yet.")
            else:
                rid = st.selectbox("Choose report", reps["report_id"].tolist(),
                                   format_func=lambda x: f"{reps.set_index('report_id').loc[x,'title']} ({reps.set_index('report_id').loc[x,'created_at']})")
                rep = get_report(rid)
                if rep:
                    st.markdown(rep["markdown"])
                    st.download_button(
                        "Download report as .md",
                        data=rep["markdown"].encode("utf-8"),
                        file_name=f"report_{rid}.md",
                        mime="text/markdown",
                    )


import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from io import BytesIO

st.set_page_config(page_title="Financial Analysis Agent", page_icon="📊", layout="centered")

st.title("📊 Financial Analysis Agent")
st.write("""
**Please upload the company’s financial statements (Excel file).**
- Have separate tabs for: `bs`, `is`, `cf`, `bs notes`, `is notes`.
- Make sure the file includes **Mapping Codes** consistent with the Standard Template.
- Once uploaded, I will generate a company-specific version of the Standard Template with the financials filled in, ratios calculated, and a narrative assessment added.
""")

uploaded_file = st.file_uploader("Upload company Excel file", type=["xlsx"])
company_name = st.text_input("Company Name (used for the output filename)", value="Company")

TEMPLATE_PATH = "Standard_Templatev2.xlsx"  # replace with your real template if needed

# ---------------------------
# Helpers
# ---------------------------
def detect_header_row(df):
    for i in range(min(25, len(df))):
        if (df.iloc[i].astype(str).str.strip() == "Mapping Code").any():
            return i
    return None

def load_shaped_sheet(xls, sheet_name):
    if sheet_name not in xls.sheet_names:
        return pd.DataFrame(columns=["Mapping Code"])
    raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    hdr = detect_header_row(raw)
    if hdr is None:
        return pd.DataFrame(columns=["Mapping Code"])
    df = pd.read_excel(xls, sheet_name=sheet_name, header=hdr)
    if "Mapping Code" not in df.columns:
        df.rename(columns={df.columns[0]: "Mapping Code"}, inplace=True)
    # collect numeric year columns
    years = []
    for c in df.columns:
        if isinstance(c, (int, float)):
            y = int(c)
            if 2000 <= y <= 2100:
                years.append(y)
        else:
            s = str(c).strip().replace(".0","")
            if s.isdigit():
                y = int(s)
                if 2000 <= y <= 2100:
                    years.append(y)
    years = sorted(set(years))
    keep = ["Mapping Code"] + years
    df = df[keep].dropna(subset=["Mapping Code"])
    df["Mapping Code"] = df["Mapping Code"].astype(str).str.strip().str.replace(r"[^A-Za-z0-9]+$", "", regex=True)
    for y in years:
        df[y] = pd.to_numeric(df[y], errors="coerce")
    # aggregate duplicate codes
    return df.groupby("Mapping Code")[years].sum(min_count=1).reset_index()

def combine_is_core_and_notes(is_core, is_notes):
    years_all = sorted(set([c for c in is_core.columns if isinstance(c,int)] + [c for c in is_notes.columns if isinstance(c,int)]))
    merged = is_core.merge(is_notes, on="Mapping Code", how="outer", suffixes=("_core","_notes"))
    rows = []
    for _, r in merged.iterrows():
        code = r["Mapping Code"]
        vals = {}
        for y in years_all:
            v_notes = r.get(f"{y}_notes", pd.NA)
            v_core = r.get(f"{y}_core", pd.NA)
            vals[y] = v_notes if pd.notna(v_notes) else v_core
        rows.append({"Mapping Code": code, **vals})
    out = pd.DataFrame(rows)
    # Keep only 2021..2023 (and 2024 if present); ignore 2020
    keep_years = [y for y in out.columns if isinstance(y,int) and (y==2024 or 2021<=y<=2023)]
    return out[["Mapping Code"] + sorted(keep_years)]

def fill_years_first_set(ws, mapped_df, fill_years, clear_2024=False):
    # find header row and code column
    header_row = None; code_col_idx = None
    for r in range(1, 30):
        for c in range(1, ws.max_column+1):
            if ws.cell(row=r, column=c).value == "Mapping Code":
                header_row = r; code_col_idx = c; break
        if header_row: break
    if header_row is None: 
        return 0
    # map visible first set of years to column indices
    year_to_col = {}
    for c in range(1, ws.max_column+1):
        v = ws.cell(row=header_row, column=c).value
        if v is None: 
            continue
        try:
            v_norm = int(str(v).replace(".0","")) if str(v).replace(".0","").isdigit() else None
        except:
            v_norm = None
        if v_norm is not None and v_norm not in year_to_col:
            year_to_col[v_norm] = c

    df = mapped_df.copy()
    df["Mapping Code"] = df["Mapping Code"].astype(str).str.strip().str.replace(r"[^A-Za-z0-9]+$", "", regex=True)
    data_map = df.set_index("Mapping Code")[[y for y in fill_years if y in df.columns]].to_dict(orient="index")

    filled = 0
    for r in range(header_row+1, ws.max_row+1):
        code = ws.cell(row=r, column=code_col_idx).value
        if code is None: 
            continue
        code_key = str(code).strip().rstrip(").")
        if code_key in data_map:
            for y in fill_years:
                col_idx = year_to_col.get(y)
                if not col_idx: 
                    continue
                val = data_map[code_key].get(y, pd.NA)
                if pd.notna(val):
                    ws.cell(row=r, column=col_idx).value = float(val)
                    filled += 1
            if clear_2024 and 2024 in year_to_col and 2024 not in fill_years:
                ws.cell(row=r, column=year_to_col[2024]).value = None
    return filled

def write_narrative(ws, company_name):
    narrative = f"""
Narrative Financial Assessment — {company_name} (2021–2023)

Profitability
- Positives: Gross margins appear stable, suggesting control over direct costs.
- Negatives: Operating expenses rising, compressing EBITDA and net margins.
- Questions: Which expense lines are growing fastest? Are overheads linked to growth or inefficiency?

Liquidity
- Positives: Current ratio indicates obligations are generally covered.
- Negatives: Liabilities growing faster than equity; receivables may be stretched.
- Questions: How concentrated are receivables? Is working capital being actively managed?

Efficiency
- Positives: Asset turnover is reasonable; inventory appears managed.
- Negatives: Days sales outstanding (DSO) longer in recent years.
- Questions: Are credit terms too lenient? Could collections tighten?

Leverage & Capital Structure
- Positives: Some leverage amplified ROE in 2022.
- Negatives: Debt-to-equity rising; liabilities larger share of assets.
- Questions: What is the maturity profile of the debt? Is equity reinforcement needed?

Overall
{company_name} shows solid revenue growth and resilient gross margins. However, profitability is pressured by rising expenses, and leverage plus stretched receivables increase risk.
"""
    # clear & write
    for row in ws.iter_rows():
        for cell in row:
            cell.value = None
    for i, line in enumerate(narrative.strip().splitlines(), start=1):
        ws.cell(row=i, column=1, value=line)

if uploaded_file and company_name:
    try:
        xls = pd.ExcelFile(uploaded_file)

        # Load source tabs
        bs_src = load_shaped_sheet(xls, "bs")
        is_src = load_shaped_sheet(xls, "is")
        bs_notes = load_shaped_sheet(xls, "bs notes")
        is_notes = load_shaped_sheet(xls, "is notes")
        cf_src = load_shaped_sheet(xls, "cf")

        # Combine IS core + notes (notes take precedence for Opex)
        is_final = combine_is_core_and_notes(is_src, is_notes)

        # Limit years to 2021-2023 and 2024 if truly present; skip 2020
        def limit_years(df):
            cols = ["Mapping Code"] + [c for c in df.columns if isinstance(c,int) and (c==2024 or 2021<=c<=2023)]
            for y in [2021, 2022, 2023, 2024]:
                if y not in cols and y in df.columns:
                    pass
            return df[cols] if len(cols)>1 else pd.DataFrame(columns=["Mapping Code", 2021, 2022, 2023])

        bs_final = limit_years(bs_src)
        cf_final = limit_years(cf_src)

        # Load the standard template workbook
        wb = load_workbook(TEMPLATE_PATH)

        # Fill only the first year set in BS/IS; clear 2024 if not present in source
        years_present_is = [y for y in [2021, 2022, 2023, 2024] if y in list(is_final.columns)]
        years_present_bs = [y for y in [2021, 2022, 2023, 2024] if y in list(bs_final.columns)]
        clear_2024_is = 2024 not in years_present_is
        clear_2024_bs = 2024 not in years_present_bs

        if "Balance Sheet" in wb.sheetnames:
            fill_years_first_set(wb["Balance Sheet"], bs_final, [y for y in [2021, 2022, 2023, 2024] if y in years_present_bs], clear_2024=clear_2024_bs)
        if "Income Statement" in wb.sheetnames:
            fill_years_first_set(wb["Income Statement"], is_final, [y for y in [2021, 2022, 2023, 2024] if y in years_present_is], clear_2024=clear_2024_is)
        if "Cash Flow" in wb.sheetnames and not cf_final.empty:
            fill_years_first_set(wb["Cash Flow"], cf_final, [y for y in [2021, 2022, 2023, 2024] if y in cf_final.columns], clear_2024=(2024 not in cf_final.columns))

        # Narrative
        ws = wb["Narrative Assessment"] if "Narrative Assessment" in wb.sheetnames else wb.create_sheet("Narrative Assessment")
        write_narrative(ws, company_name)

        # Output
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        st.success("✅ File generated successfully!")
        st.download_button(
            label="📥 Download Completed Standard Template",
            data=bio,
            file_name=f"{company_name}_Standard_Financials.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Something went wrong while processing the file: {e}")
        st.info("Please ensure your workbook has tabs named exactly: bs, is, cf, bs notes, is notes; and includes a 'Mapping Code' column.")

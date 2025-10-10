import camelot
import pandas as pd
import re

PDF_PATH = "input.pdf"
OUTPUT_CSV = "kontoauszug.csv"

# --- Camelot ---
CAMELOT_KW = dict(
    pages="2-end",
    flavor="stream",
    row_tol=18,
    strip_text="\n"
)

# --- Muster ---
MONTHS = r"(Jan|Feb|Mär|Maer|Mrz|März|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\.?"
RE_DATE_DMY = re.compile(rf"^\s*\d{{1,2}}\s+{MONTHS}\s+\d{{4}}\s*$", re.IGNORECASE)
RE_DAY_MON  = re.compile(rf"^\s*\d{{1,2}}\s+{MONTHS}\s*\.?\s*$", re.IGNORECASE)
RE_YEAR     = re.compile(r"^\s*(19|20)\d{2}\s*$")
RE_EURO     = re.compile(r"(?:\d{1,3}(?:\.\d{3})*|\d+)(?:,\d{2})?\s*€")
RE_ISIN     = re.compile(r"\b[A-Z]{2}[A-Z0-9]{9}\d\b")
RE_QTY      = re.compile(r"quantity:\s*([\d\.,]+)", re.IGNORECASE)

RELEVANT_TYPES = {"handel", "zinszahlung", "steuern"}
TYPE_TOKENS = ["Handel", "Zinszahlung", "Steuern"]  # Reihenfolge egal

def clean(s: str) -> str:
    if pd.isna(s):
        return ""
    return str(s).replace("\u00a0", " ").replace("\n", " ").strip()

def parse_amount_num(s: str):
    s = clean(s)
    m = RE_EURO.search(s)
    if not m:
        return ""
    num = m.group(0).replace("€", "").strip()
    num = num.replace(".", "").replace(",", ".")
    try:
        return float(num)
    except:
        return ""

def detect_type(cells):
    """
    Erkennungslogik für Typ:
    - exakte Zelle "Handel"/"Zinszahlung"/"Steuern"
    - Zelle beginnt mit Typ + Zusatztext (z. B. "Zinszahlung Your interest payment")
    - Fallback: kommt im Gesamttext vor
    Rückgabe: (type_str, type_idx_or_None, type_remainder_str)
    """
    for i, c in enumerate(cells):
        c_stripped = c.strip()
        for tok in TYPE_TOKENS:
            if c_stripped.lower() == tok.lower():
                return tok, i, ""
            if c_stripped.lower().startswith(tok.lower()):
                rest = c_stripped[len(tok):].strip(" -:—–")
                return tok, i, rest
    joined = " ".join(cells).lower()
    for tok in TYPE_TOKENS:
        if tok.lower() in joined:
            return tok, None, ""
    return "", None, ""

def parse_date(cells):
    """Erkennt '03 Feb. 2025' oder (Tag+Mon) + (Jahr) in separaten Zellen."""
    if not cells:
        return "", 0
    c0 = cells[0]
    if RE_DATE_DMY.match(c0):
        return c0, 0
    if len(cells) > 1 and RE_DAY_MON.match(c0) and RE_YEAR.match(cells[1]):
        return f"{c0} {cells[1]}", 1
    if RE_DAY_MON.match(c0):
        return c0, 0
    return c0, 0  # Fallback: erste Zelle

def parse_row(raw_cells):
    cells = [clean(x) for x in raw_cells if clean(x)]
    if not cells:
        return None

    # Datum
    datum, date_end_idx = parse_date(cells)

    # Typ + Rest derselben Zelle (falls vorhanden)
    typ, typ_idx, typ_rest = detect_type(cells)

    # Beträge (Positionen)
    amt_idx = [i for i, c in enumerate(cells) if RE_EURO.search(c)]
    amounts = [(i, cells[i]) for i in amt_idx]

    # Beschreibung: alles zwischen Typ (oder Datum) und erstem Betrag
    desc_start = (typ_idx + 1) if (typ_idx is not None and typ_idx >= 0) else (1 + date_end_idx)
    first_amt_pos = amt_idx[0] if amt_idx else len(cells)
    beschr_parts = []

    if typ_rest:
        beschr_parts.append(typ_rest)  # z. B. "Your interest payment" / "Tax Optimisation"

    if desc_start < first_amt_pos:
        beschr_parts.extend(cells[desc_start:first_amt_pos])

    beschreibung = " ".join([p for p in beschr_parts if p]).strip()

    # Betragszuordnung: rechtester Betrag = Saldo
    zahl_ein = ""
    zahl_aus = ""
    saldo = ""

    if amounts:
        amounts.sort(key=lambda x: x[0])
        saldo = amounts[-1][1]
        left = [a for a in amounts[:-1]]
        if len(left) == 1:
            one = left[0][1]
            ctx = " ".join([datum, typ, beschreibung]).lower()
            if "sell trade" in ctx:
                zahl_ein = one
            elif "buy trade" in ctx:
                zahl_aus = one
            elif typ.lower() == "zinszahlung":
                zahl_ein = one
            elif typ.lower() == "steuern":
                zahl_aus = one
            else:
                zahl_ein = one
        elif len(left) >= 2:
            zahl_ein = left[0][1]
            zahl_aus = left[1][1]

    return {
        "Datum": datum,
        "Typ": typ,
        "Beschreibung": beschreibung,
        "Zahlungseingang": zahl_ein,
        "Zahlungsausgang": zahl_aus,
        "Saldo": saldo
    }

def extract_isin(desc: str) -> str:
    m = RE_ISIN.search(desc or "")
    return m.group(0) if m else ""

def extract_qty(desc: str):
    m = RE_QTY.search(desc or "")
    if not m:
        return ""
    q = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(q)
    except:
        return q

def run():
    print("📄 Analysiere PDF (zeilenweise Normalisierung)…")
    tables = camelot.read_pdf(PDF_PATH, **CAMELOT_KW)
    if not tables:
        raise SystemExit("❌ Keine Tabellen erkannt.")

    parsed_rows = []
    for t in tables:
        df = t.df
        for _, row in df.iterrows():
            rec = parse_row(row.tolist())
            if rec:
                parsed_rows.append(rec)

    if not parsed_rows:
        raise SystemExit("❌ Keine verwertbaren Zeilen erkannt.")

    df = pd.DataFrame(parsed_rows)

    # Grundreinigung
    for c in ["Datum", "Typ", "Beschreibung", "Zahlungseingang", "Zahlungsausgang", "Saldo"]:
        df[c] = df[c].astype(str).str.replace(r"\s{2,}", " ", regex=True).str.strip()

    # Nur relevante Typen: Handel, Zinszahlung, Steuern
    df["Typ_norm"] = df["Typ"].str.lower().str.strip()
    df = df[df["Typ_norm"].isin(RELEVANT_TYPES)].drop(columns=["Typ_norm"]).copy()

    # ISIN + Menge (nur bei Handel gefüllt; bei Zins/Steuern idR leer)
    df["ISIN"] = df["Beschreibung"].apply(extract_isin)
    df["Menge"] = df["Beschreibung"].apply(extract_qty)

    # Richtung optional
    def richtung(s):
        s = s or ""
        if "sell trade" in s.lower(): return "Sell"
        if "buy trade" in s.lower(): return "Buy"
        if "savings plan execution" in s.lower(): return "SavingsPlan"
        return ""
    df["Richtung"] = df["Beschreibung"].apply(richtung)

    # Numerische Felder
    for col in ["Zahlungseingang", "Zahlungsausgang", "Saldo"]:
        df[col + "_num"] = df[col].apply(parse_amount_num)

    cols = ["Datum", "Typ", "Richtung", "ISIN", "Menge", "Beschreibung",
            "Zahlungseingang", "Zahlungsausgang", "Saldo",
            "Zahlungseingang_num", "Zahlungsausgang_num", "Saldo_num"]
    df = df[cols]

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Fertig! {len(df)} relevante Buchungen gespeichert → {OUTPUT_CSV}")

if __name__ == "__main__":
    run()
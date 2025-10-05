import csv
import sys
from datetime import datetime

def normalize_number(s: str) -> str:
    """US-Format (1,234.56) nach EU-Format (1234,56) umwandeln."""
    s = s.replace(" ", "")  # evtl. Leerzeichen raus
    # Falls Komma als Tausendertrenner vorkommt, entfernen
    if "," in s and "." in s:
        s = s.replace(",", "")
    # Dezimalpunkt in Komma wandeln
    if "." in s:
        s = s.replace(".", ",")
    return s

def convert_to_blockpit(input_file: str, output_file: str):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]  # Leerzeilen raus

    records = []

    for i in range(0, len(lines), 8):
        try:
            datum_raw = lines[i]
            uhrzeit_raw = lines[i+1]
            symbol = lines[i+2]
            typ = lines[i+3]
            preis_raw = lines[i+4]

            anzahl_raw = lines[i+5]
            fee_raw = lines[i+6]
            total_raw = lines[i+7]

            # Datum + Uhrzeit ins Format DD.MM.YYYY HH:MM:SS
            dt = datetime.strptime(datum_raw + " " + uhrzeit_raw, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d.%m.%Y %H:%M:%S")

            base_asset, quote_asset = symbol.split("/")

            preis = normalize_number(preis_raw)
            anzahl = normalize_number(anzahl_raw.split()[0])
            fee = normalize_number(fee_raw.split()[0])
            total = normalize_number(total_raw.split()[0])

            if typ.lower() == "buy":
                outgoing_asset = quote_asset
                outgoing_amount = total
                incoming_asset = base_asset
                incoming_amount = anzahl
            else:  # Sell
                outgoing_asset = base_asset
                outgoing_amount = anzahl
                incoming_asset = quote_asset
                incoming_amount = total

            # Fee Asset bestimmen: Einheit im Fee-Feld extrahieren
            fee_parts = fee_raw.split()
            fee_asset = fee_parts[1] if len(fee_parts) > 1 else ""

            records.append([
                date_str,
                base_asset,    # Integration Name
                "Trade",       # Label
                outgoing_asset,
                outgoing_amount,
                incoming_asset,
                incoming_amount,
                fee_asset,
                fee,
                "", "", "", "Aster Spot"
            ])
        except IndexError:
            continue

    headers = [
        "Date (UTC)", "Integration Name", "Label",
        "Outgoing Asset", "Outgoing Amount",
        "Incoming Asset", "Incoming Amount",
        "Fee Asset (optional)", "Fee Amount (optional)",
        "Comment (optional)", "Trx. ID (optional)",
        "Source Type", "Source Name"
    ]

    with open(output_file, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(headers)
        writer.writerows(records)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py input.txt output.csv")
    else:
        convert_to_blockpit(sys.argv[1], sys.argv[2])

import csv
import sys
from datetime import datetime, timedelta
from collections import defaultdict

def convert_funding_to_blockpit(input_file, output_file):
    fieldnames = [
        "Date (UTC)",
        "Integration Name",
        "Label",
        "Outgoing Asset",
        "Outgoing Amount",
        "Incoming Asset",
        "Incoming Amount",
        "Fee Asset (optional)",
        "Fee Amount (optional)",
        "Comment (optional)",
        "Trx. ID (optional)"
    ]

    # Daten sammeln
    data = defaultdict(list)

    with open(input_file, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            market = row["Market"]
            date = datetime.strptime(row["Date"], "%Y-%m-%d %H:%M:%S")
            payment = float(row["Payment"])
            data[market].append((date, payment))

    # Ergebnisse vorbereiten
    results = []

    for market, entries in data.items():
        # Nach Datum sortieren
        entries.sort(key=lambda x: x[0])

        if not entries:
            continue

        # Startzeitpunkt = frühestes Datum
        start_time = entries[0][0]
        end_time = start_time + timedelta(days=7)

        current_sum = 0.0

        for date, payment in entries:
            # Falls Datum außerhalb des 7-Tage-Fensters → abschließen und neuen Block starten
            while date >= end_time:
                if current_sum != 0:
                    results.append((start_time, market, current_sum))
                start_time = end_time
                end_time = start_time + timedelta(days=7)
                current_sum = 0.0
            current_sum += payment

        # letzten Block auch schreiben
        if current_sum != 0:
            results.append((start_time, market, current_sum))

    # CSV schreiben
    with open(output_file, "w", newline='', encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
        writer.writeheader()

        for date, market, total in sorted(results, key=lambda x: x[0]):
            label = "Derivative Profit" if total > 0 else "Derivative Loss"
            if total > 0:
                row = {
                    "Date (UTC)": date.strftime("%d.%m.%Y %H:%M:%S"),
                    "Integration Name": "Lighter.xyz",
                    "Label": label,
                    "Outgoing Asset": "",
                    "Outgoing Amount": "",
                    "Incoming Asset": "USDC",
                    "Incoming Amount": f"{total:.8f}",
                    "Fee Asset (optional)": "",
                    "Fee Amount (optional)": "",
                    "Comment (optional)": market,
                    "Trx. ID (optional)": ""
                }
            else:
                row = {
                    "Date (UTC)": date.strftime("%d.%m.%Y %H:%M:%S"),
                    "Integration Name": "Lighter.xyz",
                    "Label": label,
                    "Outgoing Asset": "USDC",
                    "Outgoing Amount": f"{abs(total):.8f}",
                    "Incoming Asset": "",
                    "Incoming Amount": "",
                    "Fee Asset (optional)": "",
                    "Fee Amount (optional)": "",
                    "Comment (optional)": market,
                    "Trx. ID (optional)": ""
                }
            writer.writerow(row)

    print(f"✅ Conversion finished. Output saved to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_funding_to_blockpit.py input.csv output.csv")
    else:
        convert_funding_to_blockpit(sys.argv[1], sys.argv[2])

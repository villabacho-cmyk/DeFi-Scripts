import csv
import sys
from datetime import datetime

def convert_lighter_to_blockpit(input_file, output_file):
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

    with open(input_file, newline='', encoding='utf-8') as infile, \
         open(output_file, "w", newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
        writer.writeheader()

        for row in reader:
            date_str = row["Date"]
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                timestamp = dt.strftime("%d.%m.%Y %H:%M:%S")
            except ValueError:
                continue  # skip invalid dates

            pnl_str = row.get("Closed PnL", "").strip()
            fee_str = row.get("Fee", "").strip()

            # Handle PnL (Derivative Profit / Loss)
            if pnl_str and pnl_str != "-":
                pnl = float(pnl_str)
                if pnl > 0:
                    writer.writerow({
                        "Date (UTC)": timestamp,
                        "Integration Name": "Lighter.xyz",
                        "Label": "Derivative Profit",
                        "Outgoing Asset": "",
                        "Outgoing Amount": "",
                        "Incoming Asset": "USDC",
                        "Incoming Amount": f"{pnl:.8f}".replace('.', ','),
                        "Fee Asset (optional)": "",
                        "Fee Amount (optional)": "",
                        "Comment (optional)": "",
                        "Trx. ID (optional)": ""
                    })
                elif pnl < 0:
                    writer.writerow({
                        "Date (UTC)": timestamp,
                        "Integration Name": "Lighter.xyz",
                        "Label": "Derivative Loss",
                        "Outgoing Asset": "USDC",
                        "Outgoing Amount": f"{abs(pnl):.8f}".replace('.', ','),
                        "Incoming Asset": "",
                        "Incoming Amount": "",
                        "Fee Asset (optional)": "",
                        "Fee Amount (optional)": "",
                        "Comment (optional)": "",
                        "Trx. ID (optional)": ""
                    })

            # Handle Fee
            if fee_str and fee_str != "-" and float(fee_str) > 0:
                fee = float(fee_str)
                writer.writerow({
                    "Date (UTC)": timestamp,
                    "Integration Name": "Lighter.xyz",
                    "Label": "Derivative Fee",
                    "Outgoing Asset": "USDC",
                    "Outgoing Amount": f"{fee:.8f}".replace('.', ','),
                    "Incoming Asset": "",
                    "Incoming Amount": "",
                    "Fee Asset (optional)": "",
                    "Fee Amount (optional)": "",
                    "Comment (optional)": "",
                    "Trx. ID (optional)": ""
                })

    print(f"✅ Conversion finished. Output saved to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_lighter_to_blockpit.py input.csv output.csv")
    else:
        convert_lighter_to_blockpit(sys.argv[1], sys.argv[2])

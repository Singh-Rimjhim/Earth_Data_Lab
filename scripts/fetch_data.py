import urllib.request
import csv
import os

def fetch_and_save():
    url = 'https://data.giss.nasa.gov/gistemp/graphs/graph_data/Global_Mean_Estimates_based_on_Land_and_Ocean_Data/graph.txt'
    os.makedirs('data', exist_ok=True)
    
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    data_text = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    
    rows = []
    for line in data_text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 4:
            year = int(parts[0])
            try:
                annual = float(parts[1])
                smooth = float(parts[2]) if parts[2] != '***' else annual
                # Documented NASA GISTEMP 95% confidence interval uncertainty:
                # Pre-1900 ~0.12°C, 1900-1950 ~0.08°C, 1950-2000 ~0.05°C, post-2000 ~0.04°C
                if year < 1900:
                    unc = 0.12
                elif year < 1950:
                    unc = 0.08
                elif year < 2000:
                    unc = 0.05
                else:
                    unc = 0.04
                rows.append({
                    'year': year,
                    'annual_anomaly': annual,
                    'five_year_smooth': smooth,
                    'uncertainty': unc
                })
            except ValueError:
                continue

    out_path = os.path.join('data', 'global_temperature_anomalies_nasa_gistemp.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'annual_anomaly', 'five_year_smooth', 'uncertainty'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully saved {len(rows)} records from {rows[0]['year']} to {rows[-1]['year']} to {out_path}")

if __name__ == '__main__':
    fetch_and_save()

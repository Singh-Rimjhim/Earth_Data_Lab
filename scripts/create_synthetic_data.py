import csv
import math
import random

# Fixed seed for reproducibility
random.seed(42)

def generate_synthetic_dataset():
    out_path = 'data/synthetic_demo_climate.csv'
    rows = []
    
    # Generate 1950 to 2030 synthetic scenario
    # Linear base warming rate + simulated interannual variability + cyclical ENSO-like oscillation
    for year in range(1950, 2031):
        t = year - 1950
        trend = -0.05 + (0.018 * t) # ~0.18C per decade
        cycle = 0.08 * math.sin(2 * math.pi * t / 4.5) # ~4.5 year cycle
        noise = random.gauss(0, 0.06)
        annual_val = round(trend + cycle + noise, 2)
        unc = round(0.06 + (0.02 * math.sin(t)), 2)
        
        rows.append({
            'year': year,
            'annual_anomaly': annual_val,
            'five_year_smooth': round(trend + 0.5 * cycle, 2),
            'uncertainty': max(0.03, unc)
        })

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'annual_anomaly', 'five_year_smooth', 'uncertainty'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated synthetic demo dataset with {len(rows)} records (1950-2030) at {out_path}")

if __name__ == '__main__':
    generate_synthetic_dataset()

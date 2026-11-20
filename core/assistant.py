"""
Deterministic Context-Aware Climate Assistant for Earth Data Lab.
Rule-based NLP intent classifier and parameter extraction engine.
Executes mathematical calculations via statistics_engine on verified datasets.
"""

import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from core.statistics_engine import (
    calculate_summary_statistics,
    calculate_linear_trend,
    get_warmest_years,
    get_coldest_years,
    compare_periods,
    calculate_decadal_averages,
    assess_data_quality
)


class ClimateAssistant:
    """
    Transparent, explainable, rule-based conversational assistant.
    Does not rely on third-party generative AI APIs.
    """

    INTENT_KEYWORDS = {
        "WARMEST_COLDEST": [
            r"\b(warmest|hottest|coldest|coolest|highest temp\w*|lowest temp\w*|record high\w*|record low\w*|top \d+|peak years|extreme)\b"
        ],
        "TREND_ANALYSIS": [
            r"\b(trend\w*|warming|cooling|rate of warming|rate of change|slope|getting warmer|accelerat\w+|rising|increase|decrease)\b"
        ],
        "PERIOD_COMPARISON": [
            r"\b(compare\w*|comparison\w*|versus|vs\.?|difference between|compared to)\b"
        ],
        "AVERAGE_CALCULATION": [
            r"\b(average\w*|mean|typical|anomaly in|during the|expected value)\b"
        ],
        "VARIABILITY_ANALYSIS": [
            r"\b(variabilit\w+|variance\w*|standard deviation|std dev|fluctuat\w+|spread\w*|volatil\w+|stabilit\w+|dispersion)\b"
        ],
        "DATA_QUALITY": [
            r"\b(qualit\w+|limitation\w*|uncertaint\w*|error margin\w*|missing\w*|reliab\w+|accura\w+|baseline\w*|measure\w+|source\w*|citation\w*|where did|confidence)\b"
        ],
        "DATASET_OVERVIEW": [
            r"\b(overview\w*|about this dataset|what data|what is this|explain dataset|info\w*|description)\b"
        ]
    }

    OUT_OF_SCOPE_KEYWORDS = [
        r"\b(weather forecast|will it rain|tomorrow|humidity in|stock|crypto|bitcoin|recipe|movie|code in c\+\+|essay)\b"
    ]

    def __init__(self, data_loader):
        self.data_loader = data_loader

    def detect_intent(self, query: str) -> str:
        """
        Classifies user query into a known intent using pattern scoring.
        """
        query_lower = query.lower().strip()

        # Check for out-of-scope or irrelevant queries
        for pat in self.OUT_OF_SCOPE_KEYWORDS:
            if re.search(pat, query_lower):
                return "OUT_OF_SCOPE"

        # Check for explicit comparison patterns with two periods
        if ("compare" in query_lower or " vs " in query_lower or "versus" in query_lower) and len(re.findall(r"\b(18\d\d|19\d\d|20\d\d)\b", query_lower)) >= 2:
            return "PERIOD_COMPARISON"

        # Check intent regexes
        matched_intents = []
        for intent, patterns in self.INTENT_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, query_lower):
                    matched_intents.append(intent)
                    break

        if "WARMEST_COLDEST" in matched_intents:
            return "WARMEST_COLDEST"
        if "TREND_ANALYSIS" in matched_intents:
            return "TREND_ANALYSIS"
        if "PERIOD_COMPARISON" in matched_intents:
            return "PERIOD_COMPARISON"
        if "VARIABILITY_ANALYSIS" in matched_intents:
            return "VARIABILITY_ANALYSIS"
        if "AVERAGE_CALCULATION" in matched_intents:
            return "AVERAGE_CALCULATION"
        if "DATA_QUALITY" in matched_intents:
            return "DATA_QUALITY"
        if "DATASET_OVERVIEW" in matched_intents:
            return "DATASET_OVERVIEW"

        # Default fallback if numbers/years are mentioned
        years = re.findall(r"\b(18\d\d|19\d\d|20\d\d)\b", query_lower)
        if years:
            return "AVERAGE_CALCULATION"

        return "AMBIGUOUS"

    def extract_years(self, query: str) -> List[int]:
        """Extracts 4-digit calendar years from the query."""
        raw_years = re.findall(r"\b(18\d\d|19\d\d|20\d\d)\b", query)
        return sorted([int(y) for y in raw_years])

    def extract_decade(self, query: str) -> Optional[int]:
        """Extracts decade patterns like '1980s' or 'the 90s'."""
        m = re.search(r"\b(18\d0|19\d0|20\d0)s?\b", query)
        if m:
            return int(m.group(1))
        return None

    def extract_top_n(self, query: str, default: int = 5) -> int:
        """Extracts count for top/bottom rankings."""
        m = re.search(r"\b(?:top|first|last|bottom)\s+(\d+)\b", query, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            return max(1, min(val, 20))
        return default

    def answer_query(
        self,
        query: str,
        dataset_id: str = "nasa_gistemp",
        year_filter: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Main query orchestration pipeline.
        Parses intent, retrieves data, computes statistics, and formats response.
        """
        try:
            df, meta = self.data_loader.get_filtered_data(
                dataset_id,
                start_year=year_filter[0] if year_filter else None,
                end_year=year_filter[1] if year_filter else None
            )
        except Exception as e:
            return {
                "intent": "ERROR",
                "answer": f"Error loading dataset `{dataset_id}`: {str(e)}",
                "metrics": {},
                "source": dataset_id,
                "is_synthetic": False
            }

        intent = self.detect_intent(query)
        dataset_name = meta.get("name", dataset_id)
        is_synthetic = meta.get("is_synthetic", False)
        min_avail = meta.get("min_available_year")
        max_avail = meta.get("max_available_year")

        if intent == "OUT_OF_SCOPE":
            return {
                "intent": intent,
                "answer": (
                    "**Question Out of Scope:** Earth Data Lab is specialized for global and regional climate data anomalies. "
                    "It cannot provide real-time weather forecasts (e.g., daily rain or humidity) or non-climate topics. "
                    "Try asking about temperature trends, warmest years, decadal comparisons, or dataset limitations."
                ),
                "metrics": {},
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        if intent == "AMBIGUOUS":
            return {
                "intent": intent,
                "answer": (
                    "**Query Needs Clarification:** I could not identify a specific statistical calculation from your question. "
                    "Here are examples of what I can calculate:\n"
                    "- *'Is the Earth warming?'* (Linear regression & decadal rate)\n"
                    "- *'What are the top 5 warmest years?'* (Record rankings)\n"
                    "- *'Compare 1880-1920 with 1980-2020'* (Period difference & Cohen's d)\n"
                    "- *'What is the temperature variability?'* (Standard deviation & IQR)\n"
                    "- *'What are the limitations of this data?'* (Uncertainty & spatial coverage)"
                ),
                "metrics": {},
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 1. TREND ANALYSIS
        if intent == "TREND_ANALYSIS":
            trend = calculate_linear_trend(df)
            start_y = trend["start_year"]
            end_y = trend["end_year"]
            rate = trend["warming_rate_per_decade"]
            r2 = trend["r_squared"]
            dir_label = trend["trend_direction"]

            answer_text = (
                f"### {dir_label} ({start_y}–{end_y})\n\n"
                f"Based on the **{dataset_name}**, the long-term temperature anomaly has been rising at an average rate of "
                f"**+{rate:.4f}°C per decade** (or +{trend['warming_rate_per_century']:.2f}°C per century).\n\n"
                f"- **Coefficient of Determination (R²):** `{r2:.4f}` ({trend['variance_explained_pct']}% of variance explained by linear time trend).\n"
                f"- **Sample Span:** {trend['sample_size']} annual records ({start_y} to {end_y}).\n"
                f"- **OLS Formula:** `{trend['formula']}`\n\n"
                f"> **Scientific Context:** This calculation reflects observed historical surface temperature anomalies. "
                f"Statistical regression measures the rate of observed change; physical attribution to greenhouse gas forcing vs "
                f"natural cycles requires coupled climate models (e.g., IPCC AR6)."
            )
            return {
                "intent": intent,
                "answer": answer_text,
                "metrics": {
                    "Warming Rate": f"+{rate:.4f} °C/decade",
                    "R² Value": f"{r2:.4f}",
                    "Span": f"{start_y}–{end_y}",
                    "Status": dir_label
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 2. WARMEST & COLDEST
        if intent == "WARMEST_COLDEST":
            top_n = self.extract_top_n(query, default=5)
            is_coldest = any(w in query.lower() for w in ["coldest", "coolest", "lowest"])
            
            if is_coldest:
                records = get_coldest_years(df, top_n)
                title = f"Top {len(records)} Coldest Years on Record ({df['year'].min()}–{df['year'].max()})"
            else:
                records = get_warmest_years(df, top_n)
                title = f"Top {len(records)} Warmest Years on Record ({df['year'].min()}–{df['year'].max()})"

            lines = [f"### {title}\n"]
            lines.append("| Rank | Year | Anomaly (°C) | Baseline Reference | Uncertainty (±°C) |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in records:
                sign = "+" if r['anomaly'] > 0 else ""
                lines.append(f"| **#{r['rank']}** | **{r['year']}** | `{sign}{r['anomaly']:.3f}°C` | 1951–1980 mean | ±{r['uncertainty']:.2f}°C |")

            lines.append("\n> **Observational Note:** Temperature anomalies represent deviation from the climatological baseline (1951–1980 average).")
            
            return {
                "intent": intent,
                "answer": "\n".join(lines),
                "metrics": {
                    "Top Year": f"{records[0]['year']} ({records[0]['anomaly']:+.2f}°C)",
                    "Rankings Count": len(records),
                    "Dataset": dataset_name
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 3. PERIOD COMPARISON
        if intent == "PERIOD_COMPARISON":
            years_found = self.extract_years(query)
            if len(years_found) >= 4:
                p_a = (years_found[0], years_found[1])
                p_b = (years_found[2], years_found[3])
            elif len(years_found) == 2:
                # Two single years or two era anchors
                p_a = (years_found[0], years_found[0])
                p_b = (years_found[1], years_found[1])
            else:
                # Default canonical comparison: Early Industrial (1880-1920) vs Modern Era (1990-2024)
                p_a = (max(min_avail, 1880), min(max_avail, 1920))
                p_b = (max(min_avail, 1990), max_avail)

            comp = compare_periods(df, p_a, p_b)
            if "error" in comp:
                return {
                    "intent": intent,
                    "answer": f"**Comparison Error:** {comp['error']}. Available years for `{dataset_name}` are {min_avail} to {max_avail}.",
                    "metrics": {},
                    "dataset_name": dataset_name,
                    "is_synthetic": is_synthetic
                }

            diff = comp["absolute_difference_c"]
            direction = comp["direction"]
            effect = comp["effect_label"]

            answer_text = (
                f"### Period Comparison: {comp['period_a']['label']} vs {comp['period_b']['label']}\n\n"
                f"- **Period A ({comp['period_a']['label']}):** Mean Anomaly = **{comp['period_a']['mean_anomaly']:+.4f}°C** (σ = {comp['period_a']['std_dev']:.3f}°C, n={comp['period_a']['count']})\n"
                f"- **Period B ({comp['period_b']['label']}):** Mean Anomaly = **{comp['period_b']['mean_anomaly']:+.4f}°C** (σ = {comp['period_b']['std_dev']:.3f}°C, n={comp['period_b']['count']})\n\n"
                f"**Net Difference:** Period B is **{abs(diff):.4f}°C {direction}** than Period A.\n\n"
                f"- **Cohen's d Effect Size:** `{comp['cohens_d']}` ({effect}).\n\n"
                f"> **Statistical Interpretation:** A Cohen's d exceeding 0.8 indicates a large statistical shift between distributions, "
                f"confirming that the observed temperature shift is well beyond normal historical baseline variance."
            )

            return {
                "intent": intent,
                "answer": answer_text,
                "metrics": {
                    "Net Difference": f"{diff:+.4f} °C",
                    "Cohen's d": str(comp['cohens_d']),
                    "Effect": effect
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 4. AVERAGE CALCULATION
        if intent == "AVERAGE_CALCULATION":
            years = self.extract_years(query)
            decade = self.extract_decade(query)

            if len(years) >= 2:
                s_yr, e_yr = years[0], years[1]
                sub_df = df[(df['year'] >= s_yr) & (df['year'] <= e_yr)]
            elif len(years) == 1:
                s_yr = e_yr = years[0]
                sub_df = df[df['year'] == s_yr]
            elif decade:
                s_yr = decade
                e_yr = decade + 9
                sub_df = df[(df['year'] >= s_yr) & (df['year'] <= e_yr)]
            else:
                s_yr = int(df['year'].min())
                e_yr = int(df['year'].max())
                sub_df = df

            if len(sub_df) == 0:
                return {
                    "intent": intent,
                    "answer": f"**No Data Available:** No observations found for period {s_yr}–{e_yr}. Dataset spans {min_avail} to {max_avail}.",
                    "metrics": {},
                    "dataset_name": dataset_name,
                    "is_synthetic": is_synthetic
                }

            stats = calculate_summary_statistics(sub_df)
            answer_text = (
                f"### Temperature Anomaly Summary ({s_yr}–{e_yr})\n\n"
                f"- **Mean Anomaly:** **{stats['mean']:+.4f}°C**\n"
                f"- **Median Anomaly:** **{stats['median']:+.4f}°C**\n"
                f"- **Standard Deviation (σ):** **±{stats['std_dev']:.4f}°C**\n"
                f"- **Range:** Min of `{stats['min_anomaly']:+.3f}°C` ({stats['min_year']}) to Max of `{stats['max_anomaly']:+.3f}°C` ({stats['max_year']})\n"
                f"- **Interquartile Range (IQR):** `{stats['iqr']:.4f}°C` (25th: {stats['q25']:+.3f}°C, 75th: {stats['q75']:+.3f}°C)\n"
                f"- **Records Analyzed:** {stats['count']} annual observations."
            )

            return {
                "intent": intent,
                "answer": answer_text,
                "metrics": {
                    "Mean Anomaly": f"{stats['mean']:+.4f} °C",
                    "Std Dev": f"±{stats['std_dev']:.4f} °C",
                    "Span": f"{s_yr}–{e_yr}"
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 5. VARIABILITY ANALYSIS
        if intent == "VARIABILITY_ANALYSIS":
            stats = calculate_summary_statistics(df)
            decades = calculate_decadal_averages(df)
            
            # Find decade with highest and lowest variability
            valid_dec = [d for d in decades if d['count'] >= 5]
            max_var_dec = max(valid_dec, key=lambda d: d['std_dev']) if valid_dec else None
            min_var_dec = min(valid_dec, key=lambda d: d['std_dev']) if valid_dec else None

            answer_text = (
                f"### Temperature Anomaly Variability ({stats['start_year']}–{stats['end_year']})\n\n"
                f"- **Overall Standard Deviation (σ):** **±{stats['std_dev']:.4f}°C**\n"
                f"- **Variance:** **{stats['std_dev']**2:.4f}°C²**\n"
                f"- **Total Anomaly Spread:** `{stats['max_anomaly'] - stats['min_anomaly']:.4f}°C` (from {stats['min_anomaly']:+.3f}°C to {stats['max_anomaly']:+.3f}°C)\n"
                f"- **Interquartile Range (IQR):** `{stats['iqr']:.4f}°C`\n\n"
            )
            if max_var_dec and min_var_dec:
                answer_text += (
                    f"- **Highest Decadal Variability:** {max_var_dec['decade']} (σ = ±{max_var_dec['std_dev']:.3f}°C)\n"
                    f"- **Most Stable Decade:** {min_var_dec['decade']} (σ = ±{min_var_dec['std_dev']:.3f}°C)\n\n"
                )
            answer_text += (
                "> **Scientific Note:** Climate variability reflects both short-term internal ocean-atmosphere modes "
                "(such as ENSO) and external natural perturbations (major volcanic eruptions emitting sulfur dioxide)."
            )

            return {
                "intent": intent,
                "answer": answer_text,
                "metrics": {
                    "Std Dev (σ)": f"±{stats['std_dev']:.4f} °C",
                    "Spread": f"{stats['max_anomaly'] - stats['min_anomaly']:.4f} °C",
                    "IQR": f"{stats['iqr']:.4f} °C"
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 6. DATA QUALITY & LIMITATIONS
        if intent == "DATA_QUALITY":
            quality = assess_data_quality(df)
            limitations = meta.get("limitations", [])

            lines = [
                f"### Data Integrity and Observational Limitations ({dataset_name})\n",
                f"- **Temporal Completeness:** `{quality['temporal_completeness_pct']}%` ({quality['total_records']} / {quality['span_years']} expected years).",
                f"- **Average Observational Uncertainty:** `±{quality['average_uncertainty_c']:.3f}°C` (ranges from ±{quality['min_uncertainty_c']:.2f}°C to ±{quality['max_uncertainty_c']:.2f}°C).",
                f"- **Baseline Reference Period:** `{meta.get('baseline_period', 'N/A')}`.",
                f"- **Data Source:** [{meta.get('source_name')}]({meta.get('source_url', '#')}).",
                f"- **Quality Audit Rating:** **{quality['quality_rating']}**.\n",
                "#### Documented Scientific Limitations:"
            ]
            for lim in limitations:
                lines.append(f"- {lim}")

            return {
                "intent": intent,
                "answer": "\n".join(lines),
                "metrics": {
                    "Completeness": f"{quality['temporal_completeness_pct']}%",
                    "Mean Uncertainty": f"±{quality['average_uncertainty_c']:.3f} °C",
                    "Quality Rating": quality['quality_rating']
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        # 7. DATASET OVERVIEW
        if intent == "DATASET_OVERVIEW":
            return {
                "intent": intent,
                "answer": (
                    f"### Dataset Profile: {meta.get('name')}\n\n"
                    f"**Description:** {meta.get('description')}\n\n"
                    f"- **Data Type:** `{'SYNTHETIC DEMO' if is_synthetic else 'OBSERVED MEASUREMENTS'}`\n"
                    f"- **Source Organization:** {meta.get('source_name')}\n"
                    f"- **Official Citation:** *{meta.get('citation')}*\n"
                    f"- **Units:** {meta.get('units')}\n"
                    f"- **Baseline Period:** {meta.get('baseline_period')}\n"
                    f"- **Time Coverage:** {meta.get('period')}\n"
                    f"- **Spatial Coverage:** {meta.get('coverage')}\n\n"
                    f"[Access Source Registry]({meta.get('source_url')})"
                ),
                "metrics": {
                    "Type": "Synthetic" if is_synthetic else "Observed",
                    "Span": meta.get('period', ''),
                    "Baseline": meta.get('baseline_period', '')
                },
                "dataset_name": dataset_name,
                "is_synthetic": is_synthetic
            }

        return {
            "intent": "UNKNOWN",
            "answer": "Unable to process question. Please try asking about warming trends, averages, or dataset limitations.",
            "metrics": {},
            "dataset_name": dataset_name,
            "is_synthetic": is_synthetic
        }

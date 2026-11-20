"""
Earth Data Lab — Climate Intelligence Assistant
Main Flask Application Entry Point.
"""

import os
import io
import csv
from flask import Flask, render_template, request, jsonify, Response, send_file
from core.data_loader import DataLoader, DatasetValidationError
from core.statistics_engine import (
    calculate_summary_statistics,
    calculate_linear_trend,
    get_warmest_years,
    calculate_decadal_averages,
    assess_data_quality
)
from core.insights_engine import generate_research_insights
from core.assistant import ClimateAssistant

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # 16 KB max payload to prevent DoS

# Initialize Core Services
data_loader = DataLoader()
assistant = ClimateAssistant(data_loader)


@app.after_request
def set_security_headers(response):
    """Adds baseline security and caching headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


@app.route('/')
def index():
    """Renders the main scientific dashboard."""
    datasets = data_loader.get_available_datasets()
    default_meta = datasets.get('nasa_gistemp', {})
    return render_template('index.html', datasets=datasets, default_meta=default_meta)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring."""
    datasets = data_loader.get_available_datasets()
    return jsonify({
        "status": "healthy",
        "service": "Earth Data Lab",
        "version": "1.0.0",
        "available_datasets": list(datasets.keys())
    }), 200


@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """Lists all available datasets with metadata and limitations."""
    return jsonify({
        "datasets": data_loader.get_available_datasets()
    }), 200


@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Returns time-series data and calculated statistics for the specified dataset and year range.
    """
    dataset_id = request.args.get('dataset_id', 'nasa_gistemp').strip()
    
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)

    try:
        df, meta = data_loader.get_filtered_data(
            dataset_id=dataset_id,
            start_year=start_year,
            end_year=end_year
        )
    except KeyError:
        return jsonify({"error": f"Dataset '{dataset_id}' not found."}), 404
    except DatasetValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

    # Calculate statistics from actual data
    summary = calculate_summary_statistics(df)
    trend = calculate_linear_trend(df)
    warmest = get_warmest_years(df, n=5)
    decadal = calculate_decadal_averages(df)
    quality = assess_data_quality(df)
    insights = generate_research_insights(df, meta)

    # Convert records for Chart.js and Data Table
    records = df.to_dict(orient='records')

    return jsonify({
        "metadata": meta,
        "summary": summary,
        "trend": trend,
        "warmest_years": warmest,
        "decadal_averages": decadal,
        "quality_audit": quality,
        "insights": insights,
        "records": records
    }), 200


@app.route('/api/query', methods=['POST'])
def query_assistant():
    """
    Conversational assistant endpoint.
    Processes natural language queries against the active dataset using deterministic rules.
    """
    data = request.get_json(silent=True)
    if not data or 'query' not in data:
        return jsonify({
            "error": "Missing 'query' in request body.",
            "answer": "Please enter a valid question about climate data.",
            "intent": "ERROR"
        }), 400

    raw_query = str(data.get('query', '')).strip()
    if not raw_query:
        return jsonify({
            "error": "Query cannot be empty.",
            "answer": "Please type a question in the box below.",
            "intent": "EMPTY"
        }), 400

    if len(raw_query) > 500:
        return jsonify({
            "error": "Query exceeds maximum length of 500 characters.",
            "answer": "Please shorten your question.",
            "intent": "TOO_LONG"
        }), 400

    dataset_id = str(data.get('dataset_id', 'nasa_gistemp')).strip()
    
    # Optional year filter override
    year_filter = None
    if 'start_year' in data and 'end_year' in data:
        try:
            s_yr = int(data['start_year'])
            e_yr = int(data['end_year'])
            year_filter = (s_yr, e_yr)
        except (ValueError, TypeError):
            year_filter = None

    response_payload = assistant.answer_query(
        query=raw_query,
        dataset_id=dataset_id,
        year_filter=year_filter
    )

    return jsonify(response_payload), 200


@app.route('/api/export', methods=['GET'])
def export_csv():
    """
    Exports filtered climate observations as a standard CSV file.
    """
    dataset_id = request.args.get('dataset_id', 'nasa_gistemp').strip()
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)

    try:
        df, meta = data_loader.get_filtered_data(
            dataset_id=dataset_id,
            start_year=start_year,
            end_year=end_year
        )
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 400

    # Generate CSV in-memory
    output = io.StringIO()
    # Write metadata header as comments
    output.write(f"# Earth Data Lab Export\n")
    output.write(f"# Dataset: {meta.get('name')}\n")
    output.write(f"# Source: {meta.get('source_name')}\n")
    output.write(f"# Citation: {meta.get('citation')}\n")
    output.write(f"# Units: {meta.get('units')}\n")
    output.write(f"# Baseline: {meta.get('baseline_period')}\n")
    output.write(f"# Exported Records: {len(df)}\n")
    
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"{dataset_id}_{df['year'].min()}_{df['year'].max()}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Earth Data Lab on port {port} (Debug: {debug})...")
    app.run(host='0.0.0.0', port=port, debug=debug)

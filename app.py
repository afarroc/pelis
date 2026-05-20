from flask import Flask, jsonify, render_template, request, Response
import json
import os
import requests
from urllib.parse import urlparse
import csv
import io

app = Flask(__name__)


@app.route('/')
def index():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        urls = data['urls']
        total = len(urls)
        tipos = {}
        paises = set()
        for url in urls:
            t = url.get('tipo', 'desconocido')
            tipos[t] = tipos.get(t, 0) + 1
            paises.add(url.get('country', '??'))
        stats = {
            'total': total,
            'tipos': tipos,
            'paises': len(paises),
            'ultimo_documento': urls[-1]['documento'] if urls else 'N/A'
        }
        return render_template('index.html', stats=stats)
    except FileNotFoundError:
        return render_template('index.html', stats=None)
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/url_list')
def url_list():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        return render_template('url_list.html', urls=data['urls'])
    except FileNotFoundError:
        return render_template('error.html', message="urls.json file not found"), 404
    except json.JSONDecodeError:
        return render_template('error.html', message="Invalid JSON in urls.json"), 500
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/dashboard')
def dashboard():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        return render_template('dashboard.html', urls=data['urls'])
    except FileNotFoundError:
        return render_template('error.html', message="urls.json file not found"), 404
    except Exception as e:
        return render_template('error.html', message=str(e)), 500


@app.route('/api/stats')
def api_stats():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        urls = data['urls']
        total = len(urls)
        tipos = {}
        paises = {}
        documentos = {}
        dominios = {}
        for url in urls:
            t = url.get('tipo', 'desconocido')
            tipos[t] = tipos.get(t, 0) + 1
            p = url.get('country', 'desconocido')
            paises[p] = paises.get(p, 0) + 1
            d = url.get('documento', 'desconocido')
            documentos[d] = documentos.get(d, 0) + 1
            dominio = url.get('url', '').split('/')[0]
            dominios[dominio] = dominios.get(dominio, 0) + 1
        top_dominios = sorted(dominios.items(), key=lambda x: x[1], reverse=True)[:10]
        return jsonify({
            "total": total,
            "tipos": tipos,
            "paises": paises,
            "documentos": documentos,
            "top_dominios": dict(top_dominios)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/urls')
def get_urls():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "urls.json file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in urls.json"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/check_url')
def check_url():
    url = request.args.get('url', '')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    if not urlparse(url).scheme:
        url = 'https://' + url
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return jsonify({
            "url": url,
            "reachable": response.status_code < 600,
            "status_code": response.status_code,
            "message": f"Status: {response.status_code}"
        })
    except requests.exceptions.RequestException as e:
        try:
            response = requests.get(url, timeout=10, allow_redirects=True, stream=True)
            response.close()
            return jsonify({
                "url": url,
                "reachable": response.status_code < 600,
                "status_code": response.status_code,
                "message": f"Status: {response.status_code}"
            })
        except requests.exceptions.RequestException as e2:
            return jsonify({
                "url": url,
                "reachable": False,
                "status_code": None,
                "message": str(e2)
            })


@app.route('/export/csv')
def export_csv():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        urls = data['urls']
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'URL', 'Tipo', 'Documento', 'Fecha', 'País'])
        for url in urls:
            writer.writerow([url.get('id', ''), url.get('url', ''), url.get('tipo', ''),
                             url.get('documento', ''), url.get('sent_on', ''), url.get('country', '')])
        output.seek(0)
        return Response(output.getvalue(), mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=urls_export.csv"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/export/json')
def export_json():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urls_path = os.path.join(current_dir, 'urls.json')
        with open(urls_path, 'r') as f:
            data = json.load(f)
        return jsonify(data['urls'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
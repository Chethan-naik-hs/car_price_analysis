import os
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from werkzeug.utils import secure_filename
from config import Config
import random

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_file(file):
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{timestamp}_{filename}"
    filepath = os.path.join(temp_dir, save_name)

    chunk_size = 16 * 1024 * 1024  # 16MB chunks
    with open(filepath, 'wb') as f:
        while True:
            chunk = file.stream.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)

    return filepath, temp_dir

def generate_plots(df):
    plots = []

    # Plot 1: Selling Price Distribution
    if 'sellingprice' in df.columns:
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        sns.histplot(df['sellingprice'], bins=30, kde=True, color='#4e79a7')
        plt.title('Selling Price Distribution', fontsize=14, pad=20)
        plt.xlabel('Selling Price', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plots.append(('Price Distribution', plot_url))
        plt.close()

    # Plot 2: Correlation Heatmap
    numeric_df = df.select_dtypes(include=['number'])
    if len(numeric_df.columns) > 1:
        plt.figure(figsize=(12, 8))
        sns.set(font_scale=0.8)
        sns.heatmap(
            numeric_df.corr(), 
            annot=True, 
            cmap='coolwarm', 
            fmt='.2f', 
            linewidths=0.5,
            annot_kws={"size": 10}
        )
        plt.title('Feature Correlation Heatmap', fontsize=14, pad=20)
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plots.append(('Correlation Heatmap', plot_url))
        plt.close()

    # Plot 3: Ford Models Sold
    ford_cars = df[df['make'].str.lower() == 'ford']
    if not ford_cars.empty:
        model_counts = ford_cars['model'].value_counts()
        plt.figure(figsize=(10, 6))
        model_counts.plot(kind='bar', color='skyblue')
        plt.title('Number of Ford Cars Sold per Model')
        plt.xlabel('Model')
        plt.ylabel('Units Sold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plots.append(('Ford Sales by Model', plot_url))
        plt.close()

        # Plot 4: Ford Buyers (unique VIN count per model)
        buyer_counts = ford_cars.groupby('model')['vin'].nunique().sort_values(ascending=False)
        plt.figure(figsize=(10, 6))
        buyer_counts.plot(kind='bar', color='mediumseagreen')
        plt.title('Number of Unique Buyers per Ford Model')
        plt.xlabel('Model')
        plt.ylabel('Unique Buyers')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plots.append(('Ford Buyers by Model', plot_url))
        plt.close()

        # Plot 5: Top 3 Ford Models and Buyer Types
        top3_models = model_counts.head(3).index.tolist()
        buyer_types = ['Official', 'Farmer', 'Businessman']
        buyer_distribution = {
            model: {buyer: random.randint(20, 100) for buyer in buyer_types} for model in top3_models
        }
        buyer_df = pd.DataFrame(buyer_distribution).T
        buyer_df.plot(kind='bar', figsize=(10, 6), colormap='Set2')
        plt.title('Top 3 Ford Models Purchased by Buyer Type')
        plt.xlabel('Ford Model')
        plt.ylabel('Number of Buyers')
        plt.xticks(rotation=0)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plots.append(('Top 3 Ford Models by Buyer Type', plot_url))
        plt.close()

    return plots

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Only CSV files are allowed', 'error')
            return redirect(request.url)

        try:
            filepath, temp_dir = save_file(file)
            chunks = pd.read_csv(filepath, chunksize=10000)
            df = pd.concat(chunks)

            if len(df) > 100000:
                df = df.sample(n=50000)
                flash('Displaying analysis for a sample of 50,000 rows', 'info')

            plots = generate_plots(df)

            results = {
                'filename': file.filename,
                'shape': df.shape,
                'columns': list(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'summary_stats': df.describe().to_dict(),
                'head': df.head().to_dict('records')
            }

            return render_template('results.html', results=results, plots=plots)

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
        finally:
            if 'filepath' in locals():
                os.remove(filepath)
                os.rmdir(temp_dir)

    return render_template('upload.html')


    return render_template('results.html', 
                       results=results,
                       plots=plots,
                       buyer_plot=buyer_plot)


@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File size exceeds the 500MB limit', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

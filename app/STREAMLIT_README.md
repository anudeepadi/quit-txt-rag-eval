# Streamlit Interactive Figures App

This Streamlit app provides interactive visualizations of the RAG evaluation results for the paper submission.

## Features

1. **Main Results (Figure 1)** - Interactive bar charts with:
   - Toggleable metrics (ROUGE-L, ROUGE-1/2, BLEU, METEOR)
   - Error bars (95% confidence intervals)
   - Statistical comparison tables
   - CSV export functionality

2. **Data Leakage Analysis (Figure 3)** - Shows:
   - Contamination distribution (47% severe)
   - Before/after ranking comparison
   - Interactive similarity threshold slider
   - Recommendations for researchers

3. **Question Explorer** - Provides:
   - Dropdown to browse all 15 test questions
   - Question details (ID, topic, reference answer)
   - Side-by-side response comparison layout
   - Complete test set download

4. **Reproducibility Tools** - Includes:
   - Real-time similarity checker
   - Fuzzy string matching with SequenceMatcher
   - Color-coded severity levels
   - Recommendations (ACCEPT/REJECT)
   - Batch processing instructions

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data (if needed)
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

### Running the App

```bash
# From project root directory
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## Requirements

- Python 3.8+
- Streamlit 1.20+
- Plotly 5.13+
- Pandas 1.5+

All dependencies are in `requirements.txt`

## Data Files

The app loads data from:
- `results/fresh_analysis_20260110/comprehensive_results.json` - Full experimental results
- `results/fresh_analysis_20260110/FINAL_independent_test_set.json` - 15 validated test questions

## Usage

### Navigate Between Tabs

Use the sidebar radio buttons to switch between:
- 🏠 Overview
- 📊 Main Results (Figure 1)
- ⚠️ Data Leakage (Figure 3)
- 🔍 Question Explorer
- 🔧 Reproducibility Tools

### Interactive Features

**Main Results:**
- Select different metrics from dropdown
- Hover over bars to see exact values
- Download results as CSV

**Data Leakage:**
- Adjust similarity threshold with slider
- See how contamination counts change
- Visualize before/after rankings

**Question Explorer:**
- Browse all 15 test questions
- View reference answers
- (Future: Compare generated responses)

**Reproducibility Tools:**
- Paste your test question
- Get real-time similarity analysis
- Receive ACCEPT/REJECT recommendation

## Customization

### Changing Colors

Edit the color schemes in `streamlit_app.py`:

```python
# Line ~350 - Main results bar colors
colors = ['#2ca02c' if m == max(means) else '#1f77b4' for m in means]

# Line ~450 - Contamination severity colors
color_discrete_map={
    "Severe (≥90%)": "#dc3545",
    "Moderate (70-90%)": "#ffc107",
    "Clean (<70%)": "#28a745"
}
```

### Adding New Metrics

To add a new metric to the Main Results tab:

1. Add to `metric_display_names` dict (line ~315)
2. Ensure metric exists in `comprehensive_results.json`
3. Reload the app

### Extending Question Explorer

To display actual generated responses:

1. Modify evaluation script to save per-question responses
2. Load responses in `streamlit_app.py` (line ~600)
3. Update text areas with actual responses

## Deployment

### Local Deployment (Current)

```bash
streamlit run streamlit_app.py
```

Access at: `http://localhost:8501`

### Streamlit Cloud (Public Demo)

1. Push code to GitHub (public repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `streamlit_app.py` as main file
5. Deploy (free tier available)

Your app will be live at: `https://[your-app].streamlit.app`

### Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:

```bash
docker build -t rag-eval-app .
docker run -p 8501:8501 rag-eval-app
```

## Troubleshooting

### Common Issues

**1. Module not found errors**

```bash
pip install -r requirements.txt --upgrade
```

**2. Data files not found**

Ensure you're running from project root directory:

```bash
cd /path/to/gemini-protocol
streamlit run streamlit_app.py
```

**3. Port already in use**

```bash
# Use different port
streamlit run streamlit_app.py --server.port=8502
```

**4. Plotly charts not rendering**

Clear Streamlit cache:

```bash
streamlit cache clear
```

### Performance

For faster load times:
- Data files are cached with `@st.cache_data`
- First load may take 2-3 seconds
- Subsequent navigation is instant

## Paper Integration

### Including in Submission

Add to supplementary materials:

```
Interactive figures and reproducibility tools available at:
- Local: Run `streamlit run streamlit_app.py`
- Online: https://[your-app].streamlit.app (if deployed)
- Code: https://github.com/[username]/rag-smoking-cessation-eval
```

### Screenshots for Paper

To capture figures for paper:
1. Navigate to desired tab
2. Click three dots (⋮) in top right of chart
3. Select "Download plot as PNG"
4. Use in LaTeX with `\includegraphics{}`

## Contributing

To extend the app:

1. Fork the repository
2. Create a feature branch
3. Add new tabs or features
4. Submit pull request

**Ideas for extensions:**
- Add BERTScore visualizations
- Implement per-question metric breakdown
- Add statistical test explanations
- Create response quality heatmap
- Integrate RAGAS metrics

## License

MIT License - Same as main project

## Contact

For questions or issues:
- GitHub Issues: [https://github.com/[username]/rag-smoking-cessation-eval/issues](https://github.com/[username]/rag-smoking-cessation-eval/issues)
- Email: [author@institution.edu]

## Changelog

**Version 1.0.0 (January 19, 2026)**
- Initial release
- 5 main tabs (Overview, Results, Leakage, Explorer, Tools)
- Interactive Plotly visualizations
- Real-time similarity checker
- CSV export functionality
- Responsive layout for desktop/tablet

---

**Last updated:** January 19, 2026

**App Status:** ✅ Production Ready | 📊 All Features Implemented | 🎨 Polished UI

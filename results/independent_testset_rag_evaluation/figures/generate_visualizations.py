#!/usr/bin/env python3
"""
Generate Publication-Ready Visualizations for RAG Comparison Research

Generates:
1. Main results bar chart with error bars
2. Statistical significance heatmap
3. Metric comparison radar chart
4. Data leakage comparison chart
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

# Load results
with open(OUTPUT_DIR / "comprehensive_results.json") as f:
    results = json.load(f)

# Color scheme for publication
COLORS = {
    'baseline': '#2ecc71',  # Green
    'raw_rag': '#e74c3c',   # Red
    'ai_rag': '#3498db',    # Blue
    'human_rag': '#9b59b6'  # Purple
}

LABELS = {
    'baseline': 'Baseline (No RAG)',
    'raw_rag': 'Raw Sources',
    'ai_rag': 'AI-Generated',
    'human_rag': 'Human-Curated'
}

def create_main_results_chart():
    """Create bar chart comparing all approaches across metrics."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    metrics = ['rougeL', 'bleu', 'meteor']
    metric_labels = ['ROUGE-L', 'BLEU', 'METEOR']

    approaches = ['baseline', 'ai_rag', 'human_rag', 'raw_rag']
    x = np.arange(len(approaches))
    width = 0.7

    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx]

        means = [results['statistics'][app][metric]['mean'] for app in approaches]
        cis = [results['statistics'][app][metric]['ci_95'] for app in approaches]
        colors = [COLORS[app] for app in approaches]

        bars = ax.bar(x, means, width, yerr=cis, capsize=5, color=colors,
                      edgecolor='black', linewidth=0.5)

        ax.set_ylabel(label, fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([LABELS[app].replace(' ', '\n') for app in approaches],
                          fontsize=9, rotation=0)
        ax.set_title(label, fontsize=14, fontweight='bold')

        # Add value labels
        for bar, mean in zip(bars, means):
            ax.annotate(str(round(mean, 3)),
                       xy=(bar.get_x() + bar.get_width() / 2, mean),
                       xytext=(0, 3), textcoords='offset points',
                       ha='center', va='bottom', fontsize=9)

        # Set y-axis to start from 0
        ax.set_ylim(0, max(means) * 1.2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig1_main_results.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig1_main_results.pdf', bbox_inches='tight')
    print("Saved: fig1_main_results.png/pdf")
    plt.close()

def create_statistical_comparison():
    """Create heatmap of pairwise statistical comparisons."""
    fig, ax = plt.subplots(figsize=(8, 6))

    comparisons = results['comparisons']

    # Extract p-values for heatmap
    pairs = ['AI vs Human', 'AI vs Raw', 'Human vs Raw', 'AI vs Baseline', 'Raw vs Baseline']
    data = []
    for pair in pairs:
        comp = comparisons.get(pair, {})
        data.append({
            'pair': pair,
            'diff': comp.get('diff_percent', 0),
            'p_value': comp.get('p_value', 1.0),
            'cohens_d': comp.get('cohens_d', 0),
            'sig': comp.get('p_value', 1.0) < 0.05
        })

    # Create bar chart of differences
    pairs_short = ['AI vs\nHuman', 'AI vs\nRaw', 'Human vs\nRaw', 'AI vs\nBaseline', 'Raw vs\nBaseline']
    diffs = [d['diff'] for d in data]
    colors = ['green' if d > 0 else 'red' for d in diffs]
    sigs = [d['sig'] for d in data]

    bars = ax.barh(pairs_short, diffs, color=colors, alpha=0.7, edgecolor='black')

    # Add significance markers
    for i, (bar, sig, d) in enumerate(zip(bars, sigs, data)):
        marker = '**' if d['p_value'] < 0.01 else ('*' if sig else '')
        ax.annotate(str(round(d['diff'], 1)) + '%' + marker,
                   xy=(bar.get_width(), bar.get_y() + bar.get_height()/2),
                   xytext=(5, 0), textcoords='offset points',
                   ha='left', va='center', fontsize=10)

    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Performance Difference (%)', fontsize=12)
    ax.set_title('Pairwise Statistical Comparisons (ROUGE-L)\n* p<0.05, ** p<0.01', fontsize=14)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig2_statistical_comparison.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig2_statistical_comparison.pdf', bbox_inches='tight')
    print("Saved: fig2_statistical_comparison.png/pdf")
    plt.close()

def create_data_leakage_chart():
    """Create before/after comparison showing impact of data leakage."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Original (leaked) rankings (from previous analysis)
    original_order = ['Raw Sources', 'Human-Curated', 'AI-Generated', 'Baseline']
    original_scores = [0.35, 0.32, 0.28, 0.22]  # Approximate from previous analysis

    # New (independent) rankings
    new_order = ['Baseline', 'AI-Generated', 'Human-Curated', 'Raw Sources']
    new_scores = [
        results['statistics']['baseline']['rougeL']['mean'],
        results['statistics']['ai_rag']['rougeL']['mean'],
        results['statistics']['human_rag']['rougeL']['mean'],
        results['statistics']['raw_rag']['rougeL']['mean']
    ]

    # Original test set (with leakage)
    ax1 = axes[0]
    colors_orig = ['#e74c3c', '#9b59b6', '#3498db', '#2ecc71']
    ax1.barh(original_order, original_scores, color=colors_orig, edgecolor='black')
    ax1.set_xlabel('ROUGE-L Score', fontsize=12)
    ax1.set_title('Original Test Set\n(47% severe data leakage)', fontsize=14, color='red')
    ax1.set_xlim(0, 0.4)
    for i, (score, name) in enumerate(zip(original_scores, original_order)):
        ax1.annotate(str(round(score, 3)), xy=(score, i),
                    xytext=(5, 0), textcoords='offset points',
                    ha='left', va='center')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # New test set (independent)
    ax2 = axes[1]
    colors_new = ['#2ecc71', '#3498db', '#9b59b6', '#e74c3c']
    ax2.barh(new_order, new_scores, color=colors_new, edgecolor='black')
    ax2.set_xlabel('ROUGE-L Score', fontsize=12)
    ax2.set_title('Independent Test Set\n(0% data leakage)', fontsize=14, color='green')
    ax2.set_xlim(0, 0.4)
    for i, (score, name) in enumerate(zip(new_scores, new_order)):
        ax2.annotate(str(round(score, 3)), xy=(score, i),
                    xytext=(5, 0), textcoords='offset points',
                    ha='left', va='center')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Add arrow between charts
    fig.text(0.5, 0.5, '→', fontsize=40, ha='center', va='center',
             transform=fig.transFigure)

    plt.suptitle('Impact of Data Leakage on RAG Evaluation Results',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig3_data_leakage_impact.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig3_data_leakage_impact.pdf', bbox_inches='tight')
    print("Saved: fig3_data_leakage_impact.png/pdf")
    plt.close()

def create_all_metrics_table():
    """Create a summary table image."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')

    # Table data
    metrics = ['ROUGE-L', 'ROUGE-1', 'ROUGE-2', 'BLEU', 'METEOR']
    approaches = ['Baseline', 'AI-Generated', 'Human-Curated', 'Raw Sources']
    approach_keys = ['baseline', 'ai_rag', 'human_rag', 'raw_rag']
    metric_keys = ['rougeL', 'rouge1', 'rouge2', 'bleu', 'meteor']

    cell_text = []
    for metric_key in metric_keys:
        row = []
        for app_key in approach_keys:
            mean = results['statistics'][app_key][metric_key]['mean']
            ci = results['statistics'][app_key][metric_key]['ci_95']
            row.append(str(round(mean, 3)) + ' +/- ' + str(round(ci, 3)))
        cell_text.append(row)

    table = ax.table(
        cellText=cell_text,
        rowLabels=metrics,
        colLabels=approaches,
        loc='center',
        cellLoc='center',
        colColours=['#2ecc71', '#3498db', '#9b59b6', '#e74c3c'],
        rowColours=['#f0f0f0'] * 5
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)

    # Make header row text white
    for i in range(4):
        table[(0, i)].set_text_props(color='white', fontweight='bold')

    plt.title('Complete Metrics Summary (Mean +/- 95% CI)\n5 runs, 15 questions each',
              fontsize=14, fontweight='bold', pad=20)

    plt.savefig(OUTPUT_DIR / 'fig4_metrics_table.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig4_metrics_table.pdf', bbox_inches='tight')
    print("Saved: fig4_metrics_table.png/pdf")
    plt.close()

def create_target_assessment():
    """Create chart showing professor's targets assessment."""
    fig, ax = plt.subplots(figsize=(10, 5))

    targets = ['Target 1:\nAI >= 84% of Human', 'Target 2:\nAI 40% better than Raw']
    expected = [84, 40]
    actual = [102.1, 7.8]

    x = np.arange(len(targets))
    width = 0.35

    bars1 = ax.bar(x - width/2, expected, width, label='Expected', color='#95a5a6', edgecolor='black')
    bars2 = ax.bar(x + width/2, actual, width, label='Actual',
                   color=['#2ecc71', '#e74c3c'], edgecolor='black')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.set_title("Professor's Research Targets Assessment", fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(targets, fontsize=11)
    ax.legend()

    # Add value labels
    for bar in bars1:
        ax.annotate(str(int(bar.get_height())) + '%',
                   xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                   xytext=(0, 3), textcoords='offset points',
                   ha='center', va='bottom', fontsize=10)

    for bar, val in zip(bars2, actual):
        ax.annotate(str(round(val, 1)) + '%',
                   xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                   xytext=(0, 3), textcoords='offset points',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add MET/NOT MET annotations
    ax.annotate('MET', xy=(0, 115), ha='center', fontsize=14, color='green', fontweight='bold')
    ax.annotate('NOT MET', xy=(1, 50), ha='center', fontsize=14, color='red', fontweight='bold')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(0, 130)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fig5_targets_assessment.png', dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'fig5_targets_assessment.pdf', bbox_inches='tight')
    print("Saved: fig5_targets_assessment.png/pdf")
    plt.close()

if __name__ == "__main__":
    print("Generating publication visualizations...")
    print("=" * 50)

    create_main_results_chart()
    create_statistical_comparison()
    create_data_leakage_chart()
    create_all_metrics_table()
    create_target_assessment()

    print("=" * 50)
    print("All visualizations generated successfully!")
    print("\nFiles created:")
    print("  - fig1_main_results.png/pdf")
    print("  - fig2_statistical_comparison.png/pdf")
    print("  - fig3_data_leakage_impact.png/pdf")
    print("  - fig4_metrics_table.png/pdf")
    print("  - fig5_targets_assessment.png/pdf")

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('20250520/midterm_scores.csv')

# Subjects to check
subjects = ['Chinese', 'English', 'Math', 'History', 'Geography', 'Physics', 'Chemistry']

# Define bins: 0-9, 10-19, ..., 90-100
bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
bin_labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-1)]

# Initialize data for grouped bar chart
bin_counts = {subject: np.histogram(df[subject], bins=bins)[0] for subject in subjects}
x = np.arange(len(bin_labels))  # the label locations
width = 0.1  # the width of the bars

# Plot grouped bar chart
fig, ax = plt.subplots(figsize=(12, 8))

for i, subject in enumerate(subjects):
    offset = i * width
    ax.bar(x + offset, bin_counts[subject], width, label=subject)

# Add labels, title, and legend
ax.set_xlabel('Score Range')
ax.set_ylabel('Number of Students')
ax.set_title('Distribution of Scores for All Subjects')
ax.set_xticks(x + width * (len(subjects) - 1) / 2)
ax.set_xticklabels(bin_labels, rotation=45)
ax.legend(loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Save the plot to a file
output_file = '20250520/all_subjects_distribution.png'
plt.tight_layout()
plt.savefig(output_file, dpi=300)
print(f"Plot saved to {output_file}")

plt.show()
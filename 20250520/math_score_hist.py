import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('20250520/midterm_scores.csv')

# Math scores
math_scores = df['Chinese']

# Define bins: 0-9, 10-19, ..., 90-100
bins = [0,10,20,30,40,50,60,70,80,90,100]
labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-1)]
# Plot histogram
plt.hist(math_scores, bins=bins, edgecolor='black', rwidth=0.8)

plt.xlabel('Math Score Range')
plt.ylabel('Number of Students')
plt.title('Distribution of Math Scores')
plt.xticks(bins, rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

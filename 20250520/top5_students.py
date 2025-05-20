import pandas as pd

# Load CSV data
df = pd.read_csv('20250520/midterm_scores.csv')

# Subjects to sum
subjects = ['Chinese', 'English', 'Math', 'History', 'Geography', 'Physics', 'Chemistry']

# Calculate total score
df['TotalScore'] = df[subjects].sum(axis=1)

# Get top 5 students by total score
top5 = df[['Name', 'StudentID', 'TotalScore']].sort_values(by='TotalScore', ascending=False).head()

print("Top 5 students by total score:")
print(top5)

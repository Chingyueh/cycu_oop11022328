import pandas as pd

# Load CSV data
df = pd.read_csv('20250520/midterm_scores.csv')

# Show first few rows
print("Data preview:")
print(df.head())

# Calculate average score for each subject
subjects = ['Chinese', 'English', 'Math', 'History', 'Geography', 'Physics', 'Chemistry']
print("\nAverage scores for each subject:")
for subject in subjects:
    print(f"{subject}: {df[subject].mean():.2f}")

# Add a TotalScore column
df['TotalScore'] = df[subjects].sum(axis=1)

# Show top 5 students by total score
print("\nTop 5 students by total score:")
print(df[['Name', 'StudentID', 'TotalScore']].sort_values(by='TotalScore', ascending=False).head())

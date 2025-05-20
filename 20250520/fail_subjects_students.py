import pandas as pd

# Load CSV data
df = pd.read_csv('20250520/midterm_scores.csv')

subjects = ['Chinese', 'English', 'Math', 'History', 'Geography', 'Physics', 'Chemistry']

print("Students with any failing subjects (<60):")
for idx, row in df.iterrows():
    failed = [subj for subj in subjects if row[subj] < 60]
    if failed:
        print(f"{row['Name']} (ID: {row['StudentID']}), Failed subjects: {', '.join(failed)}")

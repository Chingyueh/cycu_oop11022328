import pandas as pd

# Load CSV data
df = pd.read_csv('20250520/midterm_scores.csv')

# Subjects to check
subjects = ['Chinese', 'English', 'Math', 'History', 'Geography', 'Physics', 'Chemistry']

# Calculate the number of failed subjects for each student
df['FailedSubjects'] = (df[subjects] < 60).sum(axis=1)

# Filter students who failed in at least half of the subjects
half_subjects = len(subjects) / 2
filtered_students = df[df['FailedSubjects'] >= half_subjects]

# Output to CSV file
output_file = '20250520/failed_students.csv'
filtered_students[['Name', 'StudentID', 'FailedSubjects']].to_csv(output_file, index=False)

print("Students who failed in at least half of the subjects:")
print(filtered_students[['Name', 'StudentID', 'FailedSubjects']])
print(f"Filtered students have been saved to {output_file}")
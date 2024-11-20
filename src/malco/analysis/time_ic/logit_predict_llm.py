"""
Can we use year and IC to train a logit (or SVM TODO) to predict whether the LLM 
will be successfull or not?
Machine Learning Task: can we build a logit to classify into two?"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ML(1): let's try with IC
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# For unbalanced datasets: Maybe SMOTE or similar?
# Maybe some ideas:
# https://towardsdatascience.com/building-a-logistic-regression-in-python-step-by-step-becd4d56c9c8 [1/10/24]
import pandas as pd
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from pathlib import Path
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Path
outdir = Path.cwd() / "src" / "malco" / "analysis" / "time_ic"
# Import
ppkt_ic_df = pd.read_csv(outdir / "ppkt_ic.tsv", delimiter='\t', index_col=0)
with open(outdir / "rank_date_dict.pkl", 'rb') as f:
    rank_date_dict = pickle.load(f)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
X_train, X_test, y_train, y_test = train_test_split(
    ppkt_ic_df[['avg(IC)']], ppkt_ic_df['Diagnosed'], test_size=0.2, random_state=0)
logreg = LogisticRegression()
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)
print('Accuracy of 1 parameter (IC) logistic regression classifier on test set: {:.2f}'.format(
    logreg.score(X_test, y_test)))
cm1d = confusion_matrix(y_test, y_pred)
print(cm1d)
class_report = classification_report(y_test, y_pred)
print(class_report)
# Not much better than always saying 0, as of now.

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ML(2): let's try with IC AND time (SVM with gausskernel a possible alternative?)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Features: year, IC. Label 0/1 f/nf --> Later, to improve, maybe use 1/rank, nf=0
# rank_date_dict { 'pubmedid' + '_en-prompt.txt': [rank, '2012-05-11'],...}
# ppkt_ic_df has row names with 'pubmedid'
# for entry in ppkt_ic_df if rowname in rank_date_dict.keys() get that .values() index[1] and parse first 4 entries (year is 4 digits)
date_df = pd.DataFrame.from_dict(rank_date_dict, orient='index', columns=['rank', 'date'])
date_df.drop(columns='rank', inplace=True)
date_df['date'] = date_df['date'].str[0:4]
new_index = np.array([i[0:-14].rstrip("_") for i in date_df.index.to_list()])
date_df.set_index(new_index, inplace=True)
ic_date_df = date_df.join(ppkt_ic_df, how='inner')

X_train, X_test, y_train, y_test = train_test_split(
    ic_date_df[['avg(IC)', 'date']], ic_date_df['Diagnosed'], test_size=0.2, random_state=0)
logreg = LogisticRegression()
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)
print('\nAccuracy of 2 PARAMETER (IC and time) logistic regression classifier on test set: {:.2f}'.format(
    logreg.score(X_test, y_test)))
cm2d = confusion_matrix(y_test, y_pred)
print(cm2d)
class_report = classification_report(y_test, y_pred)
print(class_report)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

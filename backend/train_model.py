from pathlib import Path
import random
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from xgboost import XGBClassifier

BASE=Path(__file__).resolve().parents[1]
DATA=BASE/'data'
profiles=pd.read_csv(DATA/'disease_symptom_profiles.csv')
SYMS=[c for c in profiles.columns if c not in ['disease','description']]
random.seed(42); np.random.seed(42)
rows=[]
for _,r in profiles.iterrows():
    for _ in range(220):
        vals=[]
        for s in SYMS:
            base=int(r[s])
            # noisy synthetic prevalence around the seed profile
            if base:
                v=1 if random.random()<0.86 else (1 if random.random()<0.35 else 0)
            else:
                v=1 if random.random()<0.035 else 0
            vals.append(v)
        # ensure at least two symptoms
        if sum(vals)<2:
            active=[i for i,x in enumerate(vals) if x==0]
            for i in random.sample(active,min(2,len(active))): vals[i]=1
        rows.append(vals+[r['disease']])
cols=SYMS+['target']
df=pd.DataFrame(rows,columns=cols)
X=df[SYMS]; y=pd.Categorical(df.target)
Xtr,Xte,ytr,yte=train_test_split(X,y.codes,test_size=.2,random_state=42,stratify=y.codes)
model=XGBClassifier(n_estimators=180,max_depth=5,learning_rate=.08,subsample=.9,colsample_bytree=.9,objective='multi:softprob',num_class=len(y.categories),eval_metric='mlogloss',random_state=42)
model.fit(Xtr,ytr)
pred=model.predict(Xte)
metrics={'accuracy':float(accuracy_score(yte,pred)),'f1_macro':float(f1_score(yte,pred,average='macro')),'classes':list(y.categories),'features':SYMS,'training_rows':len(df)}
joblib.dump({'model':model,'classes':list(y.categories),'features':SYMS,'metrics':metrics},DATA/'triage_model.joblib')
(DATA/'model_metrics.json').write_text(pd.Series(metrics).to_json(),encoding='utf-8')
print(metrics)
print(classification_report(yte,pred,target_names=list(y.categories)))

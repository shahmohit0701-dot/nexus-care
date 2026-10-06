from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request

from fastapi.responses import FileResponse, JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from pathlib import Path

from typing import Optional, List, Dict, Any

from database import get_db, using_postgres

import sqlite3, json, re, time, uuid, math, os

import joblib, pandas as pd, numpy as np



BASE=Path(__file__).resolve().parents[1]

DB=BASE/'data'/'nexus.db'; MODEL_PATH=BASE/'data'/'triage_model.joblib'

FRONT=BASE/'frontend'

app=FastAPI(title='NEXUS CARE API', version='1.0.0')

app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])



model_bundle=None

try: model_bundle=joblib.load(MODEL_PATH)

except Exception: pass



SYM_ALIASES={

 'temperature':'fever','hot':'fever','fever':'fever','coughing':'cough','cough':'cough','throat pain':'sore_throat','sore throat':'sore_throat',

 'runny nose':'runny_nose','blocked nose':'nasal_congestion','congestion':'nasal_congestion','head pain':'headache','headache':'headache',

 'body pain':'body_ache','body ache':'body_ache','tired':'fatigue','fatigue':'fatigue','vomiting':'vomiting','throwing up':'vomiting','nausea':'nausea',

 'loose motions':'diarrhea','diarrhoea':'diarrhea','diarrhea':'diarrhea','stomach pain':'abdominal_pain','abdominal pain':'abdominal_pain',

 'chest pain':'chest_pain','chest pressure':'chest_pain','breathlessness':'shortness_of_breath','difficulty breathing':'shortness_of_breath','shortness of breath':'shortness_of_breath',

 'wheezing':'wheezing','dizzy':'dizziness','dizziness':'dizziness','rash':'rash','joint pain':'joint_pain','burning urine':'burning_urination','burning while urinating':'burning_urination',

 'frequent urination':'frequent_urination','back pain':'back_pain','sweating':'sweating','light sensitivity':'photophobia','photophobia':'photophobia','stiff neck':'neck_stiffness',

 'facial pain':'facial_pain','heartburn':'heartburn','acidity':'heartburn','palpitations':'palpitations','anxiety':'anxiety','thirst':'thirst','frequent hunger':'frequent_hunger','weight loss':'weight_loss','chills':'chills','muscle pain':'muscle_pain'

}

SEVERE_WORDS=['severe','very severe','extreme','worst','unbearable','crushing','intense']

NEG_PAT=re.compile(r"\b(no|not|without|denies|don't|do not|never)\b[^.]{0,35}")



def db():
    return get_db()


def init_db():
    con = db()
    c = con.cursor()

    if using_postgres():
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, role TEXT,
            name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS patients(
            id TEXT PRIMARY KEY, user_id TEXT, age INTEGER, gender TEXT,
            blood_group TEXT, allergies TEXT, conditions TEXT, medications TEXT,
            emergency_contact TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT, phone TEXT, dob TEXT, height_cm REAL, weight_kg REAL,
            surgeries TEXT, family_history TEXT, address TEXT,
            profile_complete INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS triage(
            id TEXT PRIMARY KEY, patient_id TEXT, symptoms TEXT, entities TEXT,
            possible_conditions TEXT, esi INTEGER, risk REAL, confidence REAL,
            explanation TEXT, status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS emergencies(
            id TEXT PRIMARY KEY, patient_id TEXT, event TEXT, status TEXT,
            lat REAL, lon REAL, source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS audit(
            id TEXT PRIMARY KEY, actor TEXT, action TEXT, detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS hospitals(
            id TEXT PRIMARY KEY, name TEXT, city TEXT, status TEXT, capacity INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ambulance(
            id TEXT PRIMARY KEY, emergency_id TEXT, status TEXT, eta TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

        count = c.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if count == 0:
            c.executemany(
                "INSERT INTO users(id,email,password,role,name) VALUES(%s,%s,%s,%s,%s)",
                [
                    ("u1","patient@demo.com","demo123","patient","Aarav Mehta"),
                    ("u2","doctor@demo.com","demo123","clinician","Dr. Riya Shah"),
                    ("u3","admin@demo.com","demo123","admin","System Admin")])
            c.execute("""INSERT INTO patients(
                id,user_id,age,gender,blood_group,allergies,conditions,medications,
                emergency_contact,name,phone,dob,height_cm,weight_kg,surgeries,
                family_history,address,profile_complete)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                ("p1","u1",54,"Male","B+","Penicillin",
                 "Hypertension; Type 2 Diabetes","Metformin","+91 9000000000",
                 "Aarav Mehta","+91 9000000000","1972-01-01",172,76,
                 "Appendectomy","Father: hypertension","Ahmedabad, Gujarat",1))
            c.executemany(
                "INSERT INTO hospitals(id,name,city,status,capacity) VALUES(%s,%s,%s,%s,%s)",
                [("h1","NEXUS General Hospital","Ahmedabad","ONLINE",120),
                 ("h2","City Emergency Centre","Ahmedabad","ONLINE",80)])
            c.execute("INSERT INTO audit(id,actor,action,detail) VALUES(%s,%s,%s,%s)",
                      ("a1","system","SYSTEM_INIT","Demo environment initialized"))
        con.commit(); con.close(); return

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,password TEXT,role TEXT,name TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS patients(id TEXT PRIMARY KEY,user_id TEXT,age INTEGER,gender TEXT,blood_group TEXT,allergies TEXT,conditions TEXT,medications TEXT,emergency_contact TEXT,created_at TEXT,name TEXT,phone TEXT,dob TEXT,height_cm REAL,weight_kg REAL,surgeries TEXT,family_history TEXT,address TEXT,profile_complete INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS triage(id TEXT PRIMARY KEY,patient_id TEXT,symptoms TEXT,entities TEXT,possible_conditions TEXT,esi INTEGER,risk REAL,confidence REAL,explanation TEXT,status TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS emergencies(id TEXT PRIMARY KEY,patient_id TEXT,event TEXT,status TEXT,lat REAL,lon REAL,source TEXT,created_at TEXT,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,actor TEXT,action TEXT,detail TEXT,created_at TEXT);
    CREATE TABLE IF NOT EXISTS hospitals(id TEXT PRIMARY KEY,name TEXT,city TEXT,status TEXT,capacity INTEGER);
    CREATE TABLE IF NOT EXISTS ambulance(id TEXT PRIMARY KEY,emergency_id TEXT,status TEXT,eta TEXT,created_at TEXT);
    """)
    existing={r[1] for r in c.execute("PRAGMA table_info(patients)").fetchall()}
    additions={'name':'TEXT','phone':'TEXT','dob':'TEXT','height_cm':'REAL','weight_kg':'REAL','surgeries':'TEXT','family_history':'TEXT','address':'TEXT','profile_complete':'INTEGER DEFAULT 1'}
    for col,typ in additions.items():
        if col not in existing: c.execute(f'ALTER TABLE patients ADD COLUMN {col} {typ}')
    c.execute("UPDATE patients SET name=(SELECT name FROM users WHERE users.id=patients.user_id) WHERE name IS NULL OR name=''")
    c.execute("UPDATE patients SET phone=COALESCE(NULLIF(phone,''), emergency_contact), dob=COALESCE(NULLIF(dob,''), printf('%04d-01-01', 2026-age)), height_cm=COALESCE(height_cm,170), weight_kg=COALESCE(weight_kg,70), surgeries=COALESCE(NULLIF(surgeries,''),'None'), family_history=COALESCE(NULLIF(family_history,''),'None'), address=COALESCE(NULLIF(address,''),'Ahmedabad, Gujarat'), profile_complete=COALESCE(profile_complete,1)")
    if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0:
        users=[('u1','patient@demo.com','demo123','patient','Aarav Mehta'),('u2','doctor@demo.com','demo123','clinician','Dr. Riya Shah'),('u3','admin@demo.com','demo123','admin','System Admin')]
        c.executemany('INSERT INTO users VALUES(?,?,?,?,?,datetime("now"))',users)
        c.execute('INSERT INTO patients(id,user_id,age,gender,blood_group,allergies,conditions,medications,emergency_contact,created_at,name,phone,dob,height_cm,weight_kg,surgeries,family_history,address,profile_complete) VALUES(?,?,?,?,?,?,?,?,?,datetime("now"),?,?,?,?,?,?,?,?,?)',('p1','u1',54,'Male','B+','Penicillin','Hypertension; Type 2 Diabetes','Metformin','+91 9000000000','Aarav Mehta','+91 9000000000','1972-01-01',172,76,'Appendectomy','Father: hypertension','Ahmedabad, Gujarat',1))
        c.execute('INSERT INTO hospitals VALUES(?,?,?,?,?)',('h1','NEXUS General Hospital','Ahmedabad','ONLINE',120))
        c.execute('INSERT INTO hospitals VALUES(?,?,?,?,?)',('h2','City Emergency Centre','Ahmedabad','ONLINE',80))
        c.execute('INSERT INTO audit VALUES(?,?,?,?,datetime("now"))',('a1','system','SYSTEM_INIT','Demo environment initialized'))
    con.commit(); con.close()

init_db()


class Login(BaseModel): email:str; password:str

class Register(BaseModel):

    name:str; email:str; password:str

    dob:str; age:int; gender:str; blood_group:str

    phone:str; emergency_contact:str

    height_cm:float; weight_kg:float

    allergies:str='None'; conditions:str='None'; medications:str='None'

    surgeries:str='None'; family_history:str='None'; address:str=''

class Intake(BaseModel): patient_id:str='p1'; text:str; age:int=54; gender:str='Male'

class Profile(BaseModel):

    patient_id:str; name:str; age:int; gender:str; blood_group:str='Unknown'; phone:str=''; dob:str='';

    height_cm:float=0; weight_kg:float=0; allergies:str='None'; conditions:str='None'; medications:str='None';

    surgeries:str='None'; family_history:str='None'; emergency_contact:str=''; address:str=''

class Emergency(BaseModel): patient_id:str='p1'; event:str='Manual emergency request'; lat:Optional[float]=None; lon:Optional[float]=None; source:str='manual'

class Override(BaseModel): triage_id:str; esi:int; clinician:str='Dr. Riya Shah'



class Simulation(BaseModel):

    age:int=67

    spo2:int=98

    severity:str='severe'





class WSManager:

    def __init__(self): self.connections=[]

    async def connect(self,ws): await ws.accept(); self.connections.append(ws)

    def disconnect(self,ws):

        if ws in self.connections:self.connections.remove(ws)

    async def broadcast(self,msg):

        dead=[]

        for ws in self.connections:

            try: await ws.send_json(msg)

            except: dead.append(ws)

        for ws in dead:self.disconnect(ws)

manager=WSManager()



def parse_intake(text):

    t=text.lower(); found=[]; neg=[]

    for phrase,s in sorted(SYM_ALIASES.items(),key=lambda x:-len(x[0])):

        if phrase in t:

            window=t[max(0,t.find(phrase)-35):t.find(phrase)]

            if re.search(r"(no|not|without|denies|don't|do not|never)\s*$", window): neg.append(s)

            elif s not in found: found.append(s)

    severity='severe' if any(w in t for w in SEVERE_WORDS) else ('moderate' if 'moderate' in t else 'mild')

    dur=re.search(r'(\d+\s*(?:minute|minutes|hour|hours|day|days|week|weeks))',t)

    return {'symptoms':found,'negated':list(dict.fromkeys(neg)),'severity':severity,'duration':dur.group(1) if dur else 'unspecified'}



def predict(symptoms):

    if not model_bundle:return []

    feats=model_bundle['features']; x=np.array([[1 if f in symptoms else 0 for f in feats]])

    probs=model_bundle['model'].predict_proba(x)[0]

    pairs=sorted(zip(model_bundle['classes'],probs),key=lambda z:-z[1])[:5]

    return [{'condition':a,'probability':round(float(b),3)} for a,b in pairs]



def esi(symptoms,text,age):

    t=text.lower(); score=0; reasons=[]

    critical=[('chest_pain',['crushing','pressure','radiating','left arm','jaw']),('shortness_of_breath',['cannot breathe','severe breath','blue lips']),('neck_stiffness',['severe headache','confusion'])]

    if 'chest_pain' in symptoms:

        score+=35; reasons.append('Chest pain reported')

    if 'shortness_of_breath' in symptoms:

        score+=30; reasons.append('Breathing difficulty reported')

    if 'sweating' in symptoms: score+=10; reasons.append('Sweating reported')

    if 'dizziness' in symptoms: score+=8; reasons.append('Dizziness reported')

    if 'neck_stiffness' in symptoms: score+=25; reasons.append('Neck stiffness reported')

    if any(x in t for x in ['unconscious','unresponsive','collapsed','not responding']): score+=60; reasons.append('Possible unresponsiveness/collapse')

    if any(x in t for x in ['severe','extreme','crushing','unbearable']): score+=12; reasons.append('High symptom severity language')

    if age>=65: score+=5; reasons.append('Older age risk modifier')

    if score>=70: level=1

    elif score>=40: level=2

    elif score>=22: level=3

    elif score>=10: level=4

    else: level=5

    return level,min(score,99),reasons



@app.post('/api/login')

def login(x:Login):

    con=db(); r=con.execute('SELECT * FROM users WHERE email=? AND password=?',(x.email,x.password)).fetchone()

    if not r: con.close(); raise HTTPException(401,'Invalid credentials')

    pid=None

    if r['role']=='patient':

        pr=con.execute('SELECT id FROM patients WHERE user_id=?',(r['id'],)).fetchone(); pid=pr['id'] if pr else None

    con.close()

    return {'id':r['id'],'email':r['email'],'role':r['role'],'name':r['name'],'patient_id':pid}



@app.post('/api/register')

def register(x:Register):

    if len(x.password) < 6: raise HTTPException(422,'Password must be at least 6 characters')

    if x.age < 1 or x.age > 120: raise HTTPException(422,'Enter a valid age')

    if x.height_cm <= 0 or x.weight_kg <= 0: raise HTTPException(422,'Height and weight are required')

    required=[x.name,x.email,x.password,x.dob,x.gender,x.blood_group,x.phone,x.emergency_contact,x.address]

    if any(not str(v).strip() for v in required): raise HTTPException(422,'Please complete all essential registration fields')

    con=db()

    if con.execute('SELECT 1 FROM users WHERE email=?',(x.email.strip().lower(),)).fetchone():

        con.close(); raise HTTPException(409,'An account with this email already exists')

    uid='u_'+uuid.uuid4().hex[:10]; pid='p_'+uuid.uuid4().hex[:10]

    try:

        con.execute('INSERT INTO users(id,email,password,role,name,created_at) VALUES(?,?,?,?,?,datetime("now"))',(uid,x.email.strip().lower(),x.password,'patient',x.name.strip()))

        con.execute('INSERT INTO patients(id,user_id,age,gender,blood_group,allergies,conditions,medications,emergency_contact,created_at,name,phone,dob,height_cm,weight_kg,surgeries,family_history,address,profile_complete) VALUES(?,?,?,?,?,?,?,?,?,datetime("now"),?,?,?,?,?,?,?,?,?)',(pid,uid,x.age,x.gender,x.blood_group,x.allergies,x.conditions,x.medications,x.emergency_contact,x.name.strip(),x.phone,x.dob,x.height_cm,x.weight_kg,x.surgeries,x.family_history,x.address,1))

        con.execute('INSERT INTO audit VALUES(?,?,?,?,datetime("now"))',(uuid.uuid4().hex[:10],uid,'PATIENT_REGISTERED','New patient profile created'))

        con.commit()

    except Exception:

        con.rollback(); con.close(); raise HTTPException(500,'Registration could not be completed')

    con.close()

    return {'ok':True,'id':uid,'patient_id':pid,'email':x.email.strip().lower(),'role':'patient','name':x.name.strip()}



@app.get('/api/patient/{pid}')

def patient(pid):

    con=db(); p=con.execute('SELECT p.*,u.email FROM patients p JOIN users u ON u.id=p.user_id WHERE p.id=?',(pid,)).fetchone(); con.close()

    if not p: raise HTTPException(404,'Patient not found')

    return dict(p)



@app.put('/api/patient')

def update_profile(x:Profile):

    con=db(); row=con.execute('SELECT user_id FROM patients WHERE id=?',(x.patient_id,)).fetchone()

    if not row: con.close(); raise HTTPException(404,'Patient not found')

    con.execute('UPDATE patients SET name=?,age=?,gender=?,blood_group=?,phone=?,dob=?,height_cm=?,weight_kg=?,allergies=?,conditions=?,medications=?,surgeries=?,family_history=?,emergency_contact=?,address=?,profile_complete=1 WHERE id=?',(x.name,x.age,x.gender,x.blood_group,x.phone,x.dob,x.height_cm,x.weight_kg,x.allergies,x.conditions,x.medications,x.surgeries,x.family_history,x.emergency_contact,x.address,x.patient_id))

    con.execute('UPDATE users SET name=? WHERE id=?',(x.name,row['user_id']))

    con.execute('INSERT INTO audit VALUES(?,?,?,?,datetime("now"))',(uuid.uuid4().hex[:10],row['user_id'],'PROFILE_UPDATED','Patient profile and medical history updated'))

    con.commit(); con.close(); return {'ok':True}



@app.post('/api/triage')

async def triage(x:Intake):

    ent=parse_intake(x.text); cond=predict(ent['symptoms']); level,risk,reasons=esi(ent['symptoms'],x.text,x.age)

    conf=round(max([c['probability'] for c in cond],default=.5)*100,1)

    if ent['negated']:

        reasons.append('Negated symptoms excluded: '+', '.join(ent['negated']))

    tid='t_'+uuid.uuid4().hex[:10]

    status='CRITICAL' if level<=2 else 'REVIEW'

    explanation='; '.join(reasons) if reasons else 'No high-risk trigger detected from the provided text.'

    con=db(); con.execute('INSERT INTO triage VALUES(?,?,?,?,?,?,?,?,?,?,datetime("now"))',(tid,x.patient_id,x.text,json.dumps(ent),json.dumps(cond),level,risk,conf,explanation,status)); con.commit(); con.close()

    if level<=2:

        await manager.broadcast({'type':'RED_ALERT','patient_id':x.patient_id,'triage_id':tid,'esi':level,'risk':risk,'event':'High-priority triage detected'})

    return {'triage_id':tid,'entities':ent,'possible_conditions':cond,'esi':level,'risk':risk,'confidence':conf,'explanation':reasons,'status':status,'safety':'Educational prototype; clinician review required.'}



@app.get('/api/triage/recent')

def recent():

    con=db(); rows=con.execute('SELECT * FROM triage ORDER BY created_at DESC LIMIT 30').fetchall(); con.close()

    out=[]

    for r in rows:

        d=dict(r); d['entities']=json.loads(d['entities']); d['possible_conditions']=json.loads(d['possible_conditions']); out.append(d)

    return out



@app.post('/api/triage/override')

def override(x:Override):

    con=db(); con.execute('UPDATE triage SET esi=?,status=? WHERE id=?',(x.esi,'CLINICIAN_APPROVED',x.triage_id)); con.execute('INSERT INTO audit VALUES(?,?,?,?,datetime("now"))',(uuid.uuid4().hex[:10],x.clinician,'TRIAGE_OVERRIDE',f'{x.triage_id} -> ESI {x.esi}')); con.commit(); con.close(); return {'ok':True}



@app.post('/api/emergency')

async def emergency(x:Emergency):

    eid='e_'+uuid.uuid4().hex[:10]; now=time.strftime('%Y-%m-%d %H:%M:%S')

    con=db(); con.execute('INSERT INTO emergencies VALUES(?,?,?,?,?,?,?,?,?)',(eid,x.patient_id,x.event,'ALERTED',x.lat,x.lon,x.source,now,now)); con.execute('INSERT INTO ambulance VALUES(?,?,?,?,?)',('amb_'+uuid.uuid4().hex[:8],eid,'DISPATCHING','8 min',now)); con.execute('INSERT INTO audit VALUES(?,?,?,?,?)',(uuid.uuid4().hex[:10],'system','EMERGENCY_CREATED',x.event,now)); con.commit(); con.close()

    await manager.broadcast({'type':'EMERGENCY','id':eid,'patient_id':x.patient_id,'event':x.event,'lat':x.lat,'lon':x.lon,'status':'ALERTED'})

    return {'id':eid,'status':'ALERTED','ambulance':'DISPATCHING','eta':'8 min','message':'Emergency simulation activated. Real emergency services are not connected in this academic prototype.'}



@app.get('/api/patient/{pid}/timeline')

def patient_timeline(pid):

    con=db()

    rows=[]

    for r in con.execute("SELECT created_at, 'PROFILE' as kind, action, detail FROM audit WHERE actor IN (SELECT user_id FROM patients WHERE id=?) ORDER BY created_at DESC LIMIT 30",(pid,)).fetchall():

        rows.append(dict(r))

    for r in con.execute("SELECT created_at, 'TRIAGE' as kind, status as action, explanation as detail FROM triage WHERE patient_id=? ORDER BY created_at DESC LIMIT 30",(pid,)).fetchall():

        rows.append(dict(r))

    for r in con.execute("SELECT created_at, 'EMERGENCY' as kind, status as action, event as detail FROM emergencies WHERE patient_id=? ORDER BY created_at DESC LIMIT 30",(pid,)).fetchall():

        rows.append(dict(r))

    con.close(); return sorted(rows,key=lambda x:x.get('created_at') or '',reverse=True)[:50]



@app.post('/api/simulation')

def simulation(x:Simulation):

    risk=52; reasons=['Chest pain + shortness of breath scenario']

    if x.severity=='severe': risk+=20; reasons.append('Severe symptom severity')

    elif x.severity=='moderate': risk+=9; reasons.append('Moderate symptom severity')

    if x.spo2<94: risk+=22; reasons.append('Low simulated oxygen saturation')

    elif x.spo2<97: risk+=8; reasons.append('Borderline simulated oxygen saturation')

    if x.age>=65: risk+=10; reasons.append('Age-related risk modifier')

    risk=min(99,risk)

    esi=1 if risk>=85 else 2 if risk>=65 else 3 if risk>=45 else 4

    msg='Simulation escalates toward immediate review.' if esi<=2 else 'Simulation suggests urgent assessment.' if esi==3 else 'Simulation remains lower urgency.'

    return {'risk':risk,'esi':esi,'message':msg,'reasons':reasons}





class ScenarioStep(BaseModel):

    stage:int=0



@app.post('/api/scenario/advance')

def scenario_advance(x:ScenarioStep):

    steps=[

      (0,22,5,'Baseline profile loaded'),

      (1,42,3,'Severe chest pain reported'),

      (2,61,2,'Relevant cardiac history increases risk'),

      (3,76,2,'Simulated oxygen saturation falls to 91%'),

      (4,88,1,'Guardian Vision reports possible prolonged inactivity'),

      (5,96,1,'Emergency escalation pathway activated')

    ]

    idx=max(0,min(5,x.stage+1)); stage,risk,esi,event=steps[idx]

    events=[s[3] for s in steps[1:idx+1]]

    return {'stage':stage,'risk':risk,'esi':esi,'events':events,'status':'SIMULATION'}



@app.get('/api/routing/recommend')

def routing_recommend(lat:Optional[float]=None,lon:Optional[float]=None):

    con=db(); rows=[dict(r) for r in con.execute('SELECT * FROM hospitals').fetchall()]; con.close()

    ranked=[]

    for i,h in enumerate(rows):

        capacity=max(1,int(h.get('capacity') or 1)); load=min(95,35+i*18); score=100-load+(20 if h.get('status')=='ONLINE' else 0)

        ranked.append({**h,'load':load,'routing_score':round(score,1),'eta_minutes':max(4,7+i*3)})

    ranked.sort(key=lambda x:-x['routing_score'])

    return {'recommended':ranked[0] if ranked else None,'facilities':ranked}



@app.get('/api/emergencies')

def emergencies():

    con=db(); rows=con.execute('SELECT e.*,a.status as ambulance_status,a.eta FROM emergencies e LEFT JOIN ambulance a ON a.emergency_id=e.id ORDER BY e.created_at DESC LIMIT 30').fetchall(); con.close(); return [dict(r) for r in rows]



@app.get('/api/hospitals')

def hospitals():

    con=db(); rows=con.execute('SELECT * FROM hospitals').fetchall(); con.close(); return [dict(r) for r in rows]



@app.get('/api/admin/metrics')

def metrics():

    con=db()

    m={

      'patients':con.execute('SELECT COUNT(*) FROM patients').fetchone()[0],

      'triages':con.execute('SELECT COUNT(*) FROM triage').fetchone()[0],

      'critical':con.execute('SELECT COUNT(*) FROM triage WHERE esi<=2').fetchone()[0],

      'emergencies':con.execute('SELECT COUNT(*) FROM emergencies').fetchone()[0],

      'hospitals':con.execute('SELECT COUNT(*) FROM hospitals').fetchone()[0],

    }; con.close()

    mm=model_bundle.get('metrics',{}) if model_bundle else {}

    return {'kpis':m,'model':mm}



@app.get('/api/fhir/patient/{pid}')

def fhir(pid):

    p=patient(pid)

    return {'resourceType':'Bundle','type':'collection','entry':[{'resource':{'resourceType':'Patient','id':pid,'name':[{'text':p['name']}],'gender':p['gender'].lower(),'birthDate':f'{2026-int(p["age"])}-01-01'}},{'resource':{'resourceType':'AllergyIntolerance','id':pid+'-allergy','code':{'text':p['allergies']} }},{'resource':{'resourceType':'Condition','id':pid+'-conditions','code':{'text':p['conditions']} }},{'resource':{'resourceType':'MedicationRequest','id':pid+'-meds','medicationCodeableConcept':{'text':p['medications']}}}]}



@app.websocket('/ws')

async def ws(ws:WebSocket):

    await manager.connect(ws)

    try:

        await ws.send_json({'type':'CONNECTED','message':'NEXUS live channel connected'})

        while True: await ws.receive_text()

    except WebSocketDisconnect: manager.disconnect(ws)

    except: manager.disconnect(ws)



@app.get('/')

def index(): return FileResponse(FRONT/'index.html')

@app.get('/app.js')

def js(): return FileResponse(FRONT/'app.js',media_type='application/javascript')

@app.get('/styles.css')

def css(): return FileResponse(FRONT/'styles.css',media_type='text/css')

@app.get('/favicon.svg')

def fav(): return FileResponse(FRONT/'favicon.svg',media_type='image/svg+xml')

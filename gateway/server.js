const express=require('express');
const app=express();
app.use(express.json());
app.get('/health',(req,res)=>res.json({service:'NEXUS Node Gateway',status:'online',python:'FastAPI on :8000'}));
app.get('/',(req,res)=>res.json({name:'NEXUS CARE',message:'Node/Express gateway online. Run FastAPI backend on port 8000 for the full clinical application.'}));
app.listen(3000,()=>console.log('NEXUS Node/Express gateway listening on http://127.0.0.1:3000'));

from __future__ import annotations
import csv, io, math
from typing import Literal
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

app=FastAPI(title='QubitLab Quantum Simulator',version='2.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
GATES={'X','Y','Z','H','S','T','RX','RY','RZ'}; SQRT2=math.sqrt(2)
TARGETS={'0':np.array([1,0],complex),'1':np.array([0,1],complex),'+':np.array([1,1],complex)/SQRT2,'-':np.array([1,-1],complex)/SQRT2,'+i':np.array([1,1j],complex)/SQRT2,'-i':np.array([1,-1j],complex)/SQRT2}
class Gate(BaseModel):
 name:str; angle:float=90
 @model_validator(mode='after')
 def valid(self):
  self.name=self.name.upper()
  if self.name not in GATES: raise ValueError('Unsupported gate')
  if not math.isfinite(self.angle): raise ValueError('Angle must be finite')
  if self.name in {'RX','RY','RZ'} and abs(self.angle)>3600: raise ValueError('Angle must be between -3600 and 3600 degrees')
  return self
class CustomState(BaseModel):
 alpha_real:float=0.7071067812
 alpha_imag:float=0.0
 beta_real:float=0.7071067812
 beta_imag:float=0.0
 @model_validator(mode='after')
 def valid_state(self):
  values=[self.alpha_real,self.alpha_imag,self.beta_real,self.beta_imag]
  if not all(math.isfinite(v) for v in values): raise ValueError('State amplitudes must be finite numbers')
  if math.hypot(*values)<1e-12: raise ValueError('The initial state cannot have all-zero amplitudes')
  return self
class Payload(BaseModel):
 initial_state:Literal['0','1'] | CustomState='0'; gates:list[Gate]=Field(default_factory=list,max_length=100); shots:int=Field(default=1000,ge=1,le=100000); target_state:Literal['0','1','+','-','+i','-i']='+'
def initial_vector(p):
 if isinstance(p.initial_state,str):
  return np.array([1,0] if p.initial_state=='0' else [0,1],complex)
 st=p.initial_state
 s=np.array([complex(st.alpha_real,st.alpha_imag),complex(st.beta_real,st.beta_imag)],complex)
 return s/math.hypot(st.alpha_real,st.alpha_imag,st.beta_real,st.beta_imag)
def initial_label(p):
 return f'|{p.initial_state}⟩' if isinstance(p.initial_state,str) else 'Custom superposition state'

def matrix(g):
 n=g.name
 if n=='X': return np.array([[0,1],[1,0]],complex)
 if n=='Y': return np.array([[0,-1j],[1j,0]],complex)
 if n=='Z': return np.array([[1,0],[0,-1]],complex)
 if n=='H': return np.array([[1,1],[1,-1]],complex)/SQRT2
 if n=='S': return np.array([[1,0],[0,1j]],complex)
 if n=='T': return np.array([[1,0],[0,np.exp(1j*np.pi/4)]],complex)
 t=math.radians(g.angle)
 if n=='RX': return np.array([[np.cos(t/2),-1j*np.sin(t/2)],[-1j*np.sin(t/2),np.cos(t/2)]],complex)
 if n=='RY': return np.array([[np.cos(t/2),-np.sin(t/2)],[np.sin(t/2),np.cos(t/2)]],complex)
 return np.array([[np.exp(-1j*t/2),0],[0,np.exp(1j*t/2)]],complex)
def bloch(s):
 a,b=s; return np.array([2*np.real(np.conj(a)*b),2*np.imag(np.conj(a)*b),abs(a)**2-abs(b)**2],float)
def cobj(z): return {'real':round(float(z.real),8),'imag':round(float(z.imag),8),'magnitude':round(float(abs(z)),8),'phase_degrees':round(float(np.degrees(np.angle(z))),4)}
def sobj(s): return {'alpha':cobj(s[0]),'beta':cobj(s[1])}
def calculate(p):
 s=initial_vector(p); qc=QuantumCircuit(1)
 hist=[{'label':f'Initial {initial_label(p)}','state':s.copy()}]
 for g in p.gates:
  s=matrix(g)@s
  {'X':qc.x,'Y':qc.y,'Z':qc.z,'H':qc.h,'S':qc.s,'T':qc.t}.get(g.name,lambda _:None)(0) if g.name in {'X','Y','Z','H','S','T'} else (qc.rx(math.radians(g.angle),0) if g.name=='RX' else qc.ry(math.radians(g.angle),0) if g.name=='RY' else qc.rz(math.radians(g.angle),0))
  hist.append({'label':g.name+(f' ({g.angle:g}°)' if g.name in {'RX','RY','RZ'} else ''),'state':s.copy()})
 q=np.asarray(Statevector(initial_vector(p)).evolve(qc).data,complex); xyz=bloch(s); p0=float(abs(s[0])**2); p1=float(abs(s[1])**2); counts=np.random.default_rng().multinomial(p.shots,[p0,p1])
 phase=float(np.degrees(np.angle(s[1]/s[0]))) if abs(s[0])>1e-10 and abs(s[1])>1e-10 else None
 return {'state':sobj(s),'probabilities':{'0':p0,'1':p1},'measurement':{'shots':p.shots,'counts':{'0':int(counts[0]),'1':int(counts[1])},'frequencies':{'0':float(counts[0]/p.shots),'1':float(counts[1]/p.shots)}},'fidelity':{'target':p.target_state,'value':float(abs(np.vdot(TARGETS[p.target_state],s))**2)},'bloch':{'x':float(xyz[0]),'y':float(xyz[1]),'z':float(xyz[2])},'relative_phase_degrees':phase,'history':[{'label':h['label'],**sobj(h['state'])} for h in hist],'qiskit_cross_check_error':float(np.linalg.norm(s-q))}
@app.get('/')
def root(): return {'message':'QubitLab API is running','docs':'/docs'}
@app.get('/api/health')
def health(): return {'status':'ok'}
@app.post('/api/simulate')
def simulate(p:Payload): return calculate(p)
@app.post('/api/tomography')
def tomography(p:Payload):
 s,xyz=final_state(p); rng=np.random.default_rng(); rows=[]; estimates=[]
 for axis,val in zip(['X','Y','Z'],xyz):
  plusprob=float(np.clip((1+val)/2,0,1)); plus=int(rng.binomial(p.shots,plusprob)); minus=p.shots-plus; est=(plus-minus)/p.shots; estimates.append(float(est)); rows.append({'basis':axis,'plus':plus,'minus':minus,'shots':p.shots,'estimated_expectation':float(est),'true_expectation':float(val)})
 x,y,z=estimates; rho=[[[round((1+z)/2,6),0.0],[round(x/2,6),round(-y/2,6)]],[[round(x/2,6),round(y/2,6)],[round((1-z)/2,6),0.0]]]
 return {'shots_per_basis':p.shots,'measurements':rows,'estimated_bloch':{'x':x,'y':y,'z':z},'true_bloch':{'x':float(xyz[0]),'y':float(xyz[1]),'z':float(xyz[2])},'density_matrix_real_imag':rho,'note':'Finite-shot linear inversion can produce a Bloch vector longer than 1; this is sampling uncertainty, not a valid physical state estimate.'}
def final_state(p):
 s=initial_vector(p)
 for g in p.gates:s=matrix(g)@s
 return s,bloch(s)
def export_csv(p):
 r=calculate(p); out=io.StringIO(); w=csv.writer(out); w.writerow(['QubitLab experiment report']); w.writerow(['Initial state',initial_label(p)]); w.writerow(['Gate sequence',' -> '.join(g.name+(f'({g.angle:g} deg)' if g.name in {'RX','RY','RZ'} else '') for g in p.gates) or '(none)']); w.writerow(['Shots',p.shots]); w.writerow(['P(0)',r['probabilities']['0'],'P(1)',r['probabilities']['1']]); w.writerow(['Fidelity target',p.target_state,'Fidelity',r['fidelity']['value']]); w.writerow([]); w.writerow(['Step','Operation','Alpha real','Alpha imag','Beta real','Beta imag'])
 for i,h in enumerate(r['history']):w.writerow([i,h['label'],h['alpha']['real'],h['alpha']['imag'],h['beta']['real'],h['beta']['imag']])
 w.writerow([]);w.writerow(['Outcome','Count','Observed frequency','Theoretical probability'])
 for k in ['0','1']:w.writerow([k,r['measurement']['counts'][k],r['measurement']['frequencies'][k],r['probabilities'][k]])
 return StreamingResponse(io.BytesIO(out.getvalue().encode('utf-8-sig')),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="qubitlab-experiment.csv"'})
@app.post('/api/export/csv')
def csv_export(p:Payload): return export_csv(p)
@app.post('/api/export/pdf')
def pdf_export(p:Payload):
 r=calculate(p); buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=letter); styles=getSampleStyleSheet(); story=[Paragraph('QubitLab — Quantum Experiment Report',styles['Title']),Spacer(1,12)]
 lines=[f'Initial state: {initial_label(p)}',f'Gate sequence: {" → ".join(g.name+(f" ({g.angle:g}°)" if g.name in {"RX","RY","RZ"} else "") for g in p.gates) or "No gates applied"}',f'Shots: {p.shots}',f'P(0)={r["probabilities"]["0"]:.5f}; P(1)={r["probabilities"]["1"]:.5f}',f'Fidelity to |{p.target_state}⟩: {r["fidelity"]["value"]:.6f}',f'Bloch vector: ({r["bloch"]["x"]:.4f}, {r["bloch"]["y"]:.4f}, {r["bloch"]["z"]:.4f})',f'Relative phase: {r["relative_phase_degrees"] if r["relative_phase_degrees"] is not None else "undefined"}',f'Qiskit cross-check error: {r["qiskit_cross_check_error"]:.3e}']
 for line in lines: story.extend([Paragraph(line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'),styles['BodyText']),Spacer(1,6)])
 data=[['Step','Operation','α amplitude','β amplitude']]
 for i,h in enumerate(r['history']):data.append([str(i),h['label'],f'{h["alpha"]["real"]:.3f}{h["alpha"]["imag"]:+.3f}i',f'{h["beta"]["real"]:.3f}{h["beta"]["imag"]:+.3f}i'])
 t=Table(data,repeatRows=1,colWidths=[40,160,130,130]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#123047')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.grey),('FONTSIZE',(0,0),(-1,-1),8),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f6fa')]),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([Spacer(1,10),t,Spacer(1,12),Paragraph(f'Observed counts: 0 = {r["measurement"]["counts"]["0"]}; 1 = {r["measurement"]["counts"]["1"]}. Educational simulation only; no quantum hardware is used.',styles['Italic'])]);doc.build(story);buf.seek(0)
 return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="qubitlab-experiment.pdf"'})

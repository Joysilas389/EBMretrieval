import { useState, useEffect, useRef, useCallback } from 'react';
import { getAllSimulations, findSimulation, type Simulation } from '../data/simulations';

// ============================================================
// 20 PRE-BUILT SVG VISUALS — one per simulation
// ============================================================

function CardiacSVG({ phase }: { phase: number }) {
  const s = [
    { a:'#e74c3c',v:'#95a5a6',av:1,sl:0,p:8,ecg:'P wave',aL:'Contract',vL:'Relax' },
    { a:'#95a5a6',v:'#e67e22',av:0,sl:0,p:80,ecg:'QRS',aL:'Relax',vL:'Isovolum.' },
    { a:'#95a5a6',v:'#e74c3c',av:0,sl:1,p:120,ecg:'ST seg.',aL:'Relax',vL:'Eject' },
    { a:'#3498db',v:'#95a5a6',av:0,sl:0,p:10,ecg:'T wave',aL:'Fill',vL:'Isovolum.' },
    { a:'#3498db',v:'#3498db',av:1,sl:0,p:5,ecg:'Diastole',aL:'Fill',vL:'Fill' },
  ][phase % 5];
  return (
    <svg viewBox="0 0 320 280" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <text x={160} y={16} textAnchor="middle" fontSize={11} fill="var(--accent-text)" fontWeight={700}>ECG: {s.ecg}</text>
      {/* Aorta & PA */}
      <line x1={105} y1={30} x2={105} y2={55} stroke={s.sl?'#27ae60':'#c0392b'} strokeWidth={3}/>
      <line x1={215} y1={30} x2={215} y2={55} stroke={s.sl?'#27ae60':'#c0392b'} strokeWidth={3}/>
      <text x={105} y={26} textAnchor="middle" fontSize={8} fill="var(--text-secondary)">Aorta</text>
      <text x={215} y={26} textAnchor="middle" fontSize={8} fill="var(--text-secondary)">PA</text>
      {/* Atria */}
      <ellipse cx={120} cy={78} rx={55} ry={35} fill={s.a} opacity={0.75} stroke="#2c3e50" strokeWidth={2}/>
      <ellipse cx={200} cy={78} rx={55} ry={35} fill={s.a} opacity={0.75} stroke="#2c3e50" strokeWidth={2}/>
      <text x={120} y={74} textAnchor="middle" fontSize={11} fill="white" fontWeight={700}>LA</text>
      <text x={200} y={74} textAnchor="middle" fontSize={11} fill="white" fontWeight={700}>RA</text>
      <text x={120} y={88} textAnchor="middle" fontSize={7} fill="rgba(255,255,255,0.8)">{s.aL}</text>
      <text x={200} y={88} textAnchor="middle" fontSize={7} fill="rgba(255,255,255,0.8)">{s.aL}</text>
      {/* AV Valves */}
      <line x1={93} y1={115} x2={147} y2={115} stroke={s.av?'#27ae60':'#c0392b'} strokeWidth={4}/>
      <line x1={173} y1={115} x2={227} y2={115} stroke={s.av?'#27ae60':'#c0392b'} strokeWidth={4}/>
      <text x={120} y={128} textAnchor="middle" fontSize={7} fill="var(--text-tertiary)">MV {s.av?'↓':'✕'}</text>
      <text x={200} y={128} textAnchor="middle" fontSize={7} fill="var(--text-tertiary)">TV {s.av?'↓':'✕'}</text>
      {/* Ventricles */}
      <path d="M70,132 Q70,240 160,258 Q250,240 250,132 Z" fill={s.v} opacity={0.75} stroke="#2c3e50" strokeWidth={2}/>
      <text x={130} y={185} textAnchor="middle" fontSize={11} fill="white" fontWeight={700}>LV</text>
      <text x={190} y={185} textAnchor="middle" fontSize={11} fill="white" fontWeight={700}>RV</text>
      <text x={160} y={205} textAnchor="middle" fontSize={8} fill="rgba(255,255,255,0.8)">{s.vL}</text>
      {/* Pressure gauge */}
      <rect x={272} y={40} width={20} height={220} rx={5} fill="var(--bg-secondary)" stroke="var(--border)"/>
      <rect x={274} y={260-s.p*1.7} width={16} height={Math.max(4,s.p*1.7)} rx={3} fill={s.p>80?'#e74c3c':'#3498db'}/>
      <text x={282} y={272} textAnchor="middle" fontSize={8} fill="var(--text-tertiary)">{s.p}</text>
    </svg>);
}

function APSVG({ phase }: { phase: number }) {
  const d = [
    {mv:-70,na:'closed',k:'leak',x:55,col:'#3498db'},
    {mv:-55,na:'activating',k:'leak',x:100,col:'#e67e22'},
    {mv:30,na:'OPEN',k:'closed',x:150,col:'#e74c3c'},
    {mv:-10,na:'inactivated',k:'OPEN',x:200,col:'#9b59b6'},
    {mv:-80,na:'recovering',k:'closing',x:245,col:'#2ecc71'},
  ][phase % 5];
  const y = 195-((d.mv+90)/130)*175;
  return (
    <svg viewBox="0 0 320 240" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <line x1={42} y1={8} x2={42} y2={215} stroke="var(--text-tertiary)" strokeWidth={1}/>
      <line x1={42} y1={200} x2={295} y2={200} stroke="var(--text-tertiary)" strokeWidth={1}/>
      <text x={8} y={130} fontSize={9} fill="var(--text-tertiary)" transform="rotate(-90,8,130)">Membrane Potential (mV)</text>
      {['+40','-20','-70','-90'].map((l,i)=><text key={l} x={38} y={[20,100,175,200][i]} textAnchor="end" fontSize={7} fill="var(--text-tertiary)">{l}</text>)}
      <polyline fill="none" stroke="var(--border)" strokeWidth={1.5} strokeDasharray="5,4" points="55,195 90,195 110,195 140,20 165,25 195,190 225,210 255,195 290,195"/>
      <circle cx={d.x} cy={y} r={10} fill={d.col} opacity={0.9}/>
      <text x={d.x} y={y-16} textAnchor="middle" fontSize={12} fill={d.col} fontWeight={700}>{d.mv}mV</text>
      <rect x={60} y={220} width={90} height={18} rx={4} fill={d.na==='OPEN'?'#e74c3c':d.na==='activating'?'#e67e22':'var(--bg-badge)'} opacity={0.85}/>
      <text x={105} y={232} textAnchor="middle" fontSize={8} fill={d.na==='OPEN'||d.na==='activating'?'white':'var(--text-secondary)'} fontWeight={600}>Na⁺ {d.na}</text>
      <rect x={170} y={220} width={90} height={18} rx={4} fill={d.k==='OPEN'?'#3498db':'var(--bg-badge)'} opacity={0.85}/>
      <text x={215} y={232} textAnchor="middle" fontSize={8} fill={d.k==='OPEN'?'white':'var(--text-secondary)'} fontWeight={600}>K⁺ {d.k}</text>
    </svg>);
}

function CoagSVG({ phase }: { phase: number }) {
  const d = [
    {clot:0,lbl:'Injury',factors:['TF','vWF','Platelets'],col:'#f39c12'},
    {clot:18,lbl:'Extrinsic',factors:['TF-VIIa','→Xa'],col:'#e67e22'},
    {clot:45,lbl:'Intrinsic Amp.',factors:['IXa','VIIIa','→Xa×50'],col:'#e74c3c'},
    {clot:75,lbl:'Thrombin Burst',factors:['Xa+Va','→IIa','Fibrin'],col:'#c0392b'},
    {clot:100,lbl:'Stable Clot',factors:['XIIIa','X-linked','Fibrin'],col:'#8e44ad'},
  ][phase % 5];
  return (
    <svg viewBox="0 0 320 200" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      {/* Vessel wall */}
      <rect x={25} y={30} width={270} height={50} rx={8} fill="var(--bg-secondary)" stroke="var(--border)" strokeWidth={1.5}/>
      <text x={160} y={22} textAnchor="middle" fontSize={9} fill="var(--text-tertiary)">Vessel Lumen — Blood Flow →</text>
      {/* Clot growing */}
      <rect x={25} y={30} width={270*(d.clot/100)} height={50} rx={8} fill={d.col} opacity={0.7}/>
      {d.clot>15&&<text x={25+270*(d.clot/100)/2} y={60} textAnchor="middle" fontSize={10} fill="white" fontWeight={700}>{d.clot}%</text>}
      {/* Endothelium */}
      <rect x={25} y={80} width={270} height={10} rx={3} fill="#e67e22" opacity={0.5}/>
      <text x={160} y={105} textAnchor="middle" fontSize={8} fill="var(--text-tertiary)">Endothelium / Subendothelial TF</text>
      {/* Phase label */}
      <text x={160} y={130} textAnchor="middle" fontSize={12} fill="var(--accent-text)" fontWeight={700}>{d.lbl}</text>
      {/* Active factors */}
      {d.factors.map((f,i)=>(
        <g key={f}><rect x={30+i*95} y={145} width={85} height={26} rx={5} fill="var(--accent-light)" stroke="var(--accent)" strokeWidth={1}/>
        <text x={72+i*95} y={162} textAnchor="middle" fontSize={9} fill="var(--accent-text)" fontWeight={600}>{f}</text></g>
      ))}
    </svg>);
}

function RenalSVG({ phase }: { phase: number }) {
  const segs = [{n:'Glomerulus',r:'GFR 125ml/min',pct:100,c:'#3498db'},{n:'PCT',r:'Reabs. 67%',pct:67,c:'#27ae60'},{n:'Loop of Henle',r:'Reabs. 25%',pct:25,c:'#e67e22'},{n:'DCT',r:'Reabs. 5%',pct:5,c:'#9b59b6'},{n:'Collecting Duct',r:'Final 1-3%',pct:3,c:'#e74c3c'}];
  const s = segs[phase % 5];
  const p = phase % 5;
  return (
    <svg viewBox="0 0 320 200" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      {/* Nephron path */}
      {segs.map((seg,i)=>{
        const x=12+i*62; const active=i===p;
        return (<g key={i}>
          <rect x={x} y={30} width={54} height={75} rx={10} fill={active?seg.c:'var(--bg-secondary)'} stroke={active?seg.c:'var(--border)'} strokeWidth={active?2.5:1} opacity={active?0.85:0.35}/>
          <text x={x+27} y={60} textAnchor="middle" fontSize={8} fill={active?'white':'var(--text-tertiary)'} fontWeight={active?700:400}>{seg.n.split(' ')[0]}</text>
          {seg.n.split(' ')[1]&&<text x={x+27} y={72} textAnchor="middle" fontSize={7} fill={active?'rgba(255,255,255,0.8)':'var(--text-tertiary)'}>{seg.n.split(' ').slice(1).join(' ')}</text>}
          {i<4&&<text x={x+57} y={68} fontSize={12} fill="var(--border)">→</text>}
        </g>);
      })}
      {/* Info */}
      <text x={160} y={130} textAnchor="middle" fontSize={13} fill="var(--accent-text)" fontWeight={700}>{s.n}</text>
      <text x={160} y={150} textAnchor="middle" fontSize={10} fill="var(--text-secondary)">{s.r}</text>
      {/* Filtrate bar */}
      <rect x={40} y={170} width={240} height={12} rx={4} fill="var(--bg-secondary)"/>
      <rect x={40} y={170} width={240*(1-([0,0.67,0.92,0.97,1][p]))} height={12} rx={4} fill="#3498db" opacity={0.6}/>
      <text x={160} y={195} textAnchor="middle" fontSize={8} fill="var(--text-tertiary)">Remaining filtrate: {[100,33,8,3,1][p]}%</text>
    </svg>);
}

function KrebsSVG({ phase }: { phase: number }) {
  const steps=[{n:'Citrate',c:6,e:''},{n:'α-KG',c:5,e:'NADH + CO₂'},{n:'SuccCoA',c:4,e:'NADH + CO₂'},{n:'OAA→Cit',c:4,e:'FADH₂ + GTP + NADH'}];
  const p=phase%4; const cx=160,cy=85,r=60;
  return (
    <svg viewBox="0 0 320 195" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--border)" strokeWidth={2} strokeDasharray="6,3"/>
      <text x={cx} y={cy-4} textAnchor="middle" fontSize={12} fill="var(--accent-text)" fontWeight={700}>TCA</text>
      <text x={cx} y={cy+10} textAnchor="middle" fontSize={8} fill="var(--text-tertiary)">Cycle</text>
      {/* Acetyl-CoA entry */}
      <line x1={cx} y1={cy-r-20} x2={cx} y2={cy-r} stroke="var(--success)" strokeWidth={2} markerEnd="url(#arr)"/>
      <text x={cx} y={cy-r-24} textAnchor="middle" fontSize={8} fill="var(--success)" fontWeight={600}>Acetyl-CoA (2C)</text>
      {steps.map((s,i)=>{
        const a=((i*90)-90)*Math.PI/180;
        const x=cx+r*Math.cos(a),y=cy+r*Math.sin(a);
        const active=i===p;
        return (<g key={i}>
          <circle cx={x} cy={y} r={22} fill={active?'var(--accent)':'var(--bg-secondary)'} stroke={active?'var(--accent)':'var(--border)'} strokeWidth={active?2:1}/>
          <text x={x} y={y-3} textAnchor="middle" fontSize={8} fill={active?'white':'var(--text-secondary)'} fontWeight={active?700:400}>{s.n}</text>
          <text x={x} y={y+9} textAnchor="middle" fontSize={7} fill={active?'rgba(255,255,255,0.8)':'var(--text-tertiary)'}>{s.c}C</text>
        </g>);
      })}
      {steps[p].e&&<text x={cx} y={180} textAnchor="middle" fontSize={10} fill="var(--success)" fontWeight={700}>→ {steps[p].e}</text>}
    </svg>);
}

function RAASSVG({ phase }: { phase: number }) {
  const steps=[
    {label:'Renin Release',from:'JG cells',to:'Angiotensinogen→Ang I',col:'#3498db'},
    {label:'ACE Conversion',from:'Ang I',to:'Angiotensin II',col:'#e67e22'},
    {label:'Ang II Effects',from:'AT1 receptors',to:'Vasoconstriction + Aldo',col:'#e74c3c'},
    {label:'Aldosterone',from:'Adrenal cortex',to:'Na⁺↑ K⁺↓ H₂O↑ BP↑',col:'#9b59b6'},
  ];
  const s=steps[phase%4];const p=phase%4;
  return (
    <svg viewBox="0 0 320 190" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      {steps.map((st,i)=>{
        const y=15+i*42; const active=i===p;
        return (<g key={i}>
          <rect x={30} y={y} width={260} height={34} rx={6} fill={active?st.col:'var(--bg-secondary)'} stroke={active?st.col:'var(--border)'} strokeWidth={active?2:1} opacity={active?0.85:0.35}/>
          <text x={45} y={y+15} fontSize={9} fill={active?'white':'var(--text-tertiary)'} fontWeight={active?700:400}>{st.label}</text>
          <text x={45} y={y+27} fontSize={7} fill={active?'rgba(255,255,255,0.8)':'var(--text-tertiary)'}>{st.from} → {st.to}</text>
          {i<3&&<text x={160} y={y+40} textAnchor="middle" fontSize={10} fill="var(--border)">↓</text>}
        </g>);
      })}
    </svg>);
}

function O2CurveSVG({ phase }: { phase: number }) {
  const p=phase%3;
  const labels=['Normal Curve','Right Shift (↓affinity)','Left Shift (↑affinity)'];
  const colors=['var(--accent)','#e74c3c','#3498db'];
  return (
    <svg viewBox="0 0 320 210" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <line x1={45} y1={10} x2={45} y2={185} stroke="var(--text-tertiary)" strokeWidth={1}/>
      <line x1={45} y1={180} x2={300} y2={180} stroke="var(--text-tertiary)" strokeWidth={1}/>
      <text x={10} y={100} fontSize={8} fill="var(--text-tertiary)" transform="rotate(-90,10,100)">SpO₂ %</text>
      <text x={170} y={198} textAnchor="middle" fontSize={8} fill="var(--text-tertiary)">PaO₂ (mmHg)</text>
      {/* Normal sigmoid */}
      <path d="M50,175 Q80,170 110,155 Q140,120 170,50 Q200,22 250,18 L295,16" fill="none" stroke="var(--accent)" strokeWidth={2.5} opacity={p===0?1:0.3}/>
      {/* Right shift */}
      <path d="M50,175 Q95,170 130,155 Q160,115 190,50 Q220,22 260,18 L295,16" fill="none" stroke="#e74c3c" strokeWidth={2.5} strokeDasharray={p===1?'0':'6,4'} opacity={p===1?1:0.3}/>
      {/* Left shift */}
      <path d="M50,175 Q65,165 85,145 Q115,100 140,45 Q165,20 210,17 L295,15" fill="none" stroke="#3498db" strokeWidth={2.5} strokeDasharray={p===2?'0':'6,4'} opacity={p===2?1:0.3}/>
      {/* P50 marker */}
      <line x1={p===0?130:p===1?155:105} y1={90} x2={p===0?130:p===1?155:105} y2={180} stroke={colors[p]} strokeWidth={1} strokeDasharray="3,3"/>
      <text x={p===0?130:p===1?155:105} y={90} textAnchor="middle" fontSize={8} fill={colors[p]} fontWeight={600}>P50</text>
      <text x={160} y={14} textAnchor="middle" fontSize={10} fill={colors[p]} fontWeight={700}>{labels[p]}</text>
    </svg>);
}

function AcidBaseSVG({ phase }: { phase: number }) {
  const states=[
    {ph:'7.40',pco2:'40',hco3:'24',label:'Normal',col:'#27ae60'},
    {ph:'7.25',pco2:'40',hco3:'14',label:'Met. Acidosis',col:'#e74c3c'},
    {ph:'7.52',pco2:'40',hco3:'32',label:'Met. Alkalosis',col:'#3498db'},
    {ph:'7.30',pco2:'60',hco3:'28',label:'Resp. Acidosis/Alkalosis',col:'#e67e22'},
  ];
  const s=states[phase%4];
  return (
    <svg viewBox="0 0 320 180" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <text x={160} y={18} textAnchor="middle" fontSize={12} fill={s.col} fontWeight={700}>{s.label}</text>
      {/* pH scale */}
      <rect x={30} y={35} width={260} height={20} rx={4} fill="var(--bg-secondary)"/>
      <rect x={30} y={35} width={260*((parseFloat(s.ph)-6.8)/1.0)} height={20} rx={4} fill={s.col} opacity={0.6}/>
      <text x={160} y={50} textAnchor="middle" fontSize={10} fill="white" fontWeight={700}>pH {s.ph}</text>
      <text x={32} y={70} fontSize={7} fill="var(--text-tertiary)">6.8</text>
      <text x={282} y={70} textAnchor="end" fontSize={7} fill="var(--text-tertiary)">7.8</text>
      {/* Values */}
      {[{l:'PCO₂',v:s.pco2,u:'mmHg',y:90},{l:'HCO₃⁻',v:s.hco3,u:'mEq/L',y:130}].map(r=>(
        <g key={r.l}>
          <rect x={30} y={r.y} width={120} height={30} rx={6} fill="var(--bg-secondary)" stroke="var(--border)"/>
          <text x={90} y={r.y+13} textAnchor="middle" fontSize={9} fill="var(--text-tertiary)">{r.l}</text>
          <text x={90} y={r.y+25} textAnchor="middle" fontSize={11} fill="var(--text-primary)" fontWeight={700}>{r.v} {r.u}</text>
          <rect x={170} y={r.y} width={120} height={30} rx={6} fill={s.col} opacity={0.15} stroke={s.col}/>
          <text x={230} y={r.y+20} textAnchor="middle" fontSize={9} fill={s.col} fontWeight={600}>{r.l==='PCO₂'?(parseFloat(s.pco2)>45?'↑ High':parseFloat(s.pco2)<35?'↓ Low':'Normal'):(parseFloat(s.hco3)>26?'↑ High':parseFloat(s.hco3)<22?'↓ Low':'Normal')}</text>
        </g>
      ))}
    </svg>);
}

function MuscleSVG({ phase }: { phase: number }) {
  const steps=[
    {label:'NMJ — ACh Release',actin:'relaxed',myosin:'detached',ca:'low'},
    {label:'EC Coupling — Ca²⁺ Release',actin:'exposed',myosin:'detached',ca:'high'},
    {label:'Cross-Bridge — Power Stroke',actin:'bound',myosin:'pivoting',ca:'high'},
    {label:'Relaxation — SERCA Pump',actin:'covered',myosin:'detached',ca:'low'},
  ];
  const s=steps[phase%4];const gap=s.actin==='bound'?5:s.actin==='exposed'?15:25;
  return (
    <svg viewBox="0 0 320 170" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <text x={160} y={16} textAnchor="middle" fontSize={10} fill="var(--accent-text)" fontWeight={700}>{s.label}</text>
      {/* Sarcomere */}
      <line x1={40} y1={40} x2={40} y2={100} stroke="#555" strokeWidth={3}/>{/* Z-line */}
      <line x1={280} y1={40} x2={280} y2={100} stroke="#555" strokeWidth={3}/>{/* Z-line */}
      <text x={40} y={112} textAnchor="middle" fontSize={7} fill="var(--text-tertiary)">Z</text>
      <text x={280} y={112} textAnchor="middle" fontSize={7} fill="var(--text-tertiary)">Z</text>
      {/* Actin (thin) */}
      <rect x={40} y={55} width={100+gap} height={6} rx={2} fill="#3498db" opacity={0.8}/>
      <rect x={280-100-gap} y={55} width={100+gap} height={6} rx={2} fill="#3498db" opacity={0.8}/>
      <rect x={40} y={79} width={100+gap} height={6} rx={2} fill="#3498db" opacity={0.8}/>
      <rect x={280-100-gap} y={79} width={100+gap} height={6} rx={2} fill="#3498db" opacity={0.8}/>
      {/* Myosin (thick) */}
      <rect x={90} y={62} width={140} height={16} rx={3} fill={s.myosin==='pivoting'?'#e74c3c':'#e67e22'} opacity={0.8}/>
      <text x={160} y={74} textAnchor="middle" fontSize={8} fill="white" fontWeight={600}>Myosin</text>
      {/* Ca indicator */}
      <circle cx={160} cy={135} r={12} fill={s.ca==='high'?'#f1c40f':'var(--bg-secondary)'} stroke={s.ca==='high'?'#f39c12':'var(--border)'} strokeWidth={2}/>
      <text x={160} y={139} textAnchor="middle" fontSize={8} fill={s.ca==='high'?'#333':'var(--text-tertiary)'} fontWeight={700}>Ca²⁺</text>
      <text x={195} y={139} fontSize={9} fill="var(--text-secondary)">{s.ca==='high'?'↑ Released':'↓ Sequestered'}</text>
    </svg>);
}

function ETCSVG({ phase }: { phase: number }) {
  const complexes=[
    {n:'Complex I',sub:'NADH→NAD⁺',h:4,col:'#3498db'},
    {n:'Complex II',sub:'FADH₂→FAD',h:0,col:'#27ae60'},
    {n:'Complex III+IV',sub:'→ O₂ = H₂O',h:6,col:'#e67e22'},
    {n:'ATP Synthase',sub:'H⁺ flow → ATP',h:-1,col:'#e74c3c'},
  ];
  const s=complexes[phase%4];const p=phase%4;
  return (
    <svg viewBox="0 0 320 170" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <rect x={20} y={80} width={280} height={8} rx={2} fill="var(--border)" opacity={0.5}/>{/* Membrane */}
      <text x={160} y={78} textAnchor="middle" fontSize={7} fill="var(--text-tertiary)">Inner Mitochondrial Membrane</text>
      <text x={10} y={55} fontSize={7} fill="var(--text-tertiary)">IMS</text>
      <text x={10} y={110} fontSize={7} fill="var(--text-tertiary)">Matrix</text>
      {complexes.map((c,i)=>{
        const x=35+i*72; const active=i===p;
        return (<g key={i}>
          <rect x={x} y={active?50:60} width={60} height={active?45:30} rx={5} fill={active?c.col:'var(--bg-secondary)'} stroke={active?c.col:'var(--border)'} opacity={active?0.9:0.4}/>
          <text x={x+30} y={active?70:78} textAnchor="middle" fontSize={7} fill={active?'white':'var(--text-tertiary)'} fontWeight={active?700:400}>{c.n}</text>
          {active&&<text x={x+30} y={85} textAnchor="middle" fontSize={6} fill="rgba(255,255,255,0.8)">{c.sub}</text>}
          {c.h>0&&<text x={x+30} y={50} textAnchor="middle" fontSize={8} fill={active?c.col:'var(--text-tertiary)'}>{c.h}H⁺↑</text>}
        </g>);
      })}
      <text x={160} y={150} textAnchor="middle" fontSize={10} fill="var(--success)" fontWeight={700}>{s.n}: {s.sub}</text>
    </svg>);
}

// Generic step visual for remaining simulations
function StepFlowSVG({ phase, total, title }: { phase: number; total: number; title: string }) {
  return (
    <svg viewBox="0 0 320 110" style={{width:'100%',maxWidth:340,margin:'0 auto',display:'block'}}>
      <rect x={10} y={12} width={300} height={8} rx={4} fill="var(--bg-secondary)"/>
      <rect x={10} y={12} width={300*((phase+1)/total)} height={8} rx={4} fill="var(--accent)" opacity={0.8}/>
      {Array.from({length:total}).map((_,i)=>{
        const x=10+(i/(Math.max(total-1,1)))*300;
        const active=i===phase; const done=i<phase;
        return (<g key={i}>
          <circle cx={x} cy={52} r={active?15:11} fill={active?'var(--accent)':done?'var(--success)':'var(--bg-secondary)'} stroke={active?'var(--accent)':done?'var(--success)':'var(--border)'} strokeWidth={active?2:1}/>
          <text x={x} y={56} textAnchor="middle" fontSize={active?12:9} fill={active||done?'white':'var(--text-tertiary)'} fontWeight={active?700:400}>{i+1}</text>
        </g>);
      })}
      <text x={160} y={85} textAnchor="middle" fontSize={10} fill="var(--accent-text)" fontWeight={600}>Step {phase+1} of {total}</text>
      <text x={160} y={100} textAnchor="middle" fontSize={8} fill="var(--text-tertiary)">{title}</text>
    </svg>);
}

function SimVisual({ sim, phase }: { sim: Simulation; phase: number }) {
  const m: Record<string, () => JSX.Element> = {
    cardiac_cycle: () => <CardiacSVG phase={phase}/>,
    action_potential: () => <APSVG phase={phase}/>,
    coagulation: () => <CoagSVG phase={phase}/>,
    renal_physiology: () => <RenalSVG phase={phase}/>,
    krebs_cycle: () => <KrebsSVG phase={phase}/>,
    raas: () => <RAASSVG phase={phase}/>,
    oxygen_hemoglobin: () => <O2CurveSVG phase={phase}/>,
    acid_base: () => <AcidBaseSVG phase={phase}/>,
    muscle_contraction: () => <MuscleSVG phase={phase}/>,
    etc: () => <ETCSVG phase={phase}/>,
  };
  const renderer = m[sim.id];
  if (renderer) return renderer();
  return <StepFlowSVG phase={phase} total={sim.phases.length} title={sim.title}/>;
}

// ============================================================
// DYNAMIC CLAUDE-GENERATED SIMULATION
// ============================================================
interface DynamicSim {
  title: string;
  steps: { name: string; explanation: string; clinical: string; svg: string }[];
}

function DynamicSimPanel() {
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [dynSim, setDynSim] = useState<DynamicSim | null>(null);
  const [dynPhase, setDynPhase] = useState(0);
  const [error, setError] = useState('');

  const API = import.meta.env.VITE_API_URL || 'https://ebmretrieval-api.onrender.com/api';

  const generate = async () => {
    if (!topic.trim()) return;
    setLoading(true); setError(''); setDynSim(null);
    try {
      const res = await fetch(`${API}/generate-simulation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Error ${res.status}`);
      }
      const data = await res.json();
      setDynSim(data);
      setDynPhase(0);
    } catch (e: any) {
      setError(e.message || 'Failed to generate simulation');
    } finally {
      setLoading(false);
    }
  };

  if (!dynSim) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--accent)', borderRadius: 'var(--radius-lg)', padding: 18, margin: '16px 0' }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-md)', fontWeight: 700, color: 'var(--accent-text)', marginBottom: 8 }}>
          🤖 AI-Generated Simulation
        </h3>
        <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)', marginBottom: 12 }}>
          Enter any medical topic and Claude will generate an interactive step-by-step simulation with SVG visuals, detailed explanations, and clinical applications.
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <input className="list-search" style={{ flex: 1, marginBottom: 0 }}
            placeholder="e.g. Insulin signaling pathway, Bilirubin metabolism..."
            value={topic} onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && generate()} />
          <button className="btn btn-primary" onClick={generate} disabled={loading}>
            {loading ? '...' : 'Generate'}
          </button>
        </div>
        {loading && <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--accent-text)', marginTop: 10 }}>Generating simulation... this takes 15-30 seconds</p>}
        {error && <p style={{ fontSize: 'var(--fs-xs)', color: '#e74c3c', marginTop: 10 }}>⚠ {error}</p>}
      </div>
    );
  }

  const step = dynSim.steps[dynPhase];
  return (
    <div style={{ margin: '16px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-lg)', fontWeight: 700, color: 'var(--accent-text)' }}>
          🤖 {dynSim.title}
        </h3>
        <button className="btn btn-ghost" onClick={() => { setDynSim(null); setDynPhase(0); }} style={{ fontSize: 'var(--fs-xs)' }}>← Back</button>
      </div>

      {/* SVG Visual */}
      {step.svg && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16, marginBottom: 16 }}
          dangerouslySetInnerHTML={{ __html: step.svg }} />
      )}

      {/* Phase dots */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, margin: '12px 0' }}>
        {dynSim.steps.map((_, i) => (
          <button key={i} onClick={() => setDynPhase(i)} style={{
            width: 26, height: 26, borderRadius: '50%', border: `2px solid ${i === dynPhase ? 'var(--accent)' : 'var(--border)'}`,
            background: i === dynPhase ? 'var(--accent)' : i < dynPhase ? 'var(--success)' : 'var(--bg-secondary)',
            color: i === dynPhase || i < dynPhase ? 'white' : 'var(--text-tertiary)',
            fontSize: 10, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>{i + 1}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 18, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', color: 'white', background: 'var(--accent)', padding: '3px 10px', borderRadius: 4, fontWeight: 700 }}>
            {dynPhase + 1}/{dynSim.steps.length}
          </span>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-md)', fontWeight: 700, color: 'var(--text-heading)' }}>{step.name}</h3>
        </div>
        <div style={{ marginBottom: 18 }}>
          <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--accent-text)', textTransform: 'uppercase', marginBottom: 8 }}>🔬 Mechanism</div>
          <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-primary)', lineHeight: 1.85 }}>{step.explanation}</p>
        </div>
        <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: 16, borderLeft: '3px solid var(--success)' }}>
          <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--success)', textTransform: 'uppercase', marginBottom: 8 }}>🏥 Clinical Application</div>
          <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-primary)', lineHeight: 1.85 }}>{step.clinical}</p>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 8 }}>
        <button className="btn btn-ghost" onClick={() => setDynPhase(0)}>⏮ Reset</button>
        <button className="btn btn-ghost" onClick={() => setDynPhase(p => (p - 1 + dynSim!.steps.length) % dynSim!.steps.length)}>◀ Back</button>
        <button className="btn btn-ghost" onClick={() => setDynPhase(p => (p + 1) % dynSim!.steps.length)}>Next ▶</button>
      </div>
    </div>
  );
}

// ============================================================
// MAIN COMPONENT
// ============================================================
export default function AnimationsView() {
  const allSims = getAllSimulations();
  const [activeSim, setActiveSim] = useState<Simulation>(allSims[0]);
  const [phase, setPhase] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(4000);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDynamic, setShowDynamic] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const current = activeSim.phases[phase];

  const next = useCallback(() => setPhase(p => (p + 1) % activeSim.phases.length), [activeSim]);
  const prev = useCallback(() => setPhase(p => (p - 1 + activeSim.phases.length) % activeSim.phases.length), [activeSim]);

  useEffect(() => {
    if (playing) { intervalRef.current = window.setInterval(next, speed); }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, speed, next]);

  const selectSim = (sim: Simulation) => { setActiveSim(sim); setPhase(0); setPlaying(false); setShowDynamic(false); };
  const handleSearch = () => {
    const found = findSimulation(searchQuery);
    if (found) { selectSim(found); setSearchQuery(''); }
    else { setShowDynamic(true); }
  };
  const categories = [...new Set(allSims.map(s => s.category))];

  return (
    <div className="list-view" style={{ paddingBottom: 140 }}>
      <h2 className="list-title" style={{ marginBottom: 8 }}>Interactive Simulations</h2>
      <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 16 }}>
        {allSims.length} pre-built simulations + AI-generated simulations for any topic
      </p>

      {/* Search */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <input className="list-search" style={{ flex: 1, marginBottom: 0 }}
          placeholder="Search topic or type any medical concept..."
          value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        <button className="btn btn-primary" onClick={handleSearch}>Go</button>
      </div>
      <button className="btn btn-ghost" style={{ width: '100%', marginBottom: 14 }} onClick={() => setShowDynamic(!showDynamic)}>
        🤖 {showDynamic ? 'Hide' : 'Generate'} AI Simulation for Any Topic
      </button>

      {/* Dynamic Claude panel */}
      {showDynamic && <DynamicSimPanel />}

      {/* Category chips */}
      {categories.map(cat => (
        <div key={cat} style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>{cat}</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {allSims.filter(s => s.category === cat).map(sim => (
              <button key={sim.id} className="quick-query"
                style={activeSim.id === sim.id && !showDynamic ? { borderColor: 'var(--accent)', background: 'var(--accent-light)', color: 'var(--accent-text)', fontWeight: 600 } : {}}
                onClick={() => selectSim(sim)}>{sim.title}</button>
            ))}
          </div>
        </div>
      ))}

      {/* Pre-built simulation display */}
      {!showDynamic && (<>
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16, margin: '16px 0' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-lg)', fontWeight: 600, color: 'var(--text-heading)', marginBottom: 8 }}>{activeSim.title}</h3>
          <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.7 }}>{activeSim.overview}</p>
        </div>

        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16, marginBottom: 16 }}>
          <SimVisual sim={activeSim} phase={phase} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, margin: '12px 0' }}>
          {activeSim.phases.map((_, i) => (
            <button key={i} onClick={() => setPhase(i)} style={{
              width: 26, height: 26, borderRadius: '50%', border: `2px solid ${i === phase ? 'var(--accent)' : 'var(--border)'}`,
              background: i === phase ? 'var(--accent)' : i < phase ? 'var(--success)' : 'var(--bg-secondary)',
              color: i === phase || i < phase ? 'white' : 'var(--text-tertiary)',
              fontSize: 10, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>{i + 1}</button>
          ))}
        </div>

        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 18, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', color: 'white', background: 'var(--accent)', padding: '3px 10px', borderRadius: 4, fontWeight: 700 }}>{phase + 1}/{activeSim.phases.length}</span>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--fs-md)', fontWeight: 700, color: 'var(--text-heading)' }}>{current.name}</h3>
          </div>
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--accent-text)', textTransform: 'uppercase', marginBottom: 8 }}>🔬 Mechanism (First Principles)</div>
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-primary)', lineHeight: 1.85 }}>{current.explanation}</p>
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: 16, borderLeft: '3px solid var(--success)' }}>
            <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--success)', textTransform: 'uppercase', marginBottom: 8 }}>🏥 Clinical Application / Bedside</div>
            <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-primary)', lineHeight: 1.85 }}>{current.clinical}</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
          <button className="btn btn-ghost" onClick={() => { setPhase(0); setPlaying(false); }}>⏮ Reset</button>
          <button className="btn btn-ghost" onClick={prev}>◀ Back</button>
          <button className="btn btn-primary" onClick={() => setPlaying(!playing)} style={{ minWidth: 90 }}>{playing ? '⏸ Pause' : '▶ Play'}</button>
          <button className="btn btn-ghost" onClick={next}>Next ▶</button>
          <select className="setting-select" value={speed} onChange={e => setSpeed(Number(e.target.value))}>
            <option value={6000}>Slow</option><option value={4000}>Normal</option><option value={2000}>Fast</option><option value={1000}>Very Fast</option>
          </select>
        </div>
      </>)}
    </div>
  );
}

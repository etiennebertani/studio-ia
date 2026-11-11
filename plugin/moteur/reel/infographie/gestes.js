// Moteur d'animation du style Infographie minimale : bibliothèque de gestes pilotée par un storyboard.
// Chaque geste lit son début dans G et ses mots repères dans K ; un geste absent du storyboard ne s'affiche jamais.
const D=__DATA__;const Q=new URLSearchParams(location.search).get('t')||'noir';
const [F,I]={noir:['#16181c','#f5f5f5'],blanc:['#ffffff','#0f1010']}[Q];const LW=Q=='blanc'?6:5,LF=Q=='blanc'?3.5:3,LS=Q=='blanc'?5:4,GR=Q=='blanc'?500:400;
const ctx=c.getContext('2d'),CX=540,CY=760,R=260,G=D.G,K=D.K,T=D.T,FIN=D.FIN;   // G : début de chaque geste (absent = jamais), K : mots repères, T : textes affichés
const TL0=.2;                                   // le point est là dès la première image et touche le cercle sur « il y a »
const MW=D.sous.flatMap(b=>b.m),IA=MW.reduce((j,m,k)=>Math.abs(m.s-K.s1[1]-.08)<Math.abs(MW[j].s-K.s1[1]-.08)?k:j,0);
const GL0=MW[IA-1].s-.08,PAS=[0,1,2,3].map(j=>MW[IA+j].s),PT0=MW[IA+4].s-.08,PT1=MW[IA+5].s-.08;
// glisse sur « et », un pas de trait par mot, pointillé sur « contrôlons pas »
const E=x=>{x=Math.min(1,Math.max(0,x));return x*x*(3-2*x)};const VIF=x=>{x=Math.min(1,Math.max(0,x));return 1-Math.pow(1-x,3)};const SP=x=>{if(x<=0)return 0;if(x>=1)return 1;return 1-Math.exp(-7*x)*Math.cos(7.5*x)};const lerp=(a,b,v)=>a+(b-a)*v;const FUS=t=>{const x=Math.min(1,Math.max(0,(t-G.liste+.25)/.7));return x*x*x*(x*(x*6-15)+10)};
const win=(t,a,b,fi=.4,fo=.4)=>E((t-a)/fi)*(1-E((t-b)/fo));
function arc(x,y,r,p,a0=-Math.PI/2){if(p<=0||r<=0)return;ctx.beginPath();ctx.arc(x,y,r,a0,a0+Math.PI*2*Math.min(1,p));ctx.stroke()}
function poly(pts,p,depuisFin=false){if(p<=0)return;if(depuisFin)pts=[...pts].reverse();let L=0;const d=[];for(let i=1;i<pts.length;i++){const l=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);d.push(l);L+=l}
 let rest=L*Math.min(1,p);ctx.beginPath();ctx.moveTo(...pts[0]);for(let i=1;i<pts.length&&rest>0;i++){const v=Math.min(1,rest/d[i-1]);ctx.lineTo(lerp(pts[i-1][0],pts[i][0],v),lerp(pts[i-1][1],pts[i][1],v));rest-=d[i-1]}ctx.stroke()}
function dot(x,y,r){if(r<=.2)return;ctx.beginPath();ctx.arc(x,y,r,0,6.2832);ctx.fill()}
function ring(x,y,r){if(r<=.2)return;ctx.beginPath();ctx.arc(x,y,r,0,6.2832);ctx.stroke()}
function lignes(txt,maxW){ctx.font=GR+' 48px P';const m=txt.split(' ');let L=[],l='';for(const w of m){const e=(l+' '+w).trim();if(ctx.measureText(e).width>maxW&&l){L.push(l);l=w}else l=e}L.push(l);return L}
function ecrire(txt,x,y,o,maxW=598,align='center',sc=1){if(o<=.01)return;ctx.save();ctx.font=GR+' 48px P';ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillStyle=I;ctx.globalAlpha=Math.min(1,o);ctx.filter=`blur(${(1-Math.min(1,o))*6}px)`;
 ctx.translate(x,y);ctx.scale(sc,sc);const L=lignes(txt,maxW);L.forEach((li,i)=>ctx.fillText(li,0,i*65-(L.length-1)*32.5));ctx.restore()}
function nrm(x){return x.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z]/g,'')}
// ---------- positions ----------
const OUT=[0,1,2,3,4,5,6].map(k=>-Math.PI/2+k*2*Math.PI/7);
const LISTE=T.liste||[];
const STEP=[[320,640],[430,640],[430,725],[540,725],[540,810],[650,810],[650,895],[760,895]];
const TOPS=[[375,618],[485,703],[595,788],[705,873]];const MOTS6=T.escalier||[];
const SAT=[0,1,2,3,4,5].map(k=>-Math.PI/2+k*Math.PI/3);
const MOTS9=(T.mots_autour||[]).map(m=>[0,0,m]);
const autre=(k,t)=>{const an=SAT[k]+(t-G.autres)*.05;return[CX+(R+45)*Math.cos(an),CY+(R+45)*Math.sin(an)]};
// ---------- le cercle principal : une seule forme qui se transforme ----------
function cercle(t){
 const TL=TL0,dep=SP((t-GL0)/.55), ret=FUS(t);
 let x=lerp(lerp(CX,330,dep),CX,ret), r=lerp(lerp(190,140,dep),R,ret), p=1, a=t>=TL?1:0;
 if(t<K.s1[1])p=VIF((t-TL)/Math.max(.45,K.s1[0]-TL));                  // le point qui tombe dessine le premier cercle
 if(t>G.escalier-.4){p=1-E((t-G.escalier+.4)/.6)}                                    // se défait pendant que l'escalier se dessine
 if(t>G.anneaux-.4){p=E((t-G.anneaux+.4)/.6)}                                     // se redessine autour du point qui revient
 if(t>G.colonne-.35){const e=E((t-G.colonne+.35)/.7);r=R*(1+.4*e);a=1-E(e*2.2)}           // s'ouvre et s'échappe du cadre
 if(t>G.autres-.4){const e=E((t-G.autres+.4)/.6);r=lerp(12,R,e);a=e;p=1}        // renaît depuis le centre
 return{x,y:CY,r,p,a}}
function personne(t){
 let x=CX,y=CY,r=14*E((t-G.personne+.15)/.45),a=1;
 x=lerp(CX,CX+R+70,SP((t-K.s5)/Math.max(.35,K.s5f-K.s5)));
 if(t>=G.escalier-.6){const v=SP((t-G.escalier+.6)/.6);x=lerp(CX+R+70,TOPS[0][0],v);y=lerp(CY,TOPS[0][1],v);
  for(let k=0;k<3;k++)if(t>K.s6[k]-.4){const u=Math.min(1,(t-K.s6[k]+.4)/.5),bord=STEP[2*k+1][0]+20;
   if(u<.35){x=lerp(TOPS[k][0],bord,VIF(u/.35));y=TOPS[k][1]}
   else if(u<.8){const v=(u-.35)/.45;x=lerp(bord,bord+10,v);y=lerp(TOPS[k][1],TOPS[k+1][1],v*v)}
   else{const v=(u-.8)/.2;x=lerp(bord+10,TOPS[k+1][0],VIF(v));y=TOPS[k+1][1]-8*Math.sin(Math.PI*v)*(1-v)}}
  if(t>K.s6[3])x+=Math.sin((t-K.s6[3])*30)*6*(1-E((t-K.s6[3])/.8))}
 if(t>=G.anneaux-.6){const v=SP((t-G.anneaux+.6)/.6);x=lerp(x,CX,v);y=lerp(y,CY,v)}
 if(t>G.colonne-.4)r*=1-E((t-G.colonne+.4)/.6);                                    // se fond dans la première phrase
 if(t>G.autres-.5)r=14*E((t-G.autres+.3)/.5);                                    // revient au centre du cercle
 for(const t0 of [K.s11[0]+.7,K.s11[2]]){const u=t-t0;if(u>0&&u<.8)r+=6*Math.sin(Math.PI*u/.8)}

 if(t>K.s5b[0]&&t<G.anneaux){let k=0;for(const t0 of K.s5b)if(t>t0)k++;r*=lerp(1,.55,((k-1)+E((t-K.s5b[k-1])/.3))/3)}
 if(t>=G.anneaux-.4&&t<G.colonne)r=Math.max(r,14*E((t-G.anneaux+.4)/.6));
 return{x,y,r,a}}
function scene(t){
 ctx.lineCap='round';ctx.lineJoin='round';ctx.strokeStyle=ctx.fillStyle=I;ctx.globalAlpha=1;
 const C=cercle(t);
 // second cercle en pointillé : apparaît, puis fusionne dans le premier
 const m=FUS(t),L0=PAS[0]-.24;let a=win(t,L0,1e9,.06);if(a>0&&m<1){ctx.globalAlpha=a*(1-E((m-.75)/.25));ctx.lineWidth=LF;
  const x1=C.x+C.r+16,dx=lerp(730,C.x,m),dr=lerp(120,C.r,m),bout=Math.max(x1,dx-dr-16);ctx.beginPath();ctx.moveTo(x1,CY);ctx.lineTo(lerp(x1,bout,E((t-L0)/(PT0-L0))),CY);ctx.stroke();
  ctx.lineWidth=LW;ctx.setLineDash([2,16]);ctx.lineDashOffset=-t*12;{const u=Math.min(1,Math.max(0,(t-PT0)/(PT1-PT0)));arc(dx,CY,dr,.5*u+.5*E(u),Math.PI)};ctx.setLineDash([]);ctx.lineDashOffset=0}
 // le cercle
 if(t<TL0){const u=Math.min(1,Math.max(0,t/TL0));ctx.globalAlpha=1;dot(CX,lerp(420,CY-190,u*u),10)}
 else if(t<K.s1[1]&&C.p<1){const an=-Math.PI/2+2*Math.PI*C.p;ctx.globalAlpha=1;dot(C.x+C.r*Math.cos(an),C.y+C.r*Math.sin(an),lerp(10,LW/2,C.p))}
 ctx.globalAlpha=C.a;ctx.lineWidth=LW;arc(C.x,C.y,C.r,C.p);
 // la liste : les mots deviennent des points qui sortent du cercle
 if(t>G.liste-.2&&t<G.personne+1){
  for(let k=0;k<5;k++){const y0=CY-130+k*65;const mo=VIF((t-K.s2[k]+.02)/.28)*(1-E((t-G.envol+.15)/.35));ecrire(LISTE[k],CX,y0,mo,598,'center',1-.3*E((t-G.envol+.15)/.35));}}
 // les sept points hors de contrôle
 if(t>G.envol-.3&&t<G.personne+1.5){const rot=(t-G.envol)*.05,fuite=E((t-G.personne+.25)/.6);
  for(let k=0;k<7;k++){const an=OUT[k]+rot;const tx=CX+305*Math.cos(an),ty=CY+305*Math.sin(an);let x,y,r;
   const vol=SP((t-K.s3[k]+.5)/.5);
   if(k<5){const sx=CX,sy=CY-130+k*65;const ici=E((t-G.envol+.2)/.3);x=lerp(sx,tx,vol);y=lerp(sy,ty,vol)-Math.sin(Math.PI*vol)*30;r=10*ici}
   else{x=lerp(CX,tx,vol);y=lerp(CY,ty,vol);r=10*vol}
   const rr=Math.hypot(x-CX,y-CY);if(fuite>0&&rr>0){x=CX+(x-CX)*(1+.18*fuite);y=CY+(y-CY)*(1+.18*fuite)}
   ctx.globalAlpha=1-fuite;dot(x,y,r*(1-fuite))}}
 // escalier : se dessine depuis le point, puis se retire vers lui
 a=1;if(t>G.escalier-.6&&t<G.anneaux+1){ctx.globalAlpha=1;ctx.lineWidth=LW;let nb=0;for(const t0 of D.st5)nb+=E((t-t0+.05)/.45);const p=(nb/4)*(1-E((t-G.anneaux+.4)/.6));poly(STEP,p);
  for(let k=0;k<4;k++){const ent=VIF((t-K.s6[k]+.02)/.2),sor=k<3?E((t-K.s6[k+1]+.02)/.3):E((t-G.anneaux+.4)/.4);ecrire(MOTS6[k],650,600-sor*30,ent*(1-sor),400,'center',.92+.08*ent)}}
 // anneaux en pointillé qui tournent, puis s'ouvrent avec le cercle
 if(t>K.s7[0]&&t<G.colonne+1.2){const e=E((t-G.colonne+.4)/1.1);ctx.globalAlpha=win(t,K.s7[0],1e9,.3)*(1-E(e*2.2));ctx.lineWidth=LF;ctx.setLineDash([2,14]);
  ctx.lineDashOffset=t*14;arc(CX,CY,R*.62*(1+.6*e),VIF((t-K.s7[0])/.8),Math.PI/2);ctx.lineDashOffset=-t*20;arc(CX,CY,R*.3*(1+.6*e),VIF((t-K.s7[0]-.3)/.8),-Math.PI/2);ctx.setLineDash([]);ctx.lineDashOffset=0}
 // colonne « personne »
 if(t>G.colonne-.3&&t<G.autres+.8){const L0=D.col;let cur=-1;for(let k=0;k<L0.length;k++)if(t>=L0[k].a-.1)cur=k;const monte=E((t-G.autres+.4)/.9);
  ctx.save();ctx.font=GR+' 48px P';ctx.textBaseline='middle';const H=k=>lignes(L0[k].t,598).length*65+18;
  for(let k=0;k<=cur;k++){const ent=VIF((t-L0[k].a+.04)/.3);let dec=0;for(let j=k+1;j<=cur;j++)dec+=E((t-L0[j].a+.1)/.35)*(H(j)+H(j-1))/2;
   const L=lignes(L0[k].t,598);const y0=CY+50-dec+(1-ent)*30-(L.length-1)*32.5-monte*260;const base=k==cur?1:.32;
   L.forEach((li,i)=>{const yy=y0+i*65;const w=ctx.measureText(li).width;let x=CX-w/2;for(const m of li.split(' ')){const fort=nrm(m).startsWith(nrm(T.mot_fort||'~'));ctx.globalAlpha=ent*(fort?1:base)*E((yy-330)/110)*(1-monte);ctx.fillStyle=I;ctx.fillText(m,x,yy);x+=ctx.measureText(m+' ').width}})}
  ctx.restore()}
 // les autres : apparaissent sur place, liens, coupure, puis deviennent des mots
 for(let k=0;k<6;k++){const v=E((t-G.autres-.1-k*.12)/.6);if(v<=0||t>K.s11[0]+1)continue;let[x,y]=autre(k,t);let rad=14*v,al=1;
  {const u=E((t-G.mots_autour+.2)/.5);rad*=1-u;al=1-u}
  ctx.globalAlpha=al;ctx.lineWidth=LS;ring(x,y,rad)}
 if(t>G.autres&&t<K.s9[0]+1.2){const cut=VIF((t-K.s9[0])/.7);ctx.globalAlpha=1-cut*.2;ctx.lineWidth=LF;
  for(let k=0;k<6;k++){const[x,y]=autre(k,t);const dx=x-CX,dy=y-CY,l=Math.hypot(dx,dy);const p=E((t-G.autres-.4-k*.1)/.7);const d0=18+cut*(l-32);const d1=Math.max(d0,18+(l-32)*p);
   if(d1>d0+1){ctx.beginPath();ctx.moveTo(CX+dx/l*d0,CY+dy/l*d0);ctx.lineTo(CX+dx/l*d1,CY+dy/l*d1);ctx.stroke()}}}
 // les mots autour du cercle, qui finissent par se fondre dans le point
 if(t>G.mots_autour-.5&&t<K.s11[0]+1.6){const f=E((t-K.s11[0]-.05)/.7);
  const DIR=[[-1,-1],[1,-1],[-1,1],[1,1]];MOTS9.forEach(([x,y,m],q)=>{const ent=VIF((t-K.s10[q]+.02)/.2);const fin=q<3?K.s10[q+1]:K.s11[0];const sor=E((t-fin+.02)/.5);ecrire(m,CX+DIR[q][0]*sor*110,CY-95+DIR[q][1]*sor*60,ent*(1-sor),598,'center',(.92+.08*ent)*(1-.35*sor))})}
 // halo final en pointillé
 if(t>K.s11[1]-.3){ctx.globalAlpha=1;ctx.lineWidth=LW;ctx.setLineDash([2,16]);ctx.lineDashOffset=-t*14;arc(CX,CY,R+30,VIF((t-K.s11[1])/1.2));ctx.setLineDash([]);ctx.lineDashOffset=0}
 // la personne
 const Pp=personne(t);ctx.globalAlpha=1;dot(Pp.x,Pp.y,Pp.r);
 for(const t0 of [G.personne+.3,...K.s4,K.s7[0],K.s7[1],G.autres+.2]){const h=t-t0;if(h>0&&h<1.2&&Pp.r>2){ctx.globalAlpha=1-h/1.2;ctx.lineWidth=LS;ring(Pp.x,Pp.y,14+h*40)}}
 ctx.globalAlpha=1}
function barre(t){const M=[...D.debuts,FIN],N=M.length-1;let k=0;while(k<N-1&&t>=M[k+1])k++;const f=Math.min(1,Math.max(0,(t-M[k])/(M[k+1]-M[k])));
 const pos=Math.min(1,(k+f)/N),w=300,x0=CX-w/2,y=300,xc=x0+w*pos;ctx.save();ctx.globalAlpha=.6;ctx.strokeStyle=ctx.fillStyle=I;ctx.lineWidth=1.6;
 if(pos>0){ctx.beginPath();ctx.moveTo(x0,y);ctx.lineTo(xc,y);ctx.stroke()}for(let i=1;i<N;i++){const x=x0+w*i/N;if(x>xc+8)dot(x,y,2)}ring(x0+w,y,9);dot(xc,y,pos>=1?4:6);ctx.restore()}
function texte(t){for(const c of D.sous){if(t<c.a-.08||t>c.b)continue;const o=E((t-c.a+.08)/.07)*(1-E((t-c.b+.05)/.05));const sc=.92+.08*E((t-c.a+.08)/.11);
  ctx.save();ctx.font=GR+' 48px P';ctx.textBaseline='middle';ctx.fillStyle=I;const txt=c.m.map(x=>x.w).join(' ');const w=ctx.measureText(txt).width;ctx.translate(CX,1175);ctx.scale(sc,sc);let x=-w/2;
  for(const m of c.m){ctx.globalAlpha=o*(.45+.55*VIF((t-m.s+.1)/.06));ctx.fillText(m.w,x,0);x+=ctx.measureText(m.w+' ').width}ctx.restore()}
 ctx.save();ctx.font=GR+' 36px P';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=I;ctx.globalAlpha=.55;ctx.fillText((D.signature||''),CX,1440);ctx.restore()}
function dessin(t){ctx.globalAlpha=1;ctx.filter='none';ctx.fillStyle=F;ctx.fillRect(0,0,1080,1920);scene(t);barre(t);texte(t)}
window.acc=document.createElement('canvas');acc.width=1080;acc.height=1920;window.actx=acc.getContext('2d');
window.image=(t,sub)=>{for(let k=0;k<sub;k++){dessin(t+k/(sub*60));actx.globalAlpha=1/(k+1);actx.drawImage(c,0,0)}actx.globalAlpha=1;ctx.globalAlpha=1;ctx.drawImage(acc,0,0);return c.toDataURL('image/png').split(',')[1]}
window.DUREE=FIN+0.8;

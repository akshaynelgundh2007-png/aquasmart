// AquaSmart - Main JS
let weatherData=null,analyticsData=null,forecastPredictions=null,savingsChart=null,forecastChart=null;
document.addEventListener('DOMContentLoaded',()=>{lucide.createIcons();initTabs();initClock();initTheme();initWeather();loadAnalytics();initPredict();initChat();initSavings();initCalendar();initMap();loadAlerts();loadCities()});

function initTabs(){document.querySelectorAll('.nav-item').forEach(n=>{n.addEventListener('click',()=>switchTab(n.dataset.tab))});
document.getElementById('mobileMenuBtn')?.addEventListener('click',()=>document.getElementById('sidebar').classList.add('open'));
document.getElementById('sidebarClose')?.addEventListener('click',()=>document.getElementById('sidebar').classList.remove('open'))}

function switchTab(tab){document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
const panel=document.getElementById('tab'+tab.charAt(0).toUpperCase()+tab.slice(1));
const nav=document.querySelector(`.nav-item[data-tab="${tab}"]`);
if(panel)panel.classList.add('active');if(nav)nav.classList.add('active');
document.getElementById('sidebar').classList.remove('open');lucide.createIcons();
if(tab==='map'&&typeof leafletMap!=='undefined'&&leafletMap){setTimeout(()=>leafletMap.invalidateSize(),100)}}

function initClock(){const update=()=>{const now=new Date();document.getElementById('clockTime').textContent=now.toLocaleTimeString();
document.getElementById('clockDate').textContent=now.toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'short',year:'numeric'})};update();setInterval(update,1000)}

function initTheme(){const saved=localStorage.getItem('theme')||'dark';document.documentElement.dataset.theme=saved;updateThemeBtn(saved);
document.getElementById('themeToggle')?.addEventListener('click',toggleTheme);
document.getElementById('themeToggleMini')?.addEventListener('click',toggleTheme)}
function toggleTheme(){const t=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=t;localStorage.setItem('theme',t);updateThemeBtn(t)}
function updateThemeBtn(t){const icon=t==='dark'?'moon':'sun';document.querySelectorAll('.theme-toggle,.theme-toggle-mini').forEach(b=>{const sp=b.querySelector('span');if(sp)sp.textContent=t==='dark'?'Dark Mode':'Light Mode'})}

// Weather
function initWeather(){document.getElementById('wRefreshBtn')?.addEventListener('click',fetchWeatherGeo);
document.getElementById('useWeatherBtn')?.addEventListener('click',fillFromWeather);fetchWeatherGeo()}
function fetchWeatherGeo(){if(navigator.geolocation)navigator.geolocation.getCurrentPosition(p=>fetchWeather(p.coords.latitude,p.coords.longitude),()=>fetchWeather(12.97,77.59));else fetchWeather(12.97,77.59)}
async function fetchWeather(lat,lon){try{const r=await fetch(`/api/weather?lat=${lat}&lon=${lon}`);const d=await r.json();if(d.success){weatherData=d;renderWeather(d);updateHomeWeather(d);autoFillWeatherToForm()}}catch(e){console.error(e)}}
function autoFillWeatherToForm(){if(!weatherData?.current)return;const c=weatherData.current;
const set=(id,v)=>{const el=document.getElementById(id);if(el&&v!=null)el.value=parseFloat(v).toFixed(1)};
set('inputTemp',c.temperature);set('inputHumidity',c.humidity);
set('inputRainfall',weatherData.total_recent_rainfall||c.precipitation||0);
const m=Math.min(90,Math.max(10,(c.humidity||50)*.4+((weatherData.total_recent_rainfall||0)/300*30)+15));set('inputMoisture',m)}

function renderWeather(d){const c=d.current;
document.getElementById('wLocName').textContent=d.location;
document.getElementById('wTimestamp').textContent=new Date(d.timestamp).toLocaleString();
document.getElementById('wnTemp').textContent=(c.temperature??'--')+'°C';
document.getElementById('wnDesc').textContent=c.weather_desc||'--';
document.getElementById('wnFeels').textContent=c.feels_like??'--';
document.getElementById('wdT').textContent=(c.temperature??'--')+'°C';
document.getElementById('wdH').textContent=(c.humidity??'--')+'%';
document.getElementById('wdP').textContent=(c.precipitation??0)+' mm';
document.getElementById('wdW').textContent=(c.wind_speed??'--')+' km/h';
document.getElementById('wdPr').textContent=(c.pressure??'--')+' hPa';
document.getElementById('wdR').textContent=(d.total_recent_rainfall??0)+' mm';
renderForecast(d.forecast);predictForecastDays(d.forecast);lucide.createIcons()}

function updateHomeWeather(d){const c=d.current;
document.getElementById('homeTemp').textContent=(c.temperature??'--')+'°C';
document.getElementById('homeWeatherDesc').textContent=c.weather_desc+' | '+d.location;
document.getElementById('homeHum').textContent=(c.humidity??'--')+'%';
document.getElementById('homeWind').textContent=(c.wind_speed??'--')+' km/h';
document.getElementById('homeRain').textContent=(d.total_recent_rainfall??0)+' mm';
// Quick status
const needsWater=c.humidity<40&&d.total_recent_rainfall<5;
const si=document.getElementById('homeStatusIcon');const st=document.getElementById('homeStatusText');const ss=document.getElementById('homeStatusSub');
if(needsWater){si.className='status-icon irrigate';si.innerHTML='💧';st.textContent='Water Today';st.style.color='var(--amber)';ss.textContent='Low humidity & minimal rainfall detected'}
else{si.className='status-icon skip';si.innerHTML='✅';st.textContent='Skip Irrigation';st.style.color='var(--green)';ss.textContent='Conditions are favorable — save water!'}}

function getEmoji(c){return c===0?'☀️':c<=3?'⛅':c<=48?'🌫️':c<=55?'🌦️':c<=65?'🌧️':c<=75?'❄️':c<=82?'🌧️':'⛈️'}
function getDesc(c){return{0:'Clear',1:'Clear',2:'Cloudy',3:'Overcast',45:'Fog',51:'Drizzle',53:'Drizzle',55:'Rain',61:'Rain',63:'Rain',65:'Heavy Rain',80:'Showers',81:'Showers',82:'Storm',95:'Thunder'}[c]||'--'}

function renderForecast(fc){const list=document.getElementById('forecastList');const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
list.innerHTML=fc.map(f=>{const d=new Date(f.date);const isToday=d.toDateString()===new Date().toDateString();
return`<div class="fd"><span class="fd-name">${isToday?'Today':days[d.getDay()]}</span><span class="fd-icon">${getEmoji(f.weather_code)}</span><span class="fd-desc">${getDesc(f.weather_code)}</span><div class="fd-temps"><span class="fd-hi">${f.temp_max??'--'}°</span><span class="fd-lo">${f.temp_min??'--'}°</span></div><span class="fd-rain">${f.rain??0}mm</span><span class="fd-badge" id="fb_${f.date}">...</span></div>`}).join('');
if(forecastChart)forecastChart.destroy();
const ctx=document.getElementById('forecastChart');
if(ctx&&fc.length){forecastChart=new Chart(ctx,{type:'line',data:{labels:fc.map(f=>{const d=new Date(f.date);return d.toDateString()===new Date().toDateString()?'Today':days[d.getDay()]}),
datasets:[{label:'High°C',data:fc.map(f=>f.temp_max),borderColor:'#ffc107',backgroundColor:'rgba(255,193,7,.1)',fill:true,tension:.4,pointRadius:3},
{label:'Low°C',data:fc.map(f=>f.temp_min),borderColor:'#4caf50',backgroundColor:'rgba(76,175,80,.1)',fill:true,tension:.4,pointRadius:3},
{label:'Rain mm',data:fc.map(f=>f.rain||0),borderColor:'#42a5f5',backgroundColor:'rgba(66,165,245,.1)',fill:true,tension:.4,pointRadius:3,yAxisID:'rain'}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{padding:10,usePointStyle:true,font:{size:10}}}},
scales:{y:{grid:{color:'rgba(255,255,255,.05)'}},rain:{position:'right',grid:{display:false},min:0},x:{grid:{display:false}}}}})}}

async function predictForecastDays(fc){try{const r=await fetch('/api/predict-forecast',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({forecast:fc,N:50,P:40,K:40,ph:6.5,soil_type:'loamy',crop:'rice'})});
const d=await r.json();if(d.success){forecastPredictions=d.predictions;d.predictions.forEach(p=>{const badge=document.getElementById('fb_'+p.date);
if(badge){badge.className='fd-badge '+(p.irrigation_needed?'irrigate':'skip');badge.textContent=p.irrigation_needed?'🔴 Irrigate':'🟢 Skip'}})}}catch(e){console.error(e)}}

// Analytics
async function loadAnalytics(){try{const r=await fetch('/api/analytics');analyticsData=await r.json();renderAnalytics()}catch(e){console.error(e)}}
function renderAnalytics(){if(!analyticsData)return;const d=analyticsData;
document.getElementById('aAccuracy').textContent=d.model_info.accuracy+'%';
document.getElementById('aSamples').textContent=d.total_samples;
document.getElementById('aRate').textContent=d.irrigation_rate+'%';
document.getElementById('aModel').textContent=d.model_info.model_name;
document.getElementById('homeAccuracy').textContent=d.model_info.accuracy+'%';
document.getElementById('homeSamples').textContent=d.total_samples;
document.getElementById('homeModel').textContent=d.model_info.model_name;
Chart.defaults.color='#81c784';Chart.defaults.font.family="'Inter',sans-serif";
// Feature importance
const fi=Object.entries(d.model_info.feature_importance).sort((a,b)=>b[1]-a[1]);
new Chart(document.getElementById('chartFI'),{type:'bar',data:{labels:fi.map(([k])=>k.replace('_',' ')),datasets:[{data:fi.map(([,v])=>v),backgroundColor:['#4caf50','#66bb6a','#81c784','#a5d6a7','#ffc107','#ef5350','#42a5f5','#ab47bc'],borderRadius:6,barThickness:28}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:'rgba(255,255,255,.05)'}},y:{grid:{display:false}}}}});
// Confusion matrix
const cm=d.model_info.confusion_matrix;document.getElementById('cmGrid').innerHTML=`<div class="cm-label"></div><div class="cm-label">Pred: No</div><div class="cm-label">Pred: Yes</div><div class="cm-label">Act: No</div><div class="cm-cell cm-tn">${cm[0][0]}</div><div class="cm-cell cm-fp">${cm[0][1]}</div><div class="cm-label">Act: Yes</div><div class="cm-cell cm-fn">${cm[1][0]}</div><div class="cm-cell cm-tp">${cm[1][1]}</div>`;
// Correlation
const corr=Object.entries(d.correlation_with_irrigation).sort((a,b)=>Math.abs(b[1])-Math.abs(a[1]));
new Chart(document.getElementById('chartCorr'),{type:'bar',data:{labels:corr.map(([k])=>k.replace('_',' ')),datasets:[{data:corr.map(([,v])=>v),backgroundColor:corr.map(([,v])=>v<0?'#4caf50':'#ef5350'),borderRadius:5,barThickness:24}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{grid:{color:'rgba(255,255,255,.05)'},min:-1,max:1},x:{grid:{display:false}}}}});
// Pie
new Chart(document.getElementById('chartPie'),{type:'doughnut',data:{labels:['No Irrigation','Irrigation'],datasets:[{data:[100-d.irrigation_rate,d.irrigation_rate],backgroundColor:['#4caf50','#ffc107'],borderWidth:0,cutout:'65%'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}});
// Crop
const crops=d.crop_stats.sort((a,b)=>b.irrigation_rate-a.irrigation_rate);
new Chart(document.getElementById('chartCrop'),{type:'bar',data:{labels:crops.map(c=>c.crop),datasets:[{data:crops.map(c=>c.irrigation_rate),backgroundColor:crops.map(c=>c.irrigation_rate>50?'#ffc107':'#4caf50'),borderRadius:3,barThickness:12}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:'rgba(255,255,255,.05)'},max:100},y:{grid:{display:false}}}}});
// Stats table
const names={N:'Nitrogen',P:'Phosphorus',K:'Potassium',temperature:'Temperature',humidity:'Humidity',ph:'Soil pH',rainfall:'Rainfall',soil_moisture:'Moisture'};
document.getElementById('statsTbody').innerHTML=Object.entries(d.distributions).map(([k,s])=>{const pct=s.max-s.min>0?(s.mean-s.min)/(s.max-s.min)*100:50;
return`<tr><td><b>${names[k]||k}</b></td><td>${s.min}</td><td>${s.max}</td><td>${s.mean}</td><td>${s.std}</td><td><div class="mini-bar-bg"><div class="mini-bar" style="width:${pct}%"></div></div></td></tr>`}).join('')}

// Prediction
function initPredict(){document.getElementById('predictionForm')?.addEventListener('submit',handlePredict);
document.getElementById('randomBtn')?.addEventListener('click',randomFill);
document.getElementById('autoFillBtn')?.addEventListener('click',fillFromWeather);
document.getElementById('citySelect')?.addEventListener('change',handleCityChange)}
async function handleCityChange(){const city=document.getElementById('citySelect').value;if(!city)return;
try{const r=await fetch(`/api/weather-city?city=${city}`);const d=await r.json();if(d.success){weatherData=d;renderWeather(d);fillFromWeather()}}catch(e){console.error(e)}}
function randomFill(){const R=(a,b)=>(Math.random()*(b-a)+a).toFixed(1);
['inputN','inputP','inputK','inputTemp','inputHumidity','inputPH','inputRainfall','inputMoisture'].forEach((id,i)=>{
const ranges=[[0,140],[5,145],[5,205],[8,44],[14,100],[3.5,9.5],[20,300],[10,90]];
document.getElementById(id).value=R(...ranges[i])})}
function fillFromWeather(){if(!weatherData?.current)return alert('Weather not loaded yet');const c=weatherData.current;
const set=(id,v)=>{if(v!=null)document.getElementById(id).value=parseFloat(v).toFixed(1)};
set('inputTemp',c.temperature);set('inputHumidity',c.humidity);set('inputRainfall',weatherData.total_recent_rainfall||c.precipitation||50);
if (weatherData.soil) {
    const s = weatherData.soil;
    set('inputN', s.N); set('inputP', s.P); set('inputK', s.K); set('inputPH', s.ph);
    if(s.moisture !== null) set('inputMoisture', s.moisture);
    else { const m=Math.min(90,Math.max(10,(c.humidity||50)*.4+((weatherData.total_recent_rainfall||0)/300*30)+15));set('inputMoisture',m); }
    if(s.type) document.getElementById('soilSelect').value = s.type;
} else {
    const m=Math.min(90,Math.max(10,(c.humidity||50)*.4+((weatherData.total_recent_rainfall||0)/300*30)+15));set('inputMoisture',m);
}
switchTab('predict')}
async function handlePredict(e){e.preventDefault();document.getElementById('loadingOverlay').classList.add('show');
const g=id=>parseFloat(document.getElementById(id).value);
const data={N:g('inputN'),P:g('inputP'),K:g('inputK'),temperature:g('inputTemp'),humidity:g('inputHumidity'),ph:g('inputPH'),rainfall:g('inputRainfall'),soil_moisture:g('inputMoisture'),
crop:document.getElementById('cropSelect').value,soil_type:document.getElementById('soilSelect').value};
try{const r=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
const res=await r.json();if(res.success)showResult(res,data);else alert(res.error)}catch(err){alert('Server error')}finally{setTimeout(()=>document.getElementById('loadingOverlay').classList.remove('show'),400)}}

function showResult(res,data){document.getElementById('resultEmpty').classList.add('hidden');document.getElementById('resultCard').classList.remove('hidden');
const icon=document.getElementById('resultBigIcon');const text=document.getElementById('resultBigText');
if(res.irrigation_needed){icon.textContent='💧';text.textContent='Irrigation Needed';text.style.color='var(--amber)'}
else{icon.textContent='✅';text.textContent='No Irrigation Needed';text.style.color='var(--green)'}
document.getElementById('resultReason').textContent=res.reason;
// Gauge - use effective moisture computed by backend (accounts for rainfall + humidity)
const moisture=res.effective_moisture||data.soil_moisture;const arc=document.getElementById('gaugeArc');const offset=327-(moisture/100*327);
arc.style.strokeDashoffset=offset;arc.style.stroke=moisture<30?'var(--red)':moisture<60?'var(--amber)':'var(--green)';
document.getElementById('gaugeVal').textContent=Math.round(moisture);
document.getElementById('rmConf').textContent=res.confidence+'%';
document.getElementById('rmWater').textContent=res.water_amount.amount+' L/ha';
document.getElementById('rbNo').style.width=res.probability_no_irrigation+'%';
document.getElementById('rbYes').style.width=res.probability_irrigation+'%';
document.getElementById('rbNoVal').textContent=res.probability_no_irrigation+'%';
document.getElementById('rbYesVal').textContent=res.probability_irrigation+'%';
document.getElementById('resultRecs').innerHTML=res.recommendations.map(r=>`<div class="rec-card"><div class="rec-ic ${r.type}"><i data-lucide="${r.icon}"></i></div><div class="rec-text"><h4>${r.title}</h4><p>${r.text}</p></div></div>`).join('');
lucide.createIcons();document.getElementById('resultCard').scrollIntoView({behavior:'smooth',block:'start'})}

// Chat
function initChat(){document.getElementById('chatSendBtn')?.addEventListener('click',sendChat);
document.getElementById('chatInput')?.addEventListener('keypress',e=>{if(e.key==='Enter')sendChat()});
document.querySelectorAll('.chat-sug').forEach(b=>b.addEventListener('click',()=>{document.getElementById('chatInput').value=b.dataset.msg;sendChat()}))}
async function sendChat(){const input=document.getElementById('chatInput');const msg=input.value.trim();if(!msg)return;input.value='';
const msgs=document.getElementById('chatMessages');
msgs.innerHTML+=`<div class="chat-msg user"><div class="chat-avatar">👤</div><div class="chat-bubble">${msg}</div></div>`;
msgs.innerHTML+=`<div class="chat-msg bot" id="typing"><div class="chat-avatar">🤖</div><div class="chat-bubble">Thinking...</div></div>`;
msgs.scrollTop=msgs.scrollHeight;
try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
const d=await r.json();document.getElementById('typing').remove();
msgs.innerHTML+=`<div class="chat-msg bot"><div class="chat-avatar">🤖</div><div class="chat-bubble">${d.response.replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')}</div></div>`;
msgs.scrollTop=msgs.scrollHeight}catch(e){document.getElementById('typing').remove();
msgs.innerHTML+=`<div class="chat-msg bot"><div class="chat-avatar">🤖</div><div class="chat-bubble">Sorry, I couldn't process that. Try again!</div></div>`}}

// Savings
function initSavings(){document.getElementById('calcSavingsBtn')?.addEventListener('click',calcSavings)}
function calcSavings(){const area=parseFloat(document.getElementById('savArea').value)||1;
const manual=parseFloat(document.getElementById('savManual').value)||5000;
const cost=parseFloat(document.getElementById('savCost').value)||50;
const smartUsage=Math.round(manual*0.55);const dailySaved=manual-smartUsage;
document.getElementById('savWeekly').textContent=(dailySaved*7).toLocaleString()+' litres';
document.getElementById('savMoney').textContent='₹ '+(dailySaved*30*cost/1000).toLocaleString();
document.getElementById('savYearly').textContent=(dailySaved*365).toLocaleString()+' litres';
document.getElementById('savSmart').textContent=smartUsage.toLocaleString()+' L/day';
if(savingsChart)savingsChart.destroy();
savingsChart=new Chart(document.getElementById('chartSavings'),{type:'bar',data:{labels:['Manual','Smart','Saved'],
datasets:[{data:[manual,smartUsage,dailySaved],backgroundColor:['#ef5350','#4caf50','#42a5f5'],borderRadius:8,barThickness:40}]},
options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{grid:{color:'rgba(255,255,255,.05)'}},x:{grid:{display:false}}}}})}

// Calendar
function initCalendar(){document.getElementById('calCropSelect')?.addEventListener('change',loadCalendar);loadCalendar()}
async function loadCalendar(){const crop=document.getElementById('calCropSelect').value;
try{const r=await fetch(`/api/crop-calendar?crop=${crop}`);const d=await r.json();if(d.success){
document.getElementById('calSeason').textContent='Season: '+d.season;
document.getElementById('calWater').textContent='Water: '+d.water_need_mm+'mm/season';
document.getElementById('calGrid').innerHTML=d.months.map(m=>`<div class="cal-card ${m.irrigation_level}"><h4>${m.name}</h4><p>${m.is_monsoon?'🌧️ Monsoon':m.is_growing?'🌱 Growing':'💤 Off'}</p><p>${m.tip}</p></div>`).join('')}}catch(e){console.error(e)}}

// Map
let leafletMap = null;
function initMap(){
    if(!document.getElementById('realMap')) return;
    if(leafletMap) return; // already initialized
    
    // Center on India
    leafletMap = L.map('realMap').setView([20.5937, 78.9629], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(leafletMap);
    
    // Add dark mode styling if enabled
    if(document.documentElement.dataset.theme === 'dark') {
        document.querySelector('.leaflet-layer').style.filter = 'invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)';
    }

    const cities = [
        {name:'Bengaluru', lat:12.97, lon:77.59, type:'moderate'}, {name:'Delhi', lat:28.61, lon:77.21, type:'hot'}, 
        {name:'Mumbai', lat:19.08, lon:72.88, type:'wet'}, {name:'Chennai', lat:13.08, lon:80.27, type:'hot'}, 
        {name:'Hyderabad', lat:17.39, lon:78.49, type:'hot'}, {name:'Kolkata', lat:22.57, lon:88.36, type:'wet'},
        {name:'Jaipur', lat:26.91, lon:75.79, type:'hot'}, {name:'Lucknow', lat:26.85, lon:80.95, type:'moderate'}, 
        {name:'Pune', lat:18.52, lon:73.86, type:'moderate'}, {name:'Ahmedabad', lat:23.02, lon:72.57, type:'hot'}, 
        {name:'Bhopal', lat:23.26, lon:77.41, type:'moderate'}, {name:'Patna', lat:25.61, lon:85.14, type:'wet'}
    ];
    
    // Custom icon color based on zone type
    const colors = {hot:'#ef5350', moderate:'#ffc107', wet:'#42a5f5'};
    
    cities.forEach(c => {
        const markerColor = colors[c.type];
        const customIcon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color:${markerColor};width:16px;height:16px;border-radius:50%;border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div>`,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });
        
        L.marker([c.lat, c.lon], {icon: customIcon})
         .addTo(leafletMap)
         .on('click', () => showCityInfo(c.name, c.type, c.lat, c.lon));
    });
}

function showCityInfo(name, type, lat, lon){
    const tips = {
        hot:'High evaporation zone. Irrigate early morning. Drip irrigation recommended.',
        moderate:'Balanced conditions. Follow ML predictions for optimal scheduling.',
        wet:'High moisture zone. Reduce irrigation during monsoon. Monitor drainage.'
    };
    
    document.getElementById('mapInfo').innerHTML = `
        <div style="padding:20px">
            <h3>📍 ${name}</h3>
            <p style="margin:12px 0;color:var(--text2)">Zone: <b style="color:var(--text);">${type.charAt(0).toUpperCase()+type.slice(1)}</b></p>
            <p style="color:var(--text3);font-size:0.9rem;line-height:1.5;">${tips[type]}</p>
            <div style="display:flex;gap:10px;margin-top:20px;">
                <button class="btn-primary" onclick="document.getElementById('citySelect').value='${name}';handleCityChange();"><i data-lucide="brain"></i> Predict</button>
            </div>
        </div>
    `;
    lucide.createIcons();
    leafletMap.flyTo([lat, lon], 7);
}

// Alerts
async function loadAlerts(){try{let lat=12.97,lon=77.59;if(navigator.geolocation)try{const p=await new Promise((res,rej)=>navigator.geolocation.getCurrentPosition(res,rej,{timeout:3000}));lat=p.coords.latitude;lon=p.coords.longitude}catch(e){}
const r=await fetch(`/api/alerts?lat=${lat}&lon=${lon}`);const d=await r.json();
if(d.success){document.getElementById('alertsList').innerHTML=d.alerts.map(a=>`<div class="alert-card"><div class="alert-ic ${a.type}"><i data-lucide="${a.icon}"></i></div><div class="alert-body"><h4>${a.title}</h4><p>${a.text}</p></div><span class="alert-time">${a.time}</span></div>`).join('');lucide.createIcons()}}catch(e){console.error(e)}}

// Cities
async function loadCities(){try{const r=await fetch('/api/cities');const d=await r.json();const sel=document.getElementById('citySelect');
d.cities.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;sel.appendChild(o)})}catch(e){}}

// Export
function exportPDF(){window.print()}
function exportCSV(){if(!forecastPredictions)return alert('Load weather first');
let csv='Date,Temperature,Humidity,Rainfall,Soil Moisture,Irrigation Needed,Confidence\n';
forecastPredictions.forEach(p=>{csv+=`${p.date},${p.temperature},${p.humidity},${p.rainfall},${p.soil_moisture},${p.irrigation_needed?'Yes':'No'},${p.confidence}%\n`});
const blob=new Blob([csv],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='aquasmart_forecast.csv';a.click()}
function shareWhatsApp(){const msg=forecastPredictions?`🌱 AquaSmart Irrigation Plan\n📅 ${forecastPredictions[0]?.date}\n${forecastPredictions.map(p=>`${p.date}: ${p.irrigation_needed?'💧 Irrigate':'✅ Skip'} (${p.confidence}%)`).join('\n')}`
:'🌱 AquaSmart - Smart Irrigation Forecast System\nCheck your irrigation needs at our dashboard!';
window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`)}

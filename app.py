"""AquaSmart - Flask Backend API with all endpoints"""
from flask import Flask, request, jsonify, send_from_directory
import pickle, numpy as np, pandas as pd, json, os
import urllib.request, urllib.parse
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static')

with open('models/irrigation_model.pkl','rb') as f: model = pickle.load(f)
with open('models/scaler.pkl','rb') as f: scaler = pickle.load(f)
with open('models/model_metadata.json','r') as f: model_metadata = json.load(f)
df = pd.read_csv('data/smart_irrigation.csv')

CITIES = {
    'Bengaluru': (12.97,77.59), 'Delhi': (28.61,77.21), 'Mumbai': (19.08,72.88),
    'Chennai': (13.08,80.27), 'Hyderabad': (17.39,78.49), 'Kolkata': (22.57,88.36),
    'Jaipur': (26.91,75.79), 'Lucknow': (26.85,80.95), 'Pune': (18.52,73.86),
    'Ahmedabad': (23.02,72.57), 'Bhopal': (23.26,77.41), 'Patna': (25.61,85.14)
}

CROPS = {
    'rice': {'water_need': 1200, 'season': 'kharif', 'months': [6,7,8,9,10]},
    'wheat': {'water_need': 450, 'season': 'rabi', 'months': [11,12,1,2,3]},
    'maize': {'water_need': 600, 'season': 'kharif', 'months': [6,7,8,9]},
    'cotton': {'water_need': 700, 'season': 'kharif', 'months': [4,5,6,7,8,9,10]},
    'sugarcane': {'water_need': 1800, 'season': 'annual', 'months': list(range(1,13))},
    'tomato': {'water_need': 500, 'season': 'rabi', 'months': [10,11,12,1,2,3]},
    'potato': {'water_need': 400, 'season': 'rabi', 'months': [10,11,12,1,2]},
    'chickpea': {'water_need': 300, 'season': 'rabi', 'months': [10,11,12,1,2,3]},
    'banana': {'water_need': 1500, 'season': 'annual', 'months': list(range(1,13))},
    'mango': {'water_need': 800, 'season': 'annual', 'months': list(range(1,13))},
    'grapes': {'water_need': 600, 'season': 'annual', 'months': list(range(1,13))},
    'groundnut': {'water_need': 500, 'season': 'kharif', 'months': [6,7,8,9,10]},
}

SOIL_MOISTURE_FACTOR = {'sandy': 0.7, 'loamy': 1.0, 'clay': 1.3, 'silt': 1.1, 'peat': 1.4}

@app.route('/')
def index(): return send_from_directory('static','index.html')
@app.route('/<path:path>')
def serve_static(path): return send_from_directory('static',path)

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        d = request.json
        temp=float(d['temperature']); hum=float(d['humidity']); rain=float(d['rainfall']); moist_in=float(d['soil_moisture'])
        
        # Auto-compute effective soil moisture: blend user input with rainfall/humidity effect
        rain_boost = min(30, rain / 10)       # 0-300mm rainfall → 0-30% boost
        hum_boost = max(0, (hum - 40)) * 0.2  # humidity above 40 adds moisture
        effective_moisture = min(90, max(10, moist_in + rain_boost + hum_boost))
        
        features = np.array([[float(d['N']),float(d['P']),float(d['K']),temp,hum,float(d['ph']),rain,effective_moisture]])
        fs = scaler.transform(features)
        pred = model.predict(fs)[0]
        prob = model.predict_proba(fs)[0]
        
        prob_irrigation = float(prob[1])
        prob_no_irrigation = float(prob[0])
        conf = float(max(prob))
        
        soil = d.get('soil_type','loamy')
        crop = d.get('crop','rice')
        # Pass effective_moisture into data dict for recommendations
        d['soil_moisture'] = effective_moisture
        recs = gen_recommendations(d, pred, prob, crop, soil)
        water_amt = calc_water(d, pred, crop, soil)
        reason = gen_reason(d, pred)
        return jsonify({'success':True,'irrigation_needed':int(pred),'confidence':round(conf*100,1),
            'probability_no_irrigation':round(prob_no_irrigation*100,1),'probability_irrigation':round(prob_irrigation*100,1),
            'recommendations':recs,'water_amount':water_amt,'reason':reason,'crop':crop,'soil_type':soil,
            'effective_moisture':round(effective_moisture,1)})
    except Exception as e: return jsonify({'success':False,'error':str(e)}),400

@app.route('/api/analytics')
def analytics():
    fc = ['N','P','K','temperature','humidity','ph','rainfall','soil_moisture']
    dist = {c:{'values':df[c].tolist(),'mean':round(float(df[c].mean()),2),'std':round(float(df[c].std()),2),'min':round(float(df[c].min()),2),'max':round(float(df[c].max()),2)} for c in fc}
    cs = df.groupby('crop').agg(total=('irrigation_needed','count'),needs_irrigation=('irrigation_needed','sum'),avg_moisture=('soil_moisture','mean'),avg_temp=('temperature','mean'),avg_humidity=('humidity','mean'),avg_rainfall=('rainfall','mean')).reset_index()
    cs['irrigation_rate'] = (cs['needs_irrigation']/cs['total']*100).round(1)
    corr = df[fc+['irrigation_needed']].corr()['irrigation_needed'].drop('irrigation_needed')
    return jsonify({'model_info':model_metadata,'distributions':dist,'crop_stats':cs.to_dict(orient='records'),
        'correlation_with_irrigation':{k:round(v,4) for k,v in corr.items()},'total_samples':len(df),'irrigation_rate':round(df['irrigation_needed'].mean()*100,1)})

@app.route('/api/weather')
def weather():
    try:
        lat=request.args.get('lat','20.5937'); lon=request.args.get('lon','78.9629')
        params=urllib.parse.urlencode({'latitude':lat,'longitude':lon,'current':'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure',
            'daily':'temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,relative_humidity_2m_max,relative_humidity_2m_min','timezone':'auto','past_days':3,'forecast_days':7})
        url=f'https://api.open-meteo.com/v1/forecast?{params}'
        req=urllib.request.Request(url,headers={'User-Agent':'AquaSmart/1.0'})
        with urllib.request.urlopen(req,timeout=10) as resp: data=json.loads(resp.read().decode())
        loc=get_location_name(lat,lon)
        cur=data.get('current',{})
        daily=data.get('daily',{})
        forecast=[]
        if daily.get('time') and len(daily['time']) >= 4:
            # sum rainfall for the 3 past days
            total_rain=sum(daily.get('rain_sum',[0,0,0])[:3])
            # indices 3 to end are the 7-day forecast (including today)
            for i in range(3, len(daily['time'])):
                forecast.append({'date':daily['time'][i],'temp_max':daily.get('temperature_2m_max',[None])[i],'temp_min':daily.get('temperature_2m_min',[None])[i],
                    'precipitation':daily.get('precipitation_sum',[0])[i],'rain':daily.get('rain_sum',[0])[i],'precipitation_probability':daily.get('precipitation_probability_max',[0])[i],
                    'weather_code':daily.get('weather_code',[0])[i],'wind_speed_max':daily.get('wind_speed_10m_max',[0])[i],
                    'humidity_max':daily.get('relative_humidity_2m_max',[None])[i],'humidity_min':daily.get('relative_humidity_2m_min',[None])[i]})
        else:
            total_rain=0
        return jsonify({'success':True,'location':loc,'latitude':float(lat),'longitude':float(lon),'timestamp':datetime.now().isoformat(),
            'current':{'temperature':cur.get('temperature_2m'),'humidity':cur.get('relative_humidity_2m'),'feels_like':cur.get('apparent_temperature'),
                'precipitation':cur.get('precipitation'),'rain':cur.get('rain'),'weather_code':cur.get('weather_code'),'wind_speed':cur.get('wind_speed_10m'),
                'wind_direction':cur.get('wind_direction_10m'),'pressure':cur.get('surface_pressure'),'weather_desc':get_weather_desc(cur.get('weather_code',0))},
            'forecast':forecast,'total_recent_rainfall':round(total_rain,1)})
    except Exception as e: return jsonify({'success':False,'error':str(e)}),400

@app.route('/api/weather-city')
def weather_city():
    city=request.args.get('city','Bengaluru')
    if city in CITIES:
        lat,lon=CITIES[city]
        return weather_fetch(lat,lon,city)
    return jsonify({'success':False,'error':'City not found'}),404

def weather_fetch(lat,lon,city_name=None):
    try:
        params=urllib.parse.urlencode({'latitude':lat,'longitude':lon,'current':'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,surface_pressure',
            'daily':'temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,relative_humidity_2m_max,relative_humidity_2m_min','timezone':'auto','past_days':3,'forecast_days':7})
        url=f'https://api.open-meteo.com/v1/forecast?{params}'
        req=urllib.request.Request(url,headers={'User-Agent':'AquaSmart/1.0'})
        with urllib.request.urlopen(req,timeout=10) as resp: data=json.loads(resp.read().decode())
        cur=data.get('current',{})
        daily=data.get('daily',{})
        forecast=[]
        if daily.get('time') and len(daily['time']) >= 4:
            total_rain=sum(daily.get('rain_sum',[0,0,0])[:3])
            for i in range(3, len(daily['time'])):
                forecast.append({'date':daily['time'][i],'temp_max':daily.get('temperature_2m_max',[None])[i],'temp_min':daily.get('temperature_2m_min',[None])[i],
                    'precipitation':daily.get('precipitation_sum',[0])[i],'rain':daily.get('rain_sum',[0])[i],'precipitation_probability':daily.get('precipitation_probability_max',[0])[i],
                    'weather_code':daily.get('weather_code',[0])[i],'wind_speed_max':daily.get('wind_speed_10m_max',[0])[i],
                    'humidity_max':daily.get('relative_humidity_2m_max',[None])[i],'humidity_min':daily.get('relative_humidity_2m_min',[None])[i]})
        else:
            total_rain=0
        loc=city_name or get_location_name(lat,lon)
        return jsonify({'success':True,'location':loc,'latitude':lat,'longitude':lon,'timestamp':datetime.now().isoformat(),
            'current':{'temperature':cur.get('temperature_2m'),'humidity':cur.get('relative_humidity_2m'),'feels_like':cur.get('apparent_temperature'),
                'precipitation':cur.get('precipitation'),'rain':cur.get('rain'),'weather_code':cur.get('weather_code'),'wind_speed':cur.get('wind_speed_10m'),
                'pressure':cur.get('surface_pressure'),'weather_desc':get_weather_desc(cur.get('weather_code',0))},
            'forecast':forecast,'total_recent_rainfall':round(total_rain,1)})
    except Exception as e: return jsonify({'success':False,'error':str(e)}),400

@app.route('/api/predict-forecast', methods=['POST'])
def predict_forecast():
    """Run ML prediction on each forecast day"""
    try:
        d=request.json; forecasts=d.get('forecast',[]); soil_type=d.get('soil_type','loamy'); crop=d.get('crop','rice')
        n=float(d.get('N',50)); p=float(d.get('P',50)); k=float(d.get('K',50)); ph=float(d.get('ph',6.5))
        results=[]
        for f in forecasts:
            temp=(f.get('temp_max',30)+f.get('temp_min',20))/2
            hum=(f.get('humidity_max',70)+(f.get('humidity_min',40) or 40))/2 if f.get('humidity_max') else 60
            rain=f.get('rain',0) or 0
            moist_factor=SOIL_MOISTURE_FACTOR.get(soil_type,1.0)
            est_moisture=min(90,max(10,hum*0.4+(rain/300*30)+15))*moist_factor
            est_moisture=min(90,max(10,est_moisture))
            features=np.array([[n,p,k,temp,hum,ph,rain,est_moisture]])
            fs=scaler.transform(features)
            pred=model.predict(fs)[0]; prob=model.predict_proba(fs)[0]
            results.append({'date':f.get('date'),'irrigation_needed':int(pred),'confidence':round(float(max(prob))*100,1),
                'temperature':round(temp,1),'humidity':round(hum,1),'rainfall':round(rain,1),'soil_moisture':round(est_moisture,1)})
        return jsonify({'success':True,'predictions':results})
    except Exception as e: return jsonify({'success':False,'error':str(e)}),400

@app.route('/api/alerts')
def alerts():
    try:
        lat=request.args.get('lat','20.5937'); lon=request.args.get('lon','78.9629')
        alerts_list=[]
        try:
            params=urllib.parse.urlencode({'latitude':lat,'longitude':lon,'current':'temperature_2m,relative_humidity_2m,precipitation','timezone':'auto'})
            url=f'https://api.open-meteo.com/v1/forecast?{params}'
            req=urllib.request.Request(url,headers={'User-Agent':'AquaSmart/1.0'})
            with urllib.request.urlopen(req,timeout=5) as resp: data=json.loads(resp.read().decode())
            cur=data.get('current',{})
            temp=cur.get('temperature_2m',30); hum=cur.get('relative_humidity_2m',50); precip=cur.get('precipitation',0)
            if temp and temp>38: alerts_list.append({'type':'critical','title':'Extreme Heat Alert','text':f'Temperature is {temp}°C. Irrigate before 8AM to prevent crop stress.','icon':'thermometer','time':'Now'})
            if hum and hum<25: alerts_list.append({'type':'warning','title':'Very Low Humidity','text':f'Humidity at {hum}%. Increase irrigation frequency.','icon':'droplets','time':'Now'})
            if precip and precip>5: alerts_list.append({'type':'success','title':'Rainfall Detected','text':f'Precipitation of {precip}mm detected. Irrigation may be skipped.','icon':'cloud-rain','time':'Now'})
            if temp and temp>30 and hum and hum<40: alerts_list.append({'type':'warning','title':'High Evaporation Risk','text':'Hot and dry conditions. Water early morning or late evening.','icon':'sun','time':'Today'})
            now=datetime.now()
            if 6<=now.month<=9: alerts_list.append({'type':'info','title':'Monsoon Season Active','text':'Reduce irrigation during monsoon. Monitor soil moisture closely.','icon':'cloud-rain','time':'Seasonal'})
        except: pass
        alerts_list.append({'type':'info','title':'Weekly Summary','text':'Track your water usage in the Water Savings tab.','icon':'bar-chart-3','time':'Weekly'})
        return jsonify({'success':True,'alerts':alerts_list})
    except Exception as e: return jsonify({'success':False,'error':str(e)}),400

@app.route('/api/chat', methods=['POST'])
def chat():
    msg=request.json.get('message','').lower().strip()
    resp=get_chat_response(msg)
    return jsonify({'success':True,'response':resp})

@app.route('/api/crop-calendar')
def crop_calendar():
    crop=request.args.get('crop','rice')
    info=CROPS.get(crop,CROPS['rice'])
    months_data=[]
    monsoon=[6,7,8,9]
    for m in range(1,13):
        is_growing=m in info['months']
        is_monsoon=m in monsoon
        if not is_growing: level='none'
        elif is_monsoon: level='low'
        elif m in [4,5,10]: level='medium'
        else: level='high' if is_growing else 'none'
        months_data.append({'month':m,'name':['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1],
            'is_growing':is_growing,'is_monsoon':is_monsoon,'irrigation_level':level,
            'tip':'Monsoon - reduce irrigation' if is_monsoon and is_growing else 'Active growing - regular irrigation' if is_growing else 'Off season'})
    return jsonify({'success':True,'crop':crop,'season':info['season'],'water_need_mm':info['water_need'],'months':months_data})

@app.route('/api/cities')
def cities(): return jsonify({'cities':list(CITIES.keys())})

@app.route('/api/model-info')
def model_info(): return jsonify(model_metadata)

# ---- Helper Functions ----
def get_location_name(lat,lon):
    try:
        url=f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10'
        req=urllib.request.Request(url,headers={'User-Agent':'AquaSmart/1.0'})
        with urllib.request.urlopen(req,timeout=5) as resp: data=json.loads(resp.read().decode())
        addr=data.get('address',{}); city=addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county',''); state=addr.get('state','')
        return f"{city}, {state}" if city else f"Lat {lat}, Lon {lon}"
    except: return f"Lat {lat}, Lon {lon}"

def get_weather_desc(code):
    return {0:'Clear Sky',1:'Mainly Clear',2:'Partly Cloudy',3:'Overcast',45:'Foggy',48:'Rime Fog',51:'Light Drizzle',53:'Moderate Drizzle',55:'Dense Drizzle',61:'Slight Rain',63:'Moderate Rain',65:'Heavy Rain',71:'Slight Snow',73:'Moderate Snow',75:'Heavy Snow',80:'Slight Showers',81:'Moderate Showers',82:'Violent Showers',95:'Thunderstorm',96:'Thunderstorm + Hail',99:'Severe Storm'}.get(code,'Unknown')

def gen_reason(d,pred):
    parts=[]
    t=float(d.get('temperature',30)); h=float(d.get('humidity',50)); r=float(d.get('rainfall',50)); m=float(d.get('soil_moisture',50))
    if pred==1:
        if m<30: parts.append('low soil moisture')
        if t>35: parts.append('high temperature')
        if h<30: parts.append('low humidity')
        if r<30: parts.append('insufficient rainfall')
        return ('Due to '+' + '.join(parts)+' = irrigate now') if parts else 'Conditions suggest irrigation is needed'
    else:
        if m>60: parts.append('adequate soil moisture')
        if r>100: parts.append('sufficient rainfall')
        if h>70: parts.append('high humidity')
        return ('Due to '+' + '.join(parts)+' = skip irrigation') if parts else 'Conditions are favorable, no irrigation needed'

def calc_water(d,pred,crop,soil):
    if pred==0: return {'amount':0,'unit':'litres/hectare','message':'No irrigation needed today'}
    base=CROPS.get(crop,{'water_need':600})['water_need']/120
    t=float(d.get('temperature',30)); h=float(d.get('humidity',50)); m=float(d.get('soil_moisture',50))
    factor=1.0
    if t>35: factor+=0.3
    elif t>30: factor+=0.15
    if h<30: factor+=0.2
    if m<25: factor+=0.3
    elif m<40: factor+=0.15
    sf=SOIL_MOISTURE_FACTOR.get(soil,1.0)
    amount=round(base*factor/sf)
    return {'amount':amount,'unit':'litres/hectare','message':f'Apply approximately {amount} litres per hectare today'}

def gen_recommendations(d,pred,prob,crop,soil):
    recs=[]; m=float(d.get('soil_moisture',50)); t=float(d.get('temperature',30)); h=float(d.get('humidity',50)); r=float(d.get('rainfall',50)); ph=float(d.get('ph',7))
    if pred==1:
        if m<25: recs.append({'type':'critical','icon':'droplet','title':'Critical: Very Low Soil Moisture','text':f'Soil moisture at {m}% - immediate deep irrigation needed.'})
        elif m<40: recs.append({'type':'warning','icon':'droplet','title':'Low Soil Moisture','text':f'Soil moisture at {m}%. Schedule irrigation within 4-6 hours.'})
        if t>35: recs.append({'type':'warning','icon':'thermometer','title':'High Temperature','text':f'At {t}°C, use drip irrigation early morning or evening.'})
        if h<30: recs.append({'type':'info','icon':'wind','title':'Low Humidity','text':f'Humidity at {h}%. Consider mulching to retain moisture.'})
        if r<50: recs.append({'type':'info','icon':'cloud-rain','title':'Low Rainfall','text':f'Only {r}mm rainfall. Supplement with irrigation.'})
    else:
        if m>70: recs.append({'type':'success','icon':'check-circle','title':'Optimal Moisture','text':f'Soil moisture at {m}% is excellent.'})
        if r>150: recs.append({'type':'success','icon':'cloud-rain','title':'Sufficient Rainfall','text':f'{r}mm rainfall provides adequate water.'})
        recs.append({'type':'success','icon':'leaf','title':'Water Conservation','text':'Skip this irrigation cycle and save water.'})
    if ph<5.5: recs.append({'type':'info','icon':'flask-conical','title':'Acidic Soil','text':f'pH {ph} - consider adding lime.'})
    elif ph>8: recs.append({'type':'info','icon':'flask-conical','title':'Alkaline Soil','text':f'pH {ph} - consider adding sulfur.'})
    return recs

def get_chat_response(msg):
    # 1. Match specific crop inquiries first
    crop_keys = list(CROPS.keys())
    if any(w in msg for w in crop_keys + ['crop', 'plant']): 
        crop = next((c for c in crop_keys if c in msg), 'rice')
        info = CROPS.get(crop, CROPS['rice'])
        return f"**{crop.title()}** needs ~{info['water_need']}mm water per season. Best grown in {info['season']} season (months: {', '.join(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1] for m in info['months'])}). Check the Crop Calendar for detailed monthly irrigation guidance!"
    
    # 2. Match seasonal/weather conditions
    if any(w in msg for w in ['monsoon','season','month']): return "During monsoon (June-September), reduce irrigation significantly. The Crop Calendar automatically accounts for monsoon. Check it for season-specific recommendations!"
    if any(w in msg for w in ['weather','rain','temperature','hot','cold']): return "I can see the live weather data! Head to the Weather tab for real-time conditions. The 7-Day Forecast shows irrigation predictions for each day. Pro tip: irrigate early morning when it's hot to reduce evaporation."
    
    # 3. Match soil and savings inquiries
    if any(w in msg for w in ['soil','moisture','ph','sandy','clay','loam']): return "Soil type affects water retention: Sandy soil drains fast (needs more water), Clay retains water well (needs less), Loamy is ideal. Select your soil type in the Predict tab for accurate recommendations!"
    if any(w in msg for w in ['save','saving','money','cost']): return "Smart irrigation can save 30-50% water! Check the Water Savings calculator to see your exact savings in litres and ₹. On average, farmers save ₹15,000-25,000 per hectare per year with smart irrigation."
    
    # 4. Fallback for generic water/irrigation queries
    if any(w in msg for w in ['water','irrigat','should i']): return "Based on current conditions, I recommend checking the Prediction tab with your local weather data. Click 'Auto-fill from Weather' for instant analysis! Generally: if soil moisture < 40% and no rain expected, irrigate early morning."
    
    # 5. Greeting / Default fallback
    if any(w in msg for w in ['hello','hi','hey','help']): return "Hello! I'm AquaSmart AI Assistant. I can help with:\n• Irrigation advice for your crops\n• Weather-based recommendations\n• Soil & water management tips\n• Crop calendar guidance\n\nTry asking: 'Should I water my tomatoes today?' or 'How much water does rice need?'"
    return "Great question! For the best answer, I recommend:\n1. Check the **Predict** tab with your current data\n2. Review the **7-Day Forecast** for upcoming irrigation needs\n3. Use the **Crop Calendar** for seasonal guidance\n\nAsk me about any specific crop, weather concern, or irrigation question!"

if __name__=='__main__':
    print("="*50); print("  AquaSmart - Smart Irrigation System"); print("="*50)
    print(f"  Model: {model_metadata['model_name']} | Accuracy: {model_metadata['accuracy']}%")
    print(f"  Dataset: {len(df)} samples | Cities: {len(CITIES)}")
    print("="*50); print("  Open: http://localhost:5000"); print("="*50)
    app.run(debug=True,port=5000)

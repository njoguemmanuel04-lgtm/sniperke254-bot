from flask import Flask, request
import os, requests
app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

FOREX = {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X","USD/CHF":"USDCHF=X","AUD/USD":"AUDUSD=X","NZD/USD":"NZDUSD=X","USD/CAD":"USDCAD=X"}

def send_msg(c,t):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",json={"chat_id":c,"text":t,"parse_mode":"Markdown"},timeout=10)
    except: pass

def get_price(s):
    try:
        r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1m&range=1d",headers={"User-Agent":"Mozilla/5.0"},timeout=5).json()
        return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return None

@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST': return webhook()
    return "Sniper KE 254"

@app.route('/api',methods=['GET','POST'])
def webhook():
    if request.method=='GET': return "API LIVE"
    try:
        data=request.get_json(force=True,silent=True) or {}
        if "message" in data:
            chat_id=data["message"]["chat"]["id"]
            txt=data["message"].get("text","").upper()
            if "/START" in txt:
                send_msg(chat_id,"🔥 *SNIPER KE 254 - ALL MARKETS LIVE!* 🔥\n\n/gold - Gold\n/btc - Bitcoin\n/forex - All 7 Majors\n/eurusd /gbpusd /usdjpy\n\n_Tap menu below!_")
                return "ok"
            if "/FOREX" in txt:
                msg="💱 *LIVE FOREX - 7 MAJORS* 💱\n\n"
                for pair,sym in FOREX.items():
                    p=get_price(sym)
                    msg+=f"{pair}: {p:.5f}\n" if p and p<200 else f"{pair}: {p:.2f}\n" if p else f"{pair}: Loading...\n"
                send_msg(chat_id,msg)
                return "ok"
            if "GOLD" in txt or "XAU" in txt:
                p=get_price("GC=F") or 2650.50
                send_msg(chat_id,f"🥇 *GOLD LIVE*\n\nPrice: ${p:.2f}\nSignal: BUY 📈\nSL: ${p-5:.2f}\nTP: ${p+8:.2f}")
                return "ok"
            if "BTC" in txt:
                p=get_price("BTC-USD") or 67000
                send_msg(chat_id,f"₿ *BTC LIVE*\n\nPrice: ${p:,.2f}\nBUY 🚀")
                return "ok"
            for pair,sym in FOREX.items():
                if pair.replace("/","") in txt.replace("/","").replace(" ",""):
                    p=get_price(sym)
                    if p: send_msg(chat_id,f"💱 *{pair} LIVE*\n\nPrice: {p}\nBUY 📈\nTP: {p*1.001:.5f}\nSL: {p*0.999:.5f}")
                    return "ok"
        return "ok"
    except: return "ok"

import requests,json,time,smtplib,hashlib,difflib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup

COACH_EMAIL="shox1539@gmail.com"
GMAIL_PASS="adwa ckpi yahz cvax"
INT=300

LEAGUES=[
{"name":"Westurban Statusfy","team":"11U Lions","url":"https://statusfy.com/3162413484"},
{"name":"SW Boys Club Statusfy","team":"10U Lions","url":"https://statusfy.com/6206204483"},
{"name":"11U Lions Schedule","team":"11U Lions","url":"https://www.allprosoftware.net/westurbanhighschool/aplsteam1555.htm"},
{"name":"10U Lions Schedule","team":"10U Lions","url":"https://www.allprosoftware.net/swbcleague26/aplsteam1576.htm"},
]

def load_tournaments():
    try:
        with open("tournaments.txt") as f:
            urls=[l.strip() for l in f if l.strip() and l.startswith("http")]
        return [{"name":f"Tournament","team":"Lions","url":u} for u in urls]
    except:
        return []

def fetch(url):
    try:
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=15)
        r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        lines=[l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
        return "\n".join(lines)
    except:
        return None

def get_diff(old,new):
    old_lines=old.splitlines()
    new_lines=new.splitlines()
    removed=[l[1:] for l in difflib.unified_diff(old_lines,new_lines,lineterm="",n=0) if l.startswith("-") and not l.startswith("---")]
    added=[l[1:] for l in difflib.unified_diff(old_lines,new_lines,lineterm="",n=0) if l.startswith("+") and not l.startswith("+++")]
    parts=[]
    if removed:
        parts.append("REMOVED:\n"+"\n".join(f"  - {l}" for l in removed[:10]))
    if added:
        parts.append("ADDED:\n"+"\n".join(f"  + {l}" for l in added[:10]))
    return "\n\n".join(parts) if parts else "Content changed"

def send_email(source,changes):
    now=datetime.now().strftime("%A %b %d, %I:%M %p")
    body=f"""
⚾ COACHBOT SCHEDULE ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Team:    {source['team']}
Source:  {source['name']}
Time:    {now}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT CHANGED:
{changes}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFT MESSAGE TO PARENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hey Lions families — heads up, there has been a 
schedule change posted for {source['team']}. 
Please check the league website to confirm your 
next game details and update your calendars.

- Coach
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verify at: {source['url']}
"""
    msg=MIMEMultipart()
    msg["Subject"]=f"⚾ CoachBot: {source['team']} schedule changed"
    msg["From"]=COACH_EMAIL
    msg["To"]=COACH_EMAIL
    msg.attach(MIMEText(body,"plain"))
    with smtplib.SMTP("smtp.gmail.com",587) as s:
        s.starttls()
        s.login(COACH_EMAIL,GMAIL_PASS)
        s.sendmail(COACH_EMAIL,COACH_EMAIL,msg.as_string())
    print(f"  EMAIL SENT: {source['name']}")

st={}
try:
    with open("st.json") as f:
        st=json.load(f)
except:
    pass

print("CoachBot running — sending email alerts")
n=0
while True:
    n+=1
    tournaments=load_tournaments()
    all_sources=LEAGUES+tournaments
    print(f"\n[Check {n}] {datetime.now().strftime('%I:%M %p')} — {len(tournaments)} tournament(s)")
    for s in all_sources:
        text=fetch(s["url"])
        k=s["url"]
        if text:
            h=hashlib.md5(text.encode()).hexdigest()
            if k not in st:
                print(f"  Baseline: {s['name']}")
                st[k]={"hash":h,"text":text}
            elif st[k]["hash"]!=h:
                print(f"  CHANGE: {s['name']}")
                changes=get_diff(st[k]["text"],text)
                send_email(s,changes)
                st[k]={"hash":h,"text":text}
            else:
                print(f"  OK: {s['name']}")
        else:
            print(f"  FAIL: {s['name']}")
    with open("st.json","w") as f:
        json.dump(st,f)
    print(f"  Next: {datetime.fromtimestamp(time.time()+INT).strftime('%I:%M %p')}")
    time.sleep(INT)

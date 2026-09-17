"""Google identity, private sessions, per-user drafts and audit history."""
import hashlib, json, secrets, sqlite3, time, sys, re, threading
from pathlib import Path
from http.cookies import SimpleCookie

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'vendor'))
CONFIG = ROOT / 'local-data' / 'access-config.json'
DB = ROOT / 'local-data' / 'access.sqlite3'
CONFIG_LOCK = threading.Lock()

def config():
    if not CONFIG.exists():
        return None
    c = json.loads(CONFIG.read_text('utf-8'))
    if not c.get('clientId') or not c.get('admins') or not c.get('origin'):
        raise ValueError('การตั้งค่าบัญชี Google ยังไม่ครบ')
    return c

def connect():
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY,email TEXT NOT NULL,name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY,user_id TEXT,expires REAL);
    CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY,at REAL,user_id TEXT,name TEXT,action TEXT);
    CREATE INDEX IF NOT EXISTS logs_user ON logs(user_id,id);
    ''')
    return db

def allowed(c, email):
    email = email.lower()
    return email in [x.lower() for x in c['admins'] + c.get('users', [])]

def role(c, email):
    return 'admin' if email.lower() in [x.lower() for x in c['admins']] else 'user'

def log(user, action):
    if not user or user['id'] == 'local':
        return
    with connect() as db:
        db.execute('INSERT INTO logs(at,user_id,name,action) VALUES(?,?,?,?)',
                   (time.time(), user['id'], user['name'], action))

def login(credential):
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request
    c = config()
    if not c:
        raise ValueError('ยังไม่ได้เชื่อมบัญชี Google ของระบบ')
    try:
        claims = id_token.verify_oauth2_token(credential, Request(), c['clientId'])
    except Exception:
        raise ValueError('ตรวจสอบบัญชี Google ไม่สำเร็จ กรุณาเข้าสู่ระบบใหม่')
    email = claims.get('email', '').lower()
    if claims.get('email_verified') is not True or not email.endswith('@gmail.com') or not allowed(c, email):
        raise ValueError('บัญชีนี้ยังไม่ได้รับสิทธิ์ใช้งาน กรุณาติดต่อ admin')
    uid = claims['sub']
    token = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute('INSERT OR IGNORE INTO users VALUES(?,?,?)', (uid, email, ''))
        db.execute('UPDATE users SET email=? WHERE id=?', (email, uid))
        db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
        db.execute('INSERT INTO sessions VALUES(?,?,?)', (digest(token), uid, time.time()+43200))
        user = dict(db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone())
    user['role'] = role(c, email)
    log(user, 'เข้าสู่ระบบด้วย Google')
    return token, user

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def cookie_token(headers):
    cookie = SimpleCookie()
    try:
        cookie.load(headers.get('Cookie', ''))
        return cookie['psdp_session'].value if 'psdp_session' in cookie else ''
    except Exception:
        return ''

def current(headers):
    c = config()
    token = cookie_token(headers)
    if not c or not token:
        return None
    with connect() as db:
        row = db.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?', (digest(token), time.time())).fetchone()
    if not row or not allowed(c, row['email']):
        return None
    user = dict(row)
    user['role'] = role(c, user['email'])
    return user

def logout(headers, user):
    with connect() as db:
        db.execute('DELETE FROM sessions WHERE token=?', (digest(cookie_token(headers)),))
    log(user, 'ออกจากระบบ')

def rename(user, name):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80 or any(ord(ch)<32 for ch in name):
        raise ValueError('กรุณาตั้งชื่อ 1–80 ตัวอักษร')
    with connect() as db:
        db.execute('UPDATE users SET name=? WHERE id=?', (name.strip(), user['id']))
    log(user, 'เปลี่ยนชื่อเป็น '+name.strip())

def history(user, before=0):
    query = "SELECT logs.id,at,user_id,COALESCE(NULLIF(logs.name,''),users.name) AS name,action FROM logs JOIN users ON users.id=logs.user_id WHERE logs.id<?"
    values = [before or 9223372036854775807]
    if user['role'] != 'admin':
        query += ' AND user_id=?'
        values.append(user['id'])
    with connect() as db:
        return [dict(r) for r in db.execute(query+' ORDER BY logs.id DESC LIMIT 100', values)]

def update_users(user, emails):
    if user['role'] != 'admin':
        raise ValueError('เฉพาะ admin เท่านั้น')
    if not isinstance(emails,list) or len(emails)>19:
        raise ValueError('เพิ่มผู้ใช้ได้สูงสุด 19 คน')
    if any(not isinstance(e,str) or not re.fullmatch(r'[a-zA-Z0-9._%+\-]+@gmail\.com',e.strip(),re.I) for e in emails):
        raise ValueError('กรุณาระบุ Gmail ให้ถูกต้อง')
    with CONFIG_LOCK:
        c=config()
        c['users']=sorted(set(e.strip().lower() for e in emails))
        pending=CONFIG.with_suffix('.tmp')
        pending.write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
        pending.replace(CONFIG)
    log(user,'อัปเดตรายชื่อบัญชีที่ได้รับสิทธิ์ใช้งาน')

def draft(user):
    if user['id'] == 'local':
        return ROOT / 'local-data' / 'current-draft.json'
    return ROOT / 'local-data' / ('draft-'+digest(user['id'])+'.json')

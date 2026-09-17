from pathlib import Path
import subprocess,sys,time,urllib.request,webbrowser
url='http://127.0.0.1:8765/'
def ready():
 try:
  with urllib.request.urlopen(url,timeout=2) as r:return b'PEA Smart Document' in r.read()
 except OSError:return False
if not ready():
 subprocess.Popen([sys.executable,str(Path(__file__).with_name('server.py'))],cwd=Path(__file__).parent,creationflags=subprocess.CREATE_NO_WINDOW)
 for attempt in range(20):
  time.sleep(.5)
  if ready():break
if ready():webbrowser.open(url)
else:input('Cannot open PEA Smart Document. Please check port 8765. Press Enter to close.')

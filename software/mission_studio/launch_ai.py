"""Choose an already installed local Ollama model; never downloads weights."""
import json,subprocess,sys
from pathlib import Path
from urllib.request import urlopen
def main():
 try:
  with urlopen('http://127.0.0.1:11434/api/tags',timeout=3) as response:raw=response.read(65537)
  if len(raw)>65536:raise ValueError('Installed-model list is too large')
  data=json.loads(raw);models=[m['name'] for m in data.get('models',[]) if isinstance(m,dict) and isinstance(m.get('name'),str)]
  if not models:raise ValueError('No installed local models were returned')
 except Exception as e:
  print('Local AI is not ready:',e);print('Start Ollama with an installed model, or open the HTML for the complete offline simulation.');input('Press Enter to close.');return
 print('Already installed models (no download will be performed):')
 for i,model in enumerate(models,1):print(f'{i}. {model}')
 try:index=int(input('Choose a model number, or 0 to cancel: '))-1
 except ValueError:return
 if not 0<=index<len(models):return
 subprocess.run([sys.executable,str(Path(__file__).with_name('server.py')),'--model',models[index]],check=False)
if __name__=='__main__':main()

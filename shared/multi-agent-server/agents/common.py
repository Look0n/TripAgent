import os
from pathlib import Path
from openai import OpenAI
ROOT = Path(__file__).resolve().parents[1]
def prompt(name):
    return (ROOT / 'prompts' / f'{name}_prompt.txt').read_text(encoding='utf-8')
def ask(name, content, tokens=350):
    client = OpenAI(base_url=os.getenv('OLLAMA_BASE_URL','http://localhost:11434/v1'), api_key='ollama', timeout=float(os.getenv('OLLAMA_TIMEOUT_SECONDS','60')), max_retries=0)
    response = client.chat.completions.create(model=os.getenv('OLLAMA_REVIEW_MODEL','llama3.1:8b') if name=='reviewer' else os.getenv('OLLAMA_MODEL','qwen2.5:0.5b'), messages=[{'role':'system','content':prompt(name)},{'role':'user','content':content}], temperature=0.1, max_tokens=tokens)
    return (response.choices[0].message.content or '').strip()

import subprocess, time, requests, sys

proc = subprocess.Popen([sys.executable, 'app.py'],
    cwd=r'C:\Users\LENOVO\OneDrive\Desktop\IDs for IOT\plagiarsm checker',
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

text = ("The rapid advancement of artificial intelligence has transformed "
        "numerous industries from healthcare to finance. Machine learning "
        "algorithms now power everything from recommendation systems to "
        "autonomous vehicles. However, this technological revolution also "
        "raises important ethical questions about privacy, job displacement, "
        "and the nature of human creativity. It is crucial that we develop "
        "robust frameworks to ensure AI benefits all of humanity while "
        "minimizing potential risks. Many experts believe that finding the "
        "right balance between innovation and regulation will be one of the "
        "most significant challenges of our time.")

r = requests.post('http://localhost:5000/api/ai-detect', json={'text': text}, timeout=10)
j = r.json()
print(f'BEFORE Score: {j["score"]}  Label: {j["label"]}')
print(f'  AI Phrases: {j["details"]["ai_phrase_score"]}  Burstiness: {j["details"]["burstiness_score"]}  Repetition: {j["details"]["repetition_score"]}  Perplexity: {j["details"]["perplexity_score"]}')

best_after = 100
best_text = ''
best_changes = 0

for attempt in range(5):
    r2 = requests.post('http://localhost:5000/api/bypass', json={'text': text}, timeout=10)
    j2 = r2.json()
    r3 = requests.post('http://localhost:5000/api/ai-detect', json={'text': j2['bypassed']}, timeout=10)
    j3 = r3.json()
    print(f'  Attempt {attempt+1}: {j3["score"]} ({j["score"] - j3["score"]:+.1f})')
    if j3['score'] < best_after:
        best_after = j3['score']
        best_text = j2['bypassed']
        best_changes = j2['changes']

print(f'\nBEST AFTER Score: {best_after}  (Reduction: {j["score"] - best_after:.1f})')
print(f'Changes: {best_changes}')
print(f'\n=== OUTPUT ===')
print(best_text)
if best_after < j['score']:
    print(f'\nIMPROVEMENT: {j["score"] - best_after:.1f} point drop')
else:
    print('\nNO IMPROVEMENT')

proc.terminate()

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

best_score = 100
best_text = ''
best_changes = 0
results = []

for attempt in range(10):
    r2 = requests.post('http://localhost:5000/api/bypass', json={'text': text}, timeout=10)
    j2 = r2.json()
    r3 = requests.post('http://localhost:5000/api/ai-detect', json={'text': j2['bypassed']}, timeout=10)
    j3 = r3.json()
    score = j3['score']
    reduction = j['score'] - score
    results.append(score)
    print(f'  Attempt {attempt+1:2d}: {score:5.1f} ({reduction:+5.1f})  changes={j2["changes"]:2d}')
    if score < best_score:
        best_score = score
        best_text = j2['bypassed']
        best_changes = j2['changes']

avg_score = sum(results) / len(results)
print(f'\n=== SUMMARY ===')
print(f'Before:    {j["score"]:.1f}')
print(f'Best:      {best_score:.1f} (reduction: {j["score"] - best_score:.1f})')
print(f'Average:   {avg_score:.1f}')
print(f'Worst:     {max(results):.1f}')
print(f'Improvements: {sum(1 for s in results if s < j["score"])}/10')
print(f'Best changes: {best_changes}')

if best_score < j['score']:
    print(f'\n=== BEST BYPASSED TEXT ({best_score}%) ===')
    print(best_text)

proc.terminate()

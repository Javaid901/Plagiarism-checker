import re
import json
import requests

class GrammarChecker:
    def __init__(self):
        self.api_url = "https://api.languagetool.org/v2/check"

    def check(self, text):
        if not text or len(text.strip()) < 3:
            return {
                "status": "error",
                "message": "Text too short for grammar check",
                "errors": [],
                "score": 100,
                "corrected_text": text
            }

        api_errors = self._check_with_api(text)
        rule_errors = self._check_with_rules(text)

        all_errors = api_errors + rule_errors
        all_errors = self._deduplicate_errors(all_errors)
        all_errors.sort(key=lambda e: e.get("offset", 0))

        corrected = self._apply_corrections(text, all_errors)

        total_words = len(text.split())
        error_count = len(all_errors)
        score = max(0, 100 - (error_count / max(total_words, 1) * 50))
        score = round(score, 1)

        return {
            "original": text,
            "status": "success",
            "errors": all_errors,
            "score": score,
            "error_count": error_count,
            "word_count": total_words,
            "corrected_text": corrected,
            "summary": self._generate_summary(all_errors, score, total_words)
        }

    def _check_with_api(self, text):
        try:
            data = {
                "text": text,
                "language": "en-US",
                "enabledOnly": "false"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlagiarismChecker/1.0",
                "Accept": "application/json"
            }
            resp = requests.post(self.api_url, data=data, headers=headers, timeout=10)

            if resp.status_code == 200:
                result = resp.json()
                return self._parse_api_response(result)
        except Exception:
            pass

        return []

    def _parse_api_response(self, response):
        errors = []
        for match in response.get("matches", []):
            error = {
                "offset": match.get("offset", 0),
                "length": match.get("length", 0),
                "message": match.get("message", ""),
                "replacements": [r.get("value", "") for r in match.get("replacements", [])[:3]],
                "type": match.get("rule", {}).get("issueType", "unknown"),
                "category": match.get("rule", {}).get("category", {}).get("name", "Unknown"),
                "rule_id": match.get("rule", {}).get("id", ""),
                "context": match.get("context", {}).get("text", ""),
                "source": "languagetool"
            }
            errors.append(error)
        return errors

    def _check_with_rules(self, text):
        errors = []
        words = text.split()
        sentences = re.split(r'(?<=[.!?])\s+', text)

        your_your_match = re.findall(r'\byour\s+(?=going|coming|doing|making|taking|giving|saying|telling|asking|writing|reading|playing|working|studying|eating|drinking|sleeping|walking|running|swimming|flying|driving|using|trying|getting|setting|putting|keeping|finding|holding|carrying|bringing|buying|selling|paying|spending|saving|watching|listening|thinking|feeling|knowing|understanding|believing|hoping|wishing|liking|loving|hating|needing|wanting|having|being)\b', text, re.IGNORECASE)
        if your_your_match:
            for m in re.finditer(r'\byour\s+(?=going|coming|doing|making|taking|giving|saying|telling|asking|writing|reading|playing|working|studying|eating|drinking|sleeping|walking|running|swimming|flying|driving|using|trying|getting|setting|putting|keeping|finding|holding|carrying|bringing|buying|selling|paying|spending|saving|watching|listening|thinking|feeling|knowing|understanding|believing|hoping|wishing|liking|loving|hating|needing|wanting|having|being)\b', text, re.IGNORECASE):
                errors.append({
                    "offset": m.start(),
                    "length": 4,
                    "message": "Possible misuse: 'your' instead of 'you're' (you are) before a verb",
                    "replacements": ["you're"],
                    "type": "misspelling",
                    "category": "Possible Typo",
                    "rule_id": "YOUR_YOURE",
                    "source": "local_rules"
                })

        its_it_match = re.findall(r'\bits\s+(?=a|an|the|going|coming|doing|making|taking|good|bad|big|small|new|old|very|really|quite|rather|pretty|too|so|more|most|less|least|not|also|just|only|even|still|already|yet|now|then|here|there)\b', text, re.IGNORECASE)
        if its_it_match:
            pass

        if re.search(r'\btheir\s+(?=going|coming|doing|making|taking|saying|telling|asking|writing|reading|playing|working|studying|eating|drinking|sleeping|walking|running|swimming|flying|driving|using|trying|getting|setting)\b', text, re.IGNORECASE):
            for m in re.finditer(r'\btheir\s+(?=going|coming|doing|making|taking|saying|telling|asking|writing|reading|playing|working|studying|eating|drinking|sleeping|walking|running|swimming|flying|driving|using|trying|getting|setting)\b', text, re.IGNORECASE):
                errors.append({
                    "offset": m.start(),
                    "length": 5,
                    "message": "Possible misuse: 'their' instead of 'they're' (they are) before a verb",
                    "replacements": ["they're"],
                    "type": "misspelling",
                    "category": "Possible Typo",
                    "rule_id": "THEIR_THEYRE",
                    "source": "local_rules"
                })

        for i, sentence in enumerate(sentences):
            words_in_sent = sentence.split()
            if len(words_in_sent) < 2:
                continue
            first_word = words_in_sent[0].lower()
            if first_word == "me":
                offset = sum(len(s) + 1 for s in sentences[:i]) if i > 0 else 0
                errors.append({
                    "offset": offset,
                    "length": 2,
                    "message": "Sentence should not start with 'Me'. Use 'I' instead.",
                    "replacements": ["I"],
                    "type": "style",
                    "category": "Style",
                    "rule_id": "ME_START",
                    "source": "local_rules"
                })

        return errors

    def _deduplicate_errors(self, errors):
        seen = set()
        unique = []
        for err in errors:
            key = (err.get("offset", 0), err.get("length", 0), err.get("message", ""))
            if key not in seen:
                seen.add(key)
                unique.append(err)
        return unique

    def _apply_corrections(self, text, errors):
        if not errors:
            return text

        seen_ranges = set()
        corrections = []
        for err in errors:
            replacements = err.get("replacements", [])
            if replacements:
                key = (err["offset"], err["length"])
                if key not in seen_ranges:
                    seen_ranges.add(key)
                    corrections.append({
                        "start": err["offset"],
                        "end": err["offset"] + err["length"],
                        "replacement": replacements[0]
                    })

        corrections.sort(key=lambda c: c["start"], reverse=True)

        result = text
        for c in corrections:
            result = result[:c["start"]] + c["replacement"] + result[c["end"]:]

        return result

    def _generate_summary(self, errors, score, word_count):
        if score >= 95:
            return "Your text looks well-written with minimal grammar issues."
        elif score >= 85:
            return f"Found {len(errors)} minor issue(s). Consider reviewing the suggestions."
        elif score >= 70:
            return f"Found {len(errors)} issue(s). Review recommended for better clarity."
        else:
            return f"Found {len(errors)} significant issue(s). Thorough revision recommended."

    def check_sentence_suggestions(self, text):
        result = self.check(text)
        suggestions = []
        for err in result.get("errors", []):
            context = text[max(0, err["offset"] - 10):err["offset"] + err["length"] + 10]
            suggestions.append({
                "original": text[err["offset"]:err["offset"] + err["length"]],
                "message": err["message"],
                "suggestions": err.get("replacements", []),
                "context": context.strip()
            })
        return suggestions

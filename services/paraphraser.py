import re
import random

class Paraphraser:
    def __init__(self):
        self._init_data()

    def _init_data(self):
        self.synonyms = {
            "important": ["significant", "crucial", "vital", "essential", "critical", "pivotal", "paramount", "indispensable", "momentous"],
            "use": ["utilize", "employ", "leverage", "apply", "harness", "draw on", "deploy", "make use of", "put to use"],
            "show": ["demonstrate", "illustrate", "indicate", "reveal", "exhibit", "suggest", "display", "evince", "prove", "attest to"],
            "make": ["create", "produce", "generate", "form", "construct", "craft", "fabricate", "compose", "assemble"],
            "help": ["assist", "aid", "support", "facilitate", "enable", "empower", "contribute to", "lend a hand"],
            "change": ["modify", "alter", "adjust", "transform", "convert", "revise", "reshape", "rework", "reconfigure"],
            "think": ["believe", "consider", "deem", "regard", "reckon", "presume", "suppose", "conclude", "maintain"],
            "find": ["discover", "locate", "identify", "detect", "uncover", "pinpoint", "come across", "stumble upon"],
            "know": ["understand", "comprehend", "recognize", "realize", "grasp", "apprehend", "be aware of", "be familiar with"],
            "big": ["large", "substantial", "considerable", "massive", "enormous", "immense", "gigantic", "colossal", "vast"],
            "good": ["excellent", "superior", "positive", "favorable", "beneficial", "advantageous", "worthwhile", "exceptional"],
            "bad": ["poor", "inferior", "negative", "adverse", "harmful", "detrimental", "substandard", "unfavorable"],
            "new": ["novel", "fresh", "innovative", "modern", "contemporary", "cutting-edge", "state-of-the-art", "advanced"],
            "many": ["numerous", "countless", "abundant", "plentiful", "lots of", "a plethora of", "myriad", "a wealth of"],
            "some": ["several", "various", "certain", "multiple", "diverse", "a handful of", "an array of"],
            "also": ["likewise", "similarly", "additionally", "moreover", "furthermore", "besides", "what is more"],
            "but": ["however", "nevertheless", "nonetheless", "yet", "although", "though", "on the other hand", "conversely"],
            "so": ["therefore", "thus", "consequently", "accordingly", "hence", "as a result", "for that reason"],
            "because": ["since", "as", "due to", "owing to", "given that", "on account of", "seeing that"],
            "improve": ["enhance", "upgrade", "refine", "optimize", "strengthen", "boost", "amplify", "augment", "polish"],
            "increase": ["boost", "raise", "elevate", "augment", "amplify", "escalate", "intensify", "expand"],
            "reduce": ["decrease", "diminish", "lessen", "lower", "minimize", "curb", "cut back on", "scale down"],
            "create": ["generate", "produce", "establish", "form", "craft", "forge", "build", "invent"],
            "develop": ["evolve", "advance", "progress", "cultivate", "foster", "nurture", "grow", "refine"],
            "ensure": ["guarantee", "assure", "confirm", "verify", "make sure", "see to it", "warrant"],
            "significant": ["considerable", "substantial", "notable", "remarkable", "striking", "prominent", "noteworthy"],
            "potential": ["possible", "latent", "prospective", "eventual", "underlying", "dormant"],
            "key": ["critical", "essential", "vital", "pivotal", "central", "fundamental", "core"],
            "transform": ["reshape", "remake", "revolutionize", "alter", "overhaul", "recast", "reimagine"],
            "balance": ["equilibrium", "trade-off", "middle ground", "counterweight", "stability"],
            "believe": ["think", "consider", "hold", "maintain", "contend", "assert", "be of the view"],
            "start": ["begin", "commence", "initiate", "launch", "embark on", "set in motion", "kick off"],
            "end": ["conclude", "terminate", "finish", "wrap up", "cease", "halt", "bring to a close"],
            "need": ["require", "necessitate", "demand", "call for", "entail", "warrant"],
            "want": ["desire", "wish", "aspire to", "seek", "aim for", "strive for"],
            "try": ["attempt", "endeavor", "strive", "seek", "make an effort", "undertake"],
            "give": ["provide", "offer", "furnish", "supply", "grant", "bestow", "confer"],
            "take": ["grasp", "seize", "capture", "obtain", "acquire", "procure"],
            "get": ["obtain", "acquire", "secure", "attain", "gain", "procure", "come by"],
            "come": ["arrive", "approach", "appear", "emerge", "materialize"],
            "go": ["proceed", "move", "travel", "advance", "head", "make one's way"],
            "have": ["possess", "own", "hold", "maintain", "keep", "occupy"],
            "say": ["state", "declare", "announce", "mention", "remark", "note", "observe", "express"],
            "ask": ["inquire", "question", "query", "request", "seek", "pose"],
            "look": ["examine", "inspect", "observe", "study", "survey", "scrutinize", "explore"],
            "see": ["witness", "observe", "perceive", "notice", "spot", "discern", "view"],
            "tell": ["inform", "notify", "advise", "brief", "apprise", "relate"],
            "add": ["contribute", "supplement", "augment", "enhance", "append", "incorporate"],
            "work": ["function", "operate", "perform", "run", "serve", "be effective"],
            "part": ["portion", "segment", "component", "element", "constituent", "fragment"],
            "thing": ["object", "item", "element", "aspect", "factor", "matter", "consideration"],
            "way": ["method", "approach", "means", "technique", "strategy", "manner", "mode"],
            "place": ["location", "site", "area", "spot", "position", "venue", "setting"],
            "right": ["correct", "accurate", "proper", "precise", "exact", "valid", "sound"],
            "wrong": ["incorrect", "inaccurate", "flawed", "erroneous", "mistaken", "false"],
            "hard": ["difficult", "challenging", "tough", "demanding", "arduous", "strenuous"],
            "easy": ["simple", "effortless", "straightforward", "uncomplicated", "smooth", "painless"],
            "old": ["aged", "ancient", "elderly", "vintage", "antique", "time-honored"],
            "young": ["youthful", "juvenile", "fresh", "new", "budding", "emerging"],
            "fast": ["rapid", "swift", "quick", "speedy", "brisk", "hasty", "expeditious"],
            "slow": ["gradual", "leisurely", "unhurried", "sluggish", "moderate", "gentle"],
            "strong": ["powerful", "robust", "sturdy", "resilient", "formidable", "potent", "mighty"],
            "weak": ["feeble", "fragile", "frail", "vulnerable", "delicate", "faint"],
            "first": ["initial", "primary", "foremost", "premier", "leading", "chief", "principal"],
            "last": ["final", "ultimate", "concluding", "terminal", "closing"],
            "main": ["primary", "principal", "chief", "central", "key", "core", "major"],
            "clear": ["apparent", "evident", "obvious", "plain", "manifest", "transparent", "unambiguous"],
            "different": ["distinct", "unique", "diverse", "varied", "contrasting", "disparate"],
            "same": ["identical", "equivalent", "uniform", "consistent", "matching", "indistinguishable"],
            "true": ["genuine", "authentic", "real", "legitimate", "valid", "accurate", "faithful"],
            "false": ["fake", "bogus", "phony", "artificial", "counterfeit", "inauthentic"],
            "always": ["continually", "consistently", "persistently", "constantly", "invariably", "perpetually"],
            "never": ["not ever", "at no time", "not once", "under no circumstances"],
            "often": ["frequently", "regularly", "commonly", "routinely", "repeatedly", "oftentimes"],
            "usually": ["typically", "generally", "normally", "ordinarily", "for the most part"],
            "maybe": ["perhaps", "possibly", "potentially", "conceivably", "arguably"],
            "actually": ["in fact", "in reality", "essentially", "as a matter of fact", "in truth"],
            "really": ["truly", "genuinely", "honestly", "undoubtedly", "certainly", "indeed"],
            "very": ["extremely", "exceedingly", "exceptionally", "remarkably", "immensely", "profoundly"],
            "quite": ["fairly", "rather", "reasonably", "moderately", "comparatively"],
            "must": ["have to", "need to", "ought to", "be required to", "should"],
            "can": ["be able to", "be capable of", "have the ability to", "be equipped to"],
            "may": ["might", "could", "possibly will", "are allowed to"],
            "should": ["ought to", "need to", "had better", "be advised to"],
            "could": ["might be able to", "would be capable of", "may possibly"],
            "only": ["merely", "solely", "simply", "just", "exclusively"],
            "also": ["likewise", "similarly", "additionally", "moreover", "furthermore"],
            "too": ["as well", "in addition", "also", "likewise"],
            "before": ["prior to", "preceding", "ahead of", "in advance of"],
            "after": ["following", "subsequent to", "later than", "upon"],
            "about": ["approximately", "roughly", "around", "in the vicinity of", "concerning"],
            "very": ["extremely", "highly", "deeply", "immensely", "tremendously"],
            "like": ["such as", "including", "similar to", "akin to", "comparable to"],
            "important": ["impactful", "consequential", "weighty", "meaningful", "substantial"],
        }

        self.contractions = {
            "do not": "don't", "does not": "doesn't", "did not": "didn't",
            "will not": "won't", "would not": "wouldn't", "should not": "shouldn't",
            "could not": "couldn't", "have not": "haven't", "has not": "hasn't",
            "had not": "hadn't", "is not": "isn't", "are not": "aren't",
            "was not": "wasn't", "were not": "weren't", "cannot": "can't",
            "it is": "it's", "that is": "that's", "they are": "they're",
            "we are": "we're", "you are": "you're", "i am": "i'm",
            "i have": "i've", "we have": "we've", "they have": "they've",
            "there is": "there's", "there are": "there're",
        }

        self.colloquial_map = {
            "therefore": ["so", "that is why", "which means", "hence", "as a result"],
            "consequently": ["as a result", "because of that", "that is why", "so then"],
            "furthermore": ["besides", "what is more", "on top of that", "not only that but"],
            "additionally": ["plus", "also", "on top of that", "to top it off"],
            "nevertheless": ["still", "even so", "that said", "all the same", "be that as it may"],
            "numerous": ["lots of", "plenty of", "countless", "a ton of", "loads of"],
            "currently": ["right now", "nowadays", "these days", "at the moment", "as of now"],
            "demonstrate": ["show", "prove", "make clear", "drive home"],
            "utilize": ["use", "make use of", "put to work", "draw upon"],
            "facilitate": ["make easier", "help along", "smooth the way for", "enable"],
            "implement": ["carry out", "put into action", "roll out", "execute"],
            "encounter": ["come across", "run into", "face", "meet with"],
            "endeavor": ["try", "make an effort", "give it a shot", "have a go at"],
            "purchased": ["bought", "picked up", "got hold of", "snagged"],
            "reside": ["live", "dwell", "stay", "hang one's hat"],
            "assist": ["help out", "lend a hand", "give a hand", "aid"],
            "commence": ["start", "kick off", "get going", "begin"],
            "terminate": ["end", "wrap up", "cut short", "bring to a close"],
            "obtain": ["get", "land", "score", "secure", "come by"],
            "sufficient": ["enough", "plenty of", "adequate", "all that is needed"],
            "attempt": ["try", "give it a go", "make an effort", "take a shot at"],
            "respond": ["answer back", "get back to", "reply", "write back"],
            "request": ["ask for", "put in for", "call for", "seek"],
            "require": ["need", "call for", "demand", "necessitate"],
        }

        self.hedges = ["sort of", "kind of", "pretty much", "more or less", "in a way",
                       "to some extent", "arguably", "presumably", "basically", "essentially",
                       "in a sense", "for the most part", "to a degree", "by and large"]

        self.idioms = [
            "at the end of the day", "when it comes down to it", "in the grand scheme of things",
            "what it all boils down to", "at the heart of the matter", "when all is said and done",
            "the bottom line is", "at the core of it", "the long and short of it",
            "in the bigger picture", "when you look at the bigger picture",
        ]

        self.rhetorical_starters = [
            "Here is the thing", "The truth is", "Let us be real", "Fact of the matter is",
            "What matters most is", "At the end of the day", "When you think about it",
            "Makes you wonder", "Here is what we know", "Let me put it this way",
        ]

        self.personal_reactions = [
            "I find that", "What strikes me is", "It is worth noting that",
            "I would argue that", "I tend to think", "What stands out is",
            "One has to consider", "It is safe to say that",
        ]

        self.discourse_markers = [
            "Well,", "Actually,", "Honestly,", "Truth is,", "I mean,",
            "Look,", "The thing is,", "Here is the deal,", "See,",
            "After all,", "In fact,", "To be fair,", "To be honest,",
            "Without a doubt,", "Of course,", "Naturally,", "Sure,",
            "On that note,", "With that said,", "All things considered,",
            "In any case,", "Be that as it may,", "Then again,",
        ]

        self.sentence_joiners = [
            "and", "but then", "while", "though", "yet", "so then",
            "after which", "plus", "not to mention", "along with",
        ]

        self.filler_sentences = [
            "Makes you think.", "Go figure.", "Funny how that works.",
            "Worth considering.", "Think about that.", "It really does.",
            "No question about it.", "Hard to argue with that.",
            "Goes to show.", "That is something.", "Makes sense, right?",
            "Kinda wild.", "Not bad at all.", "Quite revealing, actually.",
            "That speaks volumes.", "Says a lot, does not it?",
            "Goes without saying.", "Curious, is not it?",
            "Certainly gives you pause.", "Makes you reconsider.",
            "One of those things.", "That much is clear.",
            "Hard to ignore.", "Pretty telling.", "Par for the course.",
        ]

        self.voice_alternations = {
            "is": ["is", "remains", "stays", "stands as"],
            "are": ["are", "remain", "stay", "stand as"],
            "was": ["was", "remained", "stood as"],
            "were": ["were", "remained", "stood as"],
            "has": ["has", "possesses", "holds"],
            "have": ["have", "possess", "hold"],
            "need": ["need", "require", "demand", "call for"],
        }

        self.sentence_openers = [
            "It is worth noting that", "Interestingly enough,",
            "One cannot ignore that", "It should be said that",
            "What is interesting is that", "The fact remains that",
            "Chances are that", "More often than not,",
            "By and large,", "For the most part,",
            "In many ways,", "On the whole,",
            "As a general rule,", "Without question,",
        ]

    def paraphrase(self, text, intensity="medium"):
        sents = self._split(text)
        if not sents: return {"original": text, "paraphrased": text, "changes": 0}
        level = {"low": 0.4, "medium": 0.6, "high": 0.9}.get(intensity, 0.6)
        out = [self._swap(s, level)["text"] for s in sents]
        return {"original": text, "paraphrased": " ".join(out), "changes": sum(
            self._swap(s, level)["changes"] for s in sents),
                "intensity": intensity, "word_count_original": len(text.split()),
                "word_count_new": len(" ".join(out).split())}

    def _restructure_sentence(self, s):
        words = s.split()
        if len(words) < 5:
            return s
        clauses = re.split(r'\b(and|but|or|yet|so|because|since|although|whereas|unless|until|after|before|if)\b', s, flags=re.IGNORECASE)
        if len(clauses) > 1:
            for i in range(1, len(clauses), 2):
                conn = clauses[i].strip().lower()
                switch = {"and": ["and", "plus", "along with", "coupled with"],
                          "but": ["yet", "though", "still", "nevertheless"],
                          "or": ["or", "or alternatively", "or else"],
                          "yet": ["but still", "yet", "and yet", "still"],
                          "so": ["which is why", "as a result", "so that"],
                          "because": ["since", "seeing as", "given that", "for the reason that"],
                          "since": ["because", "given that", "seeing that"],
                          "although": ["though", "even though", "while", "despite"],
                          "whereas": ["while", "on the other hand", "by contrast"],
                          "unless": ["if not", "except when", "without"],
                          "until": ["till", "up to", "through"],
                          "after": ["once", "following", "upon"],
                          "before": ["until", "prior to", "ahead of"],
                          "if": ["provided that", "assuming", "supposing", "as long as"]}
                if conn in switch and random.random() < 0.45:
                    clauses[i] = " " + random.choice(switch[conn]) + " "
            s = "".join(clauses)
        if s.startswith("However,"):
            s = s[len("However,"):].lstrip()
            s = s[0].lower() + s[1:]
            if s.endswith("."): s = s[:-1]
            s = s.rstrip(",") + ", however."
        return s

    def _invert_voice(self, s):
        subj = re.search(r'^([A-Z][^,]*?)\s+(is|are|was|were|has been|have been|will be)\s+(\w+ed|\w+en)\s+', s)
        if subj and random.random() < 0.35:
            return ("It is " + subj.group(3) + " by " + subj.group(1) + " that " +
                    s[subj.end():] if s[subj.end():].strip() else s)
        return s

    def humanize(self, text):
        sents = self._split(text)
        if not sents: return {"original": text, "humanized": text, "changes": 0}

        sents = [s.strip() for s in sents if s.strip()]
        if len(sents) < 2:
            r = self._swap(sents[0], 1.0)
            return {"original": text, "humanized": r["text"], "changes": r["changes"],
                    "word_count_original": len(text.split()),
                    "word_count_new": len(r["text"].split())}
        tc = 0

        # STEP 1: heavy word-level + discourse transformations
        for i in range(len(sents)):
            s = sents[i]
            orig_len = len(s.split())

            for f, o in self.colloquial_map.items():
                if f in s.lower():
                    s = re.sub(re.escape(f), random.choice(o), s, count=1, flags=re.IGNORECASE)
                    tc += 1

            r = self._swap(s, 0.95)
            s = r["text"]; tc += r["changes"]

            for f, sh in self.contractions.items():
                if f in s.lower() and random.random() < 0.5:
                    s = re.sub(re.escape(f), sh, s, count=1, flags=re.IGNORECASE)
                    tc += 1
                    break

            s = self._restructure_sentence(s)

            if i > 0 and i % 2 == 0:
                discourse_starts = ("well", "actually", "honestly", "truth", "i mean", "look",
                                    "the thing", "and", "however", "therefore", "thus", "hence",
                                    "consequently", "furthermore", "moreover", "additionally",
                                    "meanwhile", "nevertheless", "nonetheless", "still", "yet",
                                    "finally", "lastly", "first", "second", "third")
                if not s.lower().startswith(discourse_starts):
                    s = random.choice(self.discourse_markers) + " " + s[0].lower() + s[1:]
                    tc += 1

            if random.random() < 0.35:
                h = random.choice(self.hedges)
                s = re.sub(r'\b(is|are|was|were|has|have|had|will|would|can|could|may|might)\b',
                           lambda m: m.group(1) + " " + h, s, count=1)
                tc += 1

            if random.random() < 0.25:
                s = self._invert_voice(s)
                tc += 1

            sents[i] = s

        # STEP 2: split at conjunctions to restructure
        split_sents = []
        for s in sents:
            words_s = s.split()
            if len(words_s) <= 7 or random.random() >= 0.6:
                split_sents.append(s)
                continue

            s_lower = s.lower()
            split_at = None

            for sep in [", but ", ", yet ", ", so "]:
                idx = s_lower.find(sep)
                if idx >= 0:
                    lhs = s[:idx].strip().split(); rhs = s[idx+len(sep):].strip().split()
                    if len(lhs) >= 3 and len(rhs) >= 3:
                        split_at = idx
                        break

            for sep in [" because ", " although ", " while ", " whereas ",
                         " unless ", " after ", " before ", " if "]:
                if split_at is not None: break
                idx = s_lower.find(sep)
                if idx >= 0:
                    lhs = s[:idx].split(); rhs = s[idx:].split()
                    if len(lhs) >= 3 and len(rhs) >= 3:
                        split_at = idx
                        break

            if split_at is not None:
                first = s[:split_at].strip().rstrip(",")
                second = s[split_at:].strip().lstrip(",").lstrip()
                if first and second:
                    frags = ["makes you think", "go figure", "funny how that works",
                             "worth thinking about", "believe it or not",
                             "interesting how that works", "quite something"]
                    split_sents.append(first + ", " + random.choice(frags) + ".")
                    if second[0].islower():
                        second = second[0].upper() + second[1:]
                    split_sents.append(second)
                    tc += 2
                    continue
            split_sents.append(s)
        sents = split_sents

        # STEP 3: insert 2-5 conversational filler sentences
        random.shuffle(self.filler_sentences)
        num_fillers = min(random.randint(2, 5), max(1, len(sents) - 1), len(self.filler_sentences))
        used_fillers = set()
        for f in self.filler_sentences[:num_fillers]:
            if f in used_fillers: continue
            pos = random.randint(1, len(sents) - 1)
            sents.insert(pos, f)
            used_fillers.add(f)
            tc += 1

        # STEP 4: idiomatic opener injection
        if random.random() < 0.5 and sents:
            opener = random.choice(self.idioms)
            sents[0] = opener[0].upper() + opener[1:] + ", " + sents[0][0].lower() + sents[0][1:]
            tc += 1

        # STEP 5: merge 2 pairs of adjacent content sentences
        for _ in range(random.randint(1, 3)):
            if len(sents) <= 3: break
            join_idx = random.randint(0, len(sents) - 2)
            for _ in range(15):
                a, b = sents[join_idx].strip(), sents[join_idx+1].strip()
                if not a.endswith("?") and not b.endswith("?") and not b.startswith("Makes") and not b.startswith("Goes"):
                    break
                join_idx = random.randint(0, len(sents) - 2)
            tail = sents[join_idx+1]
            if len(tail.split()) > 4:
                joiner = random.choice(self.sentence_joiners)
                new_s = sents[join_idx].rstrip(".!?").rstrip() + " " + joiner + " " + tail[0].lower() + tail[1:]
                sents[join_idx] = new_s
                del sents[join_idx+1]
                tc += 1

        # STEP 6: inject personal reaction before last sentence
        if len(sents) >= 3 and random.random() < 0.5:
            reaction = random.choice(self.personal_reactions)
            sents.insert(-1, reaction + " " + sents[-1][0].lower() + sents[-1][1:])
            tc += 1

        output = " ".join(sents)

        # STEP 7: cleanup
        sents2 = self._split(output)
        for j in range(len(sents2)):
            sj = sents2[j].strip()
            if sj and sj[0].islower() and len(sj) > 1:
                sents2[j] = sj[0].upper() + sj[1:]
            sents2[j] = re.sub(r'^\s*[,;:]\s*', '', sents2[j])

        output = " ".join(sents2)
        output = re.sub(r'\s+', ' ', output).strip()
        output = re.sub(r'\s+,', ',', output)
        output = re.sub(r',\s*,', ', ', output)
        output = re.sub(r'\s+\.', '.', output)
        output = re.sub(r'\bi\b', 'I', output)

        if output and output[-1] not in ".!?":
            output += "."

        return {"original": text, "humanized": output, "changes": tc,
                "word_count_original": len(text.split()),
                "word_count_new": len(output.split())}

    def bypass_ai_detection(self, text):
        sents = self._split(text)
        if not sents: return {"original": text, "bypassed": text, "changes": 0}

        sents = [s.strip() for s in sents if s.strip()]
        if len(sents) < 2:
            r = self._swap(sents[0], 0.80)
            return {"original": text, "bypassed": r["text"], "changes": r["changes"],
                    "word_count_original": len(text.split()),
                    "word_count_new": len(r["text"].split())}
        tc = 0

        # STEP 1: word-level + structural transformations on original sentences
        for i in range(len(sents)):
            s = sents[i]

            for f, o in self.colloquial_map.items():
                if f in s.lower():
                    s = re.sub(re.escape(f), random.choice(o), s, count=1, flags=re.IGNORECASE)
                    tc += 1

            r = self._swap(s, 0.80)
            s = r["text"]; tc += r["changes"]

            if random.random() < 0.5:
                for f, sh in self.contractions.items():
                    if f in s.lower():
                        s = re.sub(re.escape(f), sh, s, count=1, flags=re.IGNORECASE)
                        tc += 1
                        break

            s = self._restructure_sentence(s)

            if random.random() < 0.3:
                if not s.lower().startswith(("how", "why", "what", "do", "does", "did", "is", "are")):
                    s = random.choice(self.sentence_openers) + " " + s[0].lower() + s[1:]
                    tc += 1

            sents[i] = s

        # STEP 2: inject 2-4 filler sentences strategically
        random.shuffle(self.filler_sentences)
        num_fillers = min(random.randint(2, 4), max(1, len(sents) - 1))
        used = set()
        for f in self.filler_sentences[:num_fillers]:
            if f in used: continue
            pos = random.randint(1, len(sents) - 1)
            sents.insert(pos, f)
            used.add(f)
            tc += 1

        # STEP 3: merge 2 pairs of adjacent sentences for long/short variation
        for _ in range(random.randint(1, 2)):
            if len(sents) <= 3: break
            join_idx = random.randint(0, len(sents) - 2)
            for _ in range(15):
                if not (sents[join_idx].endswith("?") or sents[join_idx+1].endswith("?")):
                    break
                join_idx = random.randint(0, len(sents) - 2)
            tail = sents[join_idx+1]
            if len(tail.split()) > 3:
                joiner = random.choice(self.sentence_joiners)
                sents[join_idx] = sents[join_idx].rstrip(".!?").rstrip() + " " + joiner + " " + tail[0].lower() + tail[1:]
                del sents[join_idx+1]
                tc += 1

        # STEP 4: reorder 1 pair of adjacent sentences (swap order)
        if len(sents) >= 4 and random.random() < 0.3:
            swap_idx = random.randint(0, len(sents) - 2)
            a, b = sents[swap_idx], sents[swap_idx+1]
            if (not a.endswith("?") and not b.endswith("?") and
                len(a.split()) >= 4 and len(b.split()) >= 4):
                sents[swap_idx], sents[swap_idx+1] = b, a
                tc += 1

        # STEP 5: inject rhetorical starter at beginning
        if random.random() < 0.4 and sents:
            starter = random.choice(self.rhetorical_starters)
            sents[0] = starter + ", " + sents[0][0].lower() + sents[0][1:]
            tc += 1

        # STEP 6: idiom injection mid-text
        if len(sents) >= 3 and random.random() < 0.35:
            idx = random.randint(1, len(sents) - 1)
            idiom = random.choice(self.idioms)
            sents[idx] = idiom[0].upper() + idiom[1:] + ", " + sents[idx][0].lower() + sents[idx][1:]
            tc += 1

        output = " ".join(sents)

        # cleanup
        sents2 = self._split(output)
        for j in range(len(sents2)):
            sj = sents2[j].strip()
            if sj and sj[0].islower() and len(sj) > 1:
                sents2[j] = sj[0].upper() + sj[1:]
        output = " ".join(sents2)
        output = re.sub(r'\s+', ' ', output).strip()
        output = re.sub(r'\s+,', ',', output)
        output = re.sub(r',\s*,', ', ', output)
        output = re.sub(r'\s+\.', '.', output)
        output = re.sub(r'\bi\b', 'I', output)

        if output and output[-1] not in ".!?":
            output += "."

        return {"original": text, "bypassed": output, "changes": tc,
                "word_count_original": len(text.split()),
                "word_count_new": len(output.split())}

    def _swap(self, text, level):
        words = text.split(); c = 0; out = []
        for w in words:
            cl = w.strip(".,!?;:'\"()[]{}").lower()
            p = w[len(cl):] if len(cl) < len(w) else ""
            if cl in self.synonyms and random.random() < level:
                ch = random.choice(self.synonyms[cl])
                if " " in ch:
                    out.append(ch + p); c += 1; continue
                if ch != cl:
                    if w[0].isupper(): ch = ch[0].upper() + ch[1:]
                    out.append(ch + p); c += 1; continue
            out.append(w)
        return {"text": " ".join(out), "changes": c}

    def _split(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        s = re.split(r'(?<=[.!?])\s+', text)
        return [x.strip() for x in s if x.strip()]

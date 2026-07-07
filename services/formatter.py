import re
import random

class TextFormatter:
    def __init__(self):
        self.section_keywords = [
            "introduction", "intro", "overview", "background",
            "benefits", "advantages", "pros", "why",
            "eligibility", "requirements", "criteria", "qualifications", "who can",
            "how to apply", "application process", "steps", "procedure",
            "deadline", "deadlines", "important dates", "timeline",
            "documents required", "required documents", "what you need",
            "selection process", "evaluation", "how we evaluate",
            "tips", "advice", "recommendations", "suggestions",
            "faq", "frequently asked questions", "common questions",
            "contact", "contact information", "contact us",
            "conclusion", "summary", "final thoughts", "wrapping up",
            "terms", "conditions", "terms and conditions",
            "note", "important note", "disclaimer",
        ]

        self.list_markers = [
            r"^\d+[\.\)]", r"^[a-z][\.\)]", r"^[ivxlcdm]+[\.\)]",
            r"^[-*]", r"^first(ly)?,", r"^second(ly)?,", r"^third(ly)?,",
            r"^next,", r"^finally,", r"^lastly,", r"^also,",
        ]

    def format(self, text, format_type="auto"):
        if not text.strip():
            return {"original": text, "formatted": "", "format_type": format_type}

        format_type = format_type or "auto"
        detected = self._detect_input_structure(text)

        format_map = {
            "paragraphs": self._format_paragraphs,
            "bullet-list": self._format_bullet_list,
            "numbered-list": self._format_numbered_list,
            "blog-post": self._format_blog_post,
            "auto": self._auto_format,
            "title-case": self._format_title_case,
            "sentence-case": self._format_sentence_case,
            "code-block": self._format_code_block,
            "remove-whitespace": self._format_remove_whitespace,
            "uppercase": self._format_uppercase,
            "lowercase": self._format_lowercase,
            "email": self._format_email,
            "markdown-table": self._format_markdown_table,
        }
        formatter = format_map.get(format_type, self._auto_format)
        formatted = formatter(text)

        return {
            "original": text,
            "formatted": formatted,
            "format_type": format_type,
            "word_count_original": len(text.split()),
            "word_count_new": len(formatted.split()),
            "detected_structure": detected,
        }

    def _detect_input_structure(self, text):
        blocks = self._parse_to_blocks(text)
        if not blocks:
            return {"type": "empty", "label": "Empty text"}

        has_headings = any(b[0] == 'heading' for b in blocks)
        has_lists = any(b[0] in ('ul', 'ol') for b in blocks)
        has_paragraphs = any(b[0] == 'para' for b in blocks)
        block_count = len(blocks)
        list_items = sum(len(b[1]) for b in blocks if b[0] in ('ul', 'ol'))
        heading_count = sum(1 for b in blocks if b[0] == 'heading')

        details = {
            "blocks": block_count,
            "headings": heading_count,
            "list_items": list_items,
        }

        if block_count == 1:
            bt, bc = blocks[0]
            if bt == 'para':
                sents = self._sentences(bc)
                if len(sents) <= 3:
                    details["type"] = "short-text"
                    details["label"] = "Short text"
                elif len(sents) <= 8:
                    details["type"] = "paragraph"
                    details["label"] = "Single paragraph"
                else:
                    details["type"] = "long-paragraph"
                    details["label"] = "Long text"
            elif bt == 'ul':
                details["type"] = "bullet-list"
                details["label"] = f"Bullet list ({list_items} items)"
            elif bt == 'ol':
                details["type"] = "numbered-list"
                details["label"] = f"Numbered list ({list_items} items)"
            elif bt == 'heading':
                details["type"] = "single-heading"
                details["label"] = "Single heading"
        elif has_headings and has_lists:
            details["type"] = "structured-document"
            parts = []
            if heading_count:
                parts.append(f"{heading_count} heading{'s' if heading_count > 1 else ''}")
            if list_items:
                parts.append(f"{list_items} list item{'s' if list_items > 1 else ''}")
            if has_paragraphs:
                details["label"] = f"Structured document — {' + '.join(parts)}"
            else:
                details["label"] = f"Heading{'s' if heading_count > 1 else ''} with lists — {' + '.join(parts)}"
        elif has_headings:
            details["type"] = "headings-only"
            details["label"] = f"Section headings ({heading_count} heading{'s' if heading_count > 1 else ''})"
        elif has_lists:
            details["type"] = "mixed-lists"
            ul_count = sum(1 for b in blocks if b[0] == 'ul')
            ol_count = sum(1 for b in blocks if b[0] == 'ol')
            labels = []
            if ul_count:
                labels.append(f"{ul_count} bullet list{'s' if ul_count > 1 else ''}")
            if ol_count:
                labels.append(f"{ol_count} numbered list{'s' if ol_count > 1 else ''}")
            details["label"] = ' + '.join(labels)
        else:
            details["type"] = "paragraphs"
            details["label"] = f"{block_count} paragraph{'s' if block_count > 1 else ''}"

        return details

    def _split_paragraphs(self, text):
        paras = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paras if p.strip()]

    def _sentences(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        sents = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sents if s.strip()]

    def _detect_sections(self, text):
        sents = self._sentences(text)
        sections = []
        current_label = None
        current_items = []

        for s in sents:
            word_count = len(s.split())
            s_lower = s.lower().rstrip(".:")
            kw_match = None
            skip = 0

            skip_verbs = ["is", "are", "was", "were", "has", "have", "had", "includes", "include"]
            for kw in self.section_keywords:
                if s_lower == kw or s_lower == "the " + kw:
                    kw_match = kw; skip = len(s); break
                if s_lower.startswith(kw + ":") or s_lower.startswith("the " + kw + ":"):
                    kw_match = kw; skip = s_lower.index(":") + 1; break
                if word_count <= 5:
                    after_kw = s_lower[len(kw):].strip()
                    after_the = s_lower[len("the " + kw):].strip() if s_lower.startswith("the ") else ""
                    next_word = (after_kw.split()[0] if after_kw else "")
                    next_word_the = (after_the.split()[0] if after_the else "")
                    if s_lower.startswith(kw + " ") and next_word not in skip_verbs:
                        kw_match = kw; skip = len(kw); break
                    if s_lower.startswith("the " + kw + " ") and next_word_the not in skip_verbs:
                        kw_match = kw; skip = len(kw) + 4; break

            if kw_match:
                if current_label or current_items:
                    sections.append((current_label or "intro", current_items))
                current_label = kw_match
                rest = s[skip:].strip(" ,.:;").strip()
                current_items = [rest] if rest else []
            else:
                current_items.append(s)

        if current_label is not None or current_items:
            sections.append((current_label or "intro", current_items))

        if not sections and sents:
            sections = [("intro", sents)]

        return sections

    def _is_list_item(self, sent):
        for pattern in self.list_markers:
            if re.match(pattern, sent, re.IGNORECASE):
                return True
        return False

    def _is_list_section(self, sents):
        if len(sents) <= 1:
            return False
        list_count = sum(1 for s in sents if self._is_list_item(s))
        short_count = sum(1 for s in sents if len(s.split()) <= 12)
        return list_count >= len(sents) * 0.3 or short_count >= len(sents) * 0.6

    def _parse_to_blocks(self, text):
        lines = text.split('\n')
        blocks = []
        current_para = []

        def is_heading(line):
            stripped = line.strip()
            if not stripped:
                return False
            # Don't classify list items as headings
            if re.match(r'^[\d]+[\.\)]\s', stripped) or re.match(r'^[\-\*\•]\s', stripped):
                return False
            if len(stripped) < 70 and not stripped.rstrip().endswith('.') and not stripped.rstrip().endswith(':'):
                words = stripped.split()
                if 1 <= len(words) <= 10:
                    return True
            if stripped.rstrip().endswith(':'):
                return True
            if stripped.lower().rstrip('.:') in self.section_keywords:
                return True
            if stripped.isupper() and len(stripped) < 60 and len(stripped.split()) <= 6:
                return True
            return False

        def is_list_line(line):
            stripped = line.strip()
            if not stripped:
                return False
            if re.match(r'^[\d]+[\.\)]\s', stripped):
                return 'ol'
            if re.match(r'^[a-z][\.\)]\s', stripped):
                return 'ol'
            if re.match(r'^[ivxlcdm]+[\.\)]\s', stripped.lower()):
                return 'ol'
            if re.match(r'^[\-\*\•]\s', stripped):
                return 'ul'
            if len(stripped.split()) <= 14:
                first_word = stripped.split()[0].lower().rstrip(',;')
                if first_word in ['first', 'second', 'third', 'next', 'then', 'finally', 'lastly', 'also', 'another', 'additionally', 'furthermore', 'moreover', 'including']:
                    return 'ul'
            return None

        i = 0
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()

            if not stripped:
                if current_para:
                    blocks.append(('para', ' '.join(current_para)))
                    current_para = []
                i += 1
                continue

            if is_heading(raw):
                if current_para:
                    blocks.append(('para', ' '.join(current_para)))
                    current_para = []
                list_type = None
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    lt = is_list_line(lines[j])
                    if lt:
                        list_type = lt
                        break
                    if is_heading(lines[j]) or j - i > 10:
                        break
                    j += 1

                if list_type:
                    items = []
                    j = i + 1
                    saw_content_after_blank = False
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            if items:
                                saw_content_after_blank = True
                            j += 1
                            continue
                        if saw_content_after_blank:
                            break
                        lt = is_list_line(lines[j])
                        if lt == list_type:
                            cleaned = re.sub(r'^[\d\.,\)\-\*\•\s]+', '', next_line).strip()
                            items.append(cleaned if cleaned else next_line)
                        elif not lt and next_line and len(next_line.split()) <= 14 and items:
                            cleaned = re.sub(r'^[\d\.,\)\-\*\•\s]+', '', next_line).strip()
                            if cleaned.lower().rstrip('.:') in self.section_keywords or (cleaned.endswith(':') and len(cleaned.split()) <= 6):
                                break
                            items.append(cleaned if cleaned else next_line)
                        else:
                            break
                        j += 1
                    non_heading_items = []
                    for item in items:
                        if not (item.lower().rstrip('.:') in self.section_keywords or (item.endswith(':') and len(item.split()) <= 6)):
                            non_heading_items.append(item)
                    if non_heading_items:
                        blocks.append(('heading', stripped))
                        blocks.append((list_type, non_heading_items))
                        i = j
                        continue

                blocks.append(('heading', stripped))
                i += 1
                continue

            lt = is_list_line(raw)
            if lt:
                if current_para:
                    blocks.append(('para', ' '.join(current_para)))
                    current_para = []
                items = []
                j = i
                saw_blank = False
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        if items:
                            saw_blank = True
                        j += 1
                        continue
                    if saw_blank:
                        break
                    llt = is_list_line(lines[j])
                    if llt == lt:
                        cleaned = re.sub(r'^[\d\.,\)\-\*\•\s]+', '', next_line).strip()
                        items.append(cleaned if cleaned else next_line)
                    elif not llt and next_line and len(next_line.split()) <= 14 and items:
                        cleaned = re.sub(r'^[\d\.,\)\-\*\•\s]+', '', next_line).strip()
                        if cleaned.lower().rstrip('.:') in self.section_keywords or (cleaned.endswith(':') and len(cleaned.split()) <= 6):
                            break
                        items.append(cleaned if cleaned else next_line)
                    else:
                        break
                    j += 1
                blocks.append((lt, items))
                i = j
                continue

            current_para.append(stripped)
            i += 1

        if current_para:
            blocks.append(('para', ' '.join(current_para)))

        if not blocks:
            sents = self._sentences(text)
            if sents:
                sections = self._detect_sections(text)
                for label, sents in sections:
                    heading = label[0].upper() + label[1:] if label and label != "intro" else ""
                    if not heading or heading == "Intro":
                        heading = "Introduction"
                    blocks.append(('heading', heading))
                    if self._is_list_section(sents):
                        items = [re.sub(r'^[\d\.,\)\-\*\s]+', '', s).strip() or s for s in sents]
                        blocks.append(('ul', items))
                    else:
                        blocks.append(('para', ' '.join(sents)))

        return blocks

    def _blocks_to_html(self, blocks):
        html_parts = []
        for block_type, content in blocks:
            if block_type == 'heading':
                html_parts.append(f'<h3>{content}</h3>')
            elif block_type == 'ul':
                items_html = ''.join(f'<li>{item}</li>' for item in content)
                html_parts.append(f'<ul>{items_html}</ul>')
            elif block_type == 'ol':
                items_html = ''.join(f'<li>{item}</li>' for item in content)
                html_parts.append(f'<ol>{items_html}</ol>')
            elif block_type == 'para':
                html_parts.append(f'<p>{content}</p>')
        return '\n'.join(html_parts)

    def _auto_format(self, text):
        blocks = self._parse_to_blocks(text)
        return self._blocks_to_html(blocks)

    def _format_paragraphs(self, text):
        blocks = self._parse_to_blocks(text)
        transformed = []
        for bt, bc in blocks:
            if bt == 'heading':
                transformed.append((bt, bc))
            elif bt in ('ul', 'ol'):
                para = '. '.join(bc) + '.'
                transformed.append(('para', para))
            elif bt == 'para':
                transformed.append((bt, bc))
        return self._blocks_to_html(transformed)

    def _format_bullet_list(self, text):
        blocks = self._parse_to_blocks(text)
        transformed = []
        for bt, bc in blocks:
            if bt == 'heading':
                transformed.append((bt, bc))
            elif bt in ('ul', 'ol'):
                transformed.append(('ul', bc))
            elif bt == 'para':
                sents = self._sentences(bc)
                items = [s for s in sents if s]
                if items:
                    transformed.append(('ul', items))
        return self._blocks_to_html(transformed)

    def _format_numbered_list(self, text):
        blocks = self._parse_to_blocks(text)
        transformed = []
        for bt, bc in blocks:
            if bt == 'heading':
                transformed.append((bt, bc))
            elif bt in ('ul', 'ol'):
                transformed.append(('ol', bc))
            elif bt == 'para':
                sents = self._sentences(bc)
                items = [s for s in sents if s]
                if items:
                    transformed.append(('ol', items))
        return self._blocks_to_html(transformed)

    def _format_blog_post(self, text):
        sections = self._detect_sections(text)
        output_parts = []

        for label, sents in sections:
            heading = label[0].upper() + label[1:] if label and label != "intro" else ""
            if not heading:
                heading = "Introduction"
            if heading == "Intro":
                heading = "Introduction"

            if self._is_list_section(sents):
                output_parts.append(f"<h3>{heading}</h3>")
                output_parts.append("<ul>")
                cleaned = []
                for s in sents:
                    s_clean = re.sub(r'^[\d\.,\)\-\*\s]+', '', s).strip()
                    if s_clean:
                        cleaned.append(s_clean)
                if not cleaned:
                    cleaned = sents
                for item in cleaned:
                    output_parts.append(f"<li>{item}</li>")
                output_parts.append("</ul>")
            else:
                output_parts.append(f"<h3>{heading}</h3>")
                para_text = " ".join(sents)
                output_parts.append(f"<p>{para_text}</p>")

        html = "\n".join(output_parts)
        return html

    def _format_title_case(self, text):
        blocks = self._parse_to_blocks(text)
        minor = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'with', 'in', 'of', 'is', 'as'}
        transformed = []
        for bt, bc in blocks:
            if bt == 'heading':
                transformed.append((bt, self._title_case_str(bc, minor)))
            elif bt in ('ul', 'ol'):
                transformed.append((bt, [self._title_case_str(item, minor) for item in bc]))
            elif bt == 'para':
                transformed.append((bt, self._title_case_str(bc, minor)))
        return self._blocks_to_html(transformed)

    def _title_case_str(self, text, minor):
        words = text.split()
        titled = []
        for i, w in enumerate(words):
            clean = w.strip(".,!?;:'\"()[]{}")
            punct = w[len(clean):] if len(clean) < len(w) else ""
            if i == 0 or i == len(words) - 1 or clean.lower() not in minor:
                titled.append(clean[0].upper() + clean[1:] + punct)
            else:
                titled.append(clean.lower() + punct)
        return ' '.join(titled)

    def _format_sentence_case(self, text):
        blocks = self._parse_to_blocks(text)
        transformed = []
        for bt, bc in blocks:
            if bt == 'heading':
                transformed.append((bt, bc[0].upper() + bc[1:] if bc else bc))
            elif bt in ('ul', 'ol'):
                items = []
                for item in bc:
                    s = item.strip()
                    items.append(s[0].upper() + s[1:] if s else s)
                transformed.append((bt, items))
            elif bt == 'para':
                sents = self._sentences(bc)
                out = []
                for s in sents:
                    s = s.strip()
                    if s:
                        s = s[0].upper() + s[1:]
                    out.append(s)
                transformed.append(('para', ' '.join(out)))
        return self._blocks_to_html(transformed)

    def _format_code_block(self, text):
        escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<pre><code>{escaped}</code></pre>'

    def _format_remove_whitespace(self, text):
        import re
        lines = re.sub(r'[ \t]+', ' ', text).strip().split('\n')
        lines = [l.strip() for l in lines if l.strip()]
        if not lines:
            lines = ['']
        return '\n\n'.join(f'<p>{l}</p>' for l in lines)

    def _format_uppercase(self, text):
        return f'<p style="text-transform:uppercase;">{text.upper()}</p>'

    def _format_lowercase(self, text):
        return f'<p style="text-transform:lowercase;">{text.lower()}</p>'

    def _format_email(self, text):
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        parts = []
        current_section = None
        section_lines = []
        for l in lines:
            lower = l.lower()
            if any(kw in lower for kw in ['dear ', 'hello ', 'hi ', 'to ', 'subject:', 're:', 'from:', 'cc:', 'bcc:']):
                if current_section and section_lines:
                    parts.append((current_section, section_lines))
                current_section = l
                section_lines = []
            else:
                section_lines.append(l)
        if current_section and section_lines:
            parts.append((current_section, section_lines))
        if not parts:
            parts.append(("Email", lines))

        html_parts = []
        for section, content in parts:
            if content:
                para = ' '.join(content)
                html_parts.append(f'<p>{para}</p>')
        return '\n'.join(html_parts)

    def _format_markdown_table(self, text):
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return '<p>No content</p>'
        rows = [l.split('|') for l in lines if l.count('|') >= 2]
        if not rows:
            rows = [l.split('\t') for l in lines if '\t' in l]
        if not rows:
            rows = [l.split(',') for l in lines]
        if not rows:
            rows = [l.split() for l in lines]

        html = '<table style="border-collapse:collapse;width:100%;margin:8px 0;">'
        for i, row in enumerate(rows):
            tag = 'th' if i == 0 else 'td'
            style = ('background:var(--bg-input);font-weight:600;text-align:center;' if i == 0 else '')
            html += '<tr>'
            for cell in row:
                cell = cell.strip().strip('|').strip()
                html += f'<{tag} style="border:1px solid var(--border);padding:6px 10px;{style}">{cell}</{tag}>'
            html += '</tr>'
        html += '</table>'
        return html

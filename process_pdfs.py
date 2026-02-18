import fitz  # PyMuPDF
import json
import os
import re
import hashlib
from pathlib import Path

def extract_state_year(filename):
    """Extract state and year from filenames like 'Alabama2025.pdf'"""
    name = Path(filename).stem  # Remove .pdf extension
    
    # Match one or more capitalized words followed by a 4-digit year
    match = re.match(r'^([A-Za-z ]+?)(\d{4})$', name.strip())
    if match:
        state = match.group(1).strip()
        year = match.group(2)
        return state, year
    return None, None

def clean_text(text):
    """Clean extracted text"""
    # Collapse excessive whitespace and newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Rejoin hyphenated line breaks
    text = re.sub(r'-\n(\w)', r'\1', text)
    return text.strip()

def get_file_hash(filepath):
    """Generate a unique ID from the file contents"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()[:8]

def process_pdfs(pdf_dir, output_path, error_path):
    records = []
    errors = []

    pdf_files = list(Path(pdf_dir).rglob('*.pdf'))
    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        try:
            state, year = extract_state_year(pdf_path.name)
            doc = fitz.open(str(pdf_path))

            pages_text = []
            for page in doc:
                pages_text.append(page.get_text())

            full_text = clean_text('\n'.join(pages_text))
            file_id = get_file_hash(str(pdf_path))

            record = {
                "id": file_id,
                "filename": pdf_path.name,
                "state": state if state else "Unknown",
                "year": year if year else "Unknown",
                "page_count": len(doc),
                "full_text": full_text,
                "text_by_page": [clean_text(p) for p in pages_text]
            }

            records.append(record)
            doc.close()

        except Exception as e:
            print(f"  ERROR: {pdf_path.name} — {e}")
            errors.append({"filename": pdf_path.name, "error": str(e)})

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    if errors:
        with open(error_path, 'w', encoding='utf-8') as f:
            for err in errors:
                f.write(f"{err['filename']}: {err['error']}\n")
        print(f"\nCompleted with {len(errors)} error(s). See {error_path}.")
    else:
        print(f"\nCompleted successfully. {len(records)} documents indexed.")

    print(f"Output saved to {output_path}")

if __name__ == '__main__':
    process_pdfs(
        pdf_dir='.',
        output_path='output/index.json',
        error_path='output/errors.txt'
    )

import csv
import hashlib
import io
import random
import re
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"

ARCHIVE = ROOT / "data" / "seed_corpus" / "raw" / "uci_sms.zip"
OUTPUT = ROOT / "data" / "seed_corpus" / "staging" / "uci_ham_candidates.csv"

COLUMNS = [
    "id",
    "channel",
    "language",
    "text",
    "label",
    "family",
    "source",
]


def download_dataset():
    if ARCHIVE.exists():
        print("Using previously downloaded UCI archive.")
        return ARCHIVE.read_bytes()

    print("Downloading UCI SMS Spam Collection...")

    request = Request(
        URL,
        headers={"User-Agent": "CareShield-Educational-Research/1.0"},
    )

    with urlopen(request, timeout=45) as response:
        content = response.read(10000001)

    if len(content) > 10000000:
        raise ValueError("Unexpectedly large dataset download.")

    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_bytes(content)

    return content


def extract_messages(content):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = archive.namelist()

        for name in names:
            if Path(name).name.lower() == "smsspamcollection":
                return archive.read(name)

        for name in names:
            if name.lower().endswith(".zip"):
                return extract_messages(archive.read(name))

    raise ValueError("SMSSpamCollection file not found.")


def candidate_is_suitable(text):
    if not 30 <= len(text) <= 350:
        return False

    if not text.isascii():
        return False

    if len(re.findall(r"[A-Za-z]", text)) < 20:
        return False

    if re.search(r"https?://|www\.|@", text, re.IGNORECASE):
        return False

    return not re.search(r"(?:\d[\s().-]*){8,}", text)


def main():
    content = download_dataset()

    try:
        messages = extract_messages(content).decode("utf-8")
    except UnicodeDecodeError:
        messages = extract_messages(content).decode("latin-1")

    counts = {"ham": 0, "spam": 0}
    candidates = []
    seen = set()

    for line in messages.splitlines():
        label, separator, message = line.partition("\t")

        if not separator or label not in counts:
            continue

        counts[label] += 1

        if label != "ham":
            continue

        message = message.strip()
        key = " ".join(message.casefold().split())

        if key in seen or not candidate_is_suitable(message):
            continue

        seen.add(key)
        candidates.append(message)

    random.Random(2026).shuffle(candidates)

    if len(candidates) < 600:
        raise ValueError(
            f"Only {len(candidates)} candidates found; expected 600."
        )

    selected = candidates[:600]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()

        for message in selected:
            digest = hashlib.sha256(
                message.encode("utf-8")
            ).hexdigest()[:16]

            writer.writerow({
                "id": f"uci-{digest}",
                "channel": "sms",
                "language": "und",
                "text": message,
                "label": "legitimate",
                "family": "none",
                "source": "uci_sms_spam_collection",
            })

    print()
    print("UCI DATASET IMPORT REPORT")
    print("-------------------------")
    print(f"Original ham messages: {counts['ham']}")
    print(f"Original spam messages: {counts['spam']}")
    print(f"Unique candidates after filtering: {len(candidates)}")
    print(f"Candidates selected for review: {len(selected)}")
    print(f"Staging file: {OUTPUT}")
    print()
    print("IMPORTANT: These are provisional labels.")
    print("Review privacy, language, and labels before committing.")


if __name__ == "__main__":
    main()
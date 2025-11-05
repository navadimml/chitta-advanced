#!/usr/bin/env python3
"""Debug script to understand the stemming issue"""

def stem_hebrew(word: str) -> str:
    """Simple Hebrew stemming"""
    # Remove common prefixes
    for prefix in ['ה', 'ו', 'ב', 'כ', 'ל', 'מ', 'ש']:
        if word.startswith(prefix) and len(word) > len(prefix) + 1:
            word = word[len(prefix):]
            break

    # Remove common suffixes
    for suffix in ['ים', 'ות', 'ה']:
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            word = word[:-len(suffix)]
            break

    return word

# Test cases
test_words = [
    "הסירטונים",  # from failing test
    "הסרטונים",   # correct spelling
    "סרטון",       # keyword
    "נישמרים",     # from test
    "נשמר",        # keyword
    "שומרים",      # from test
    "שומר",        # keyword
]

print("Stemming results:")
print("-" * 60)
for word in test_words:
    stemmed = stem_hebrew(word)
    print(f"{word:20} -> {stemmed}")

print("\n" + "=" * 60)
print("Checking test case 1: 'מה לגבי הסירטונים, איפה הם נישמרים?'")
print("=" * 60)

text1 = "מה לגבי הסירטונים, איפה הם נישמרים?"
words1 = text1.split()
stemmed1 = [stem_hebrew(w) for w in words1]

print(f"Original words: {words1}")
print(f"Stemmed words: {stemmed1}")

# Check for keyword matches
keywords = ['סרטון', 'נשמר']
print(f"\nLooking for keywords: {keywords}")

for keyword in keywords:
    keyword_stemmed = stem_hebrew(keyword)
    print(f"\nKeyword: {keyword} (stemmed: {keyword_stemmed})")
    found = False
    for i, word in enumerate(stemmed1):
        if keyword_stemmed in word or word in keyword_stemmed:
            print(f"  ✓ Found in: {words1[i]} (stemmed: {word})")
            found = True
            break
    if not found:
        print(f"  ✗ Not found")

print("\n" + "=" * 60)
print("Checking test case 2: 'איפה הסרטונים שומרים?'")
print("=" * 60)

text2 = "איפה הסרטונים שומרים?"
words2 = text2.split()
stemmed2 = [stem_hebrew(w) for w in words2]

print(f"Original words: {words2}")
print(f"Stemmed words: {stemmed2}")

keywords2 = ['סרטון', 'שומר']
print(f"\nLooking for keywords: {keywords2}")

for keyword in keywords2:
    keyword_stemmed = stem_hebrew(keyword)
    print(f"\nKeyword: {keyword} (stemmed: {keyword_stemmed})")
    found = False
    for i, word in enumerate(stemmed2):
        if keyword_stemmed in word or word in keyword_stemmed:
            print(f"  ✓ Found in: {words2[i]} (stemmed: {word})")
            found = True
            break
    if not found:
        print(f"  ✗ Not found")

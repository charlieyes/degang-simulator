"""
Minimal English text processing module for GPT-SoVITS.
This is a stub implementation for basic English support.
"""

import re


def text_normalize(text):
    """Normalize English text."""
    # Basic normalization - remove extra spaces, normalize punctuation
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def g2p(text):
    """
    Convert English text to phonemes.
    This is a minimal implementation - for full English support,
    you would need a proper G2P model like espeak or CMUdict.
    """
    # For now, return a simple tokenization
    # Split by spaces and convert to uppercase
    words = text.upper().split()
    phones = []
    for word in words:
        # Simple character-based phoneme approximation
        # This is not accurate but prevents errors
        for char in word:
            if char.isalpha():
                phones.append(char)
            elif char in [',', '.', '!', '?']:
                phones.append(',')
        phones.append(' ')
    # Remove trailing space
    if phones and phones[-1] == ' ':
        phones.pop()
    return phones

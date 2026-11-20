"""Generate an age-style ten-word passphrase.

Word list: https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt
Replace this utility when https://github.com/FiloSottile/age/pull/726 ships.
"""

from pathlib import Path
import secrets


def generate_passphrase():
    words = Path(__file__).with_name("bip39-english.txt").read_text().split()
    if (
        len(words) != 2048
        or len(set(words)) != 2048
        or any(not word.isascii() or not word.islower() or not word.isalpha() for word in words)
    ):
        raise ValueError("Expected 2,048 unique lowercase words in the BIP39 word list.")
    return "-".join(secrets.choice(words) for _ in range(10))


if __name__ == "__main__":
    print(generate_passphrase())

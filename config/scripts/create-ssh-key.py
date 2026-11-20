"""Create an SSH key with a random passphrase saved in macOS Keychain."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

from generate_passphrase import generate_passphrase


def create_key(key_path, comment):
    public_key_path = Path(str(key_path) + ".pub")
    if os.path.lexists(key_path) or os.path.lexists(public_key_path):
        raise ValueError("Refusing to replace an existing SSH keypair.")

    passphrase = generate_passphrase()
    with tempfile.TemporaryDirectory(prefix="ssh-askpass-") as directory:
        askpass = Path(directory) / "askpass"
        askpass.write_text('#!/bin/sh\nprintf \'%s\\n\' "$SSH_KEY_PASSPHRASE"\n')
        askpass.chmod(0o700)
        environment = os.environ.copy()
        environment.update(
            SSH_ASKPASS=str(askpass),
            SSH_ASKPASS_REQUIRE="force",
            SSH_KEY_PASSPHRASE=passphrase,
            DISPLAY=environment.get("DISPLAY") or ":0",
        )
        subprocess.run(
            ["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-C", comment, "-f", str(key_path)],
            env=environment,
            stdin=subprocess.DEVNULL,
            check=True,
        )
        try:
            subprocess.run(
                ["/usr/bin/ssh-add", "-q", "--apple-use-keychain", str(key_path)],
                env=environment,
                stdin=subprocess.DEVNULL,
                check=True,
            )
            verification_environment = os.environ.copy()
            verification_environment.pop("SSH_KEY_PASSPHRASE", None)
            verification_environment.update(
                SSH_ASKPASS="/usr/bin/false",
                SSH_ASKPASS_REQUIRE="force",
                DISPLAY=environment["DISPLAY"],
            )
            subprocess.run(
                ["/usr/bin/ssh-add", "-q", "--apple-use-keychain", str(key_path)],
                env=verification_environment,
                stdin=subprocess.DEVNULL,
                check=True,
            )
        except BaseException:
            key_path.unlink(missing_ok=True)
            public_key_path.unlink(missing_ok=True)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("key_path", type=Path)
    parser.add_argument("--comment", required=True)
    arguments = parser.parse_args()
    try:
        create_key(arguments.key_path, arguments.comment)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"SSH key setup failed: {error}\n")
    except KeyboardInterrupt:
        parser.exit(130, "SSH key setup interrupted.\n")
    print("SSH key: generated; passphrase saved and verified in Keychain.")


if __name__ == "__main__":
    main()

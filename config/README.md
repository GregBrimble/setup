# Mac setup

Install Command Line Tools for Xcode (`xcode-select --install`), then:

```sh
curl -fsSL https://raw.githubusercontent.com/GregBrimble/setup/main/home/setup.sh -o /tmp/setup.sh
/bin/sh /tmp/setup.sh --adopt
```

Have your private-assets recovery passphrase ready. Complete account sign-ins
and macOS permission prompts when asked.

Rerun `~/setup.sh` to apply setup; add `--upgrade` to upgrade packages.
Edits save automatically. Publishing is manual:

```sh
mise dot sync  # Publish and fetch
mise dot pull  # Apply fetched changes
~/setup.sh
```

[Private assets and Tailwind Plus](tasks/private/README.md)

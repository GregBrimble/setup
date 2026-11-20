# Private assets

Keep the recovery passphrase in your password manager. Setup asks for it on a
new Mac. To recover a missing local identity: `mise run private:unlock`.

Edit `~/.local/share/private-assets/`; mise encrypts saved contents, but filenames
are public. Publish with `mise dot sync`.

For Tailwind Plus, set `email` and `password` in
`secrets/tailwind-plus.json`, then run:

```sh
mise run assets:tailwind-plus:update
```

Copy components from `~/.local/share/tailwind-plus/{ui-blocks,templates,ui-kit}`
into projects before editing.

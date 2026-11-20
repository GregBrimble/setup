# Homebrew CLI packages

Declare GitLab taps under `[bootstrap.brew.taps]` in `config.cloudflare.toml`,
then add packages under `[bootstrap.packages]`:

```toml
"brew-cli:cloudflare/engineering/example" = "latest"
```

Run `~/setup.sh`. Only `latest` is supported.

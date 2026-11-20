#!/bin/sh
set -eu

if ! mise_bin=$(command -v mise); then
	mise_bin="$HOME/.local/bin/mise"
	if [ ! -x "$mise_bin" ]; then
		installer=$(curl -fsSL https://mise.run)
		MISE_INSTALL_PATH="$mise_bin" /bin/sh -c "$installer"
	fi
fi
readonly mise_bin

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
export MISE_BIN="$mise_bin"
export MISE_AGE_KEY_FILE="$HOME/.local/share/mise/private-assets/identity.txt"

if [ "${1:-}" = --adopt ]; then
	shift
	recovery=$(mktemp -d)
	readonly recovery
	trap 'rm -rf "$recovery"' 0
	readonly base=https://raw.githubusercontent.com/GregBrimble/setup/main/config
	for file in private-identity.age private-recipient.txt; do
		curl -fsSL "$base/$file" -o "$recovery/$file"
	done
	curl -fsSL "$base/scripts/unlock-private.sh" -o "$recovery/unlock-private.sh"
	/bin/sh "$recovery/unlock-private.sh" "$recovery"
	"$mise_bin" bootstrap --adopt GregBrimble/setup --only files
	rm -rf "$recovery"
	trap - 0
fi

/bin/sh "$HOME/.config/mise/scripts/unlock-private.sh"
MISE_ENV=bootstrap "$mise_bin" vars prompt is_cloudflare
is_cloudflare=$(MISE_ENV=bootstrap "$mise_bin" vars is_cloudflare)
readonly is_cloudflare

case "$is_cloudflare" in
	true)
		MISE_ENV=bootstrap "$mise_bin" plugins link --force --quiet brew-cli "$HOME/.config/mise/plugins/brew-cli"
		export MISE_ENV=bootstrap,cloudflare
		;;
	false)
		export MISE_ENV=bootstrap
		;;
	*)
		echo "is_cloudflare must be true or false." >&2
		exit 1
		;;
esac

exec "$mise_bin" bootstrap --prompt-vars "$@"

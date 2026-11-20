#!/bin/sh
set -eu
umask 077

readonly recovery_dir="${1:-$HOME/.config/mise}"
readonly identity_dir="$HOME/.local/share/mise/private-assets"
readonly identity="$identity_dir/identity.txt"

age_exec() {
	if command -v "$1" >/dev/null 2>&1; then
		"$@"
	elif [ -x "/opt/homebrew/bin/$1" ]; then
		binary="/opt/homebrew/bin/$1"
		shift
		"$binary" "$@"
	else
		"${MISE_BIN:-mise}" exec age@latest -- "$@"
	fi
}

check_identity() {
	actual=$(age_exec age-keygen -y "$1") || return 1
	expected=$(cat "$recovery_dir/private-recipient.txt")
	if [ "$actual" != "$expected" ]; then
		echo "Private assets: identity does not match the recovery recipient." >&2
		return 1
	fi
}

if [ -e "$identity" ]; then
	[ ! -L "$identity" ] || { echo "Private assets: identity must not be a symlink." >&2; exit 1; }
	check_identity "$identity"
	chmod 0600 "$identity"
	exit 0
fi

mkdir -p "$identity_dir"
chmod 0700 "$identity_dir"
temporary=$(mktemp -d "$identity_dir/.identity.XXXXXX")
readonly temporary
trap 'rm -rf "$temporary"' 0
echo "Private assets: enter the recovery passphrase to unlock this Mac's age identity."
age_exec age --decrypt --output "$temporary/identity.txt" "$recovery_dir/private-identity.age"
check_identity "$temporary/identity.txt"
mv "$temporary/identity.txt" "$identity"
echo "Private assets: age identity ready."

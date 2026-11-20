#!/bin/sh
set -eu
umask 077

run_quietly() {
	if output=$("$@" 2>&1); then
		return 0
	else
		status=$?
		printf '%s\n' "$output" >&2
		return "$status"
	fi
}

readonly token="$1"
readonly label="$2"
readonly source="${3:-$HOME/.local/share/private-assets/casks/$token.rb}"
readonly tap=gregbrimble/private
readonly cask="$tap/$token"

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
mise run private:unlock

if [ ! -f "$source" ]; then
	printf '%s: cask file is missing: %s\n' "$label" "$source" >&2
	exit 1
fi

repository=$(brew --repository "$tap")
readonly repository
mkdir -p "$repository/Casks"
/usr/bin/install -m 0600 "$source" "$repository/Casks/$token.rb"
run_quietly brew trust --cask "$cask"

printf '%s: checking Homebrew installation...\n' "$label"
run_quietly brew install --cask --adopt "$cask"
printf '%s: ready.\n' "$label"

#!/bin/sh
set -eu

if [ "${1-}" = -Y ] && [ "${2-}" = sign ]; then
	public_key_file=
	previous=
	for argument do
		if [ "$previous" = -f ]; then
			public_key_file="$argument"
			break
		fi
		previous="$argument"
	done
	case "$public_key_file" in
		'~/'*) public_key_file="$HOME/${public_key_file#\~/}" ;;
	esac
	case "$public_key_file" in
		/*.pub)
			if ! /usr/bin/ssh-add -T "$public_key_file" >/dev/null 2>&1; then
				/usr/bin/ssh-add -q --apple-use-keychain "${public_key_file%.pub}"
			fi
			;;
	esac
fi
exec /usr/bin/ssh-keygen "$@"

#!/bin/sh
set -eu

if [ "${1-}" != --candidate ]; then
	if [ "$#" -ne 1 ]; then
		echo "Usage: cleanup-downloads.sh /absolute/path/to/Downloads" >&2
		exit 64
	fi
	case "$1" in
		/*) ;;
		*) echo "Downloads path must be absolute." >&2; exit 64 ;;
	esac
	if [ ! -d "$1" ] || [ -L "$1" ] || [ "$1" = / ]; then
		echo "Downloads path must be an existing directory, not a symlink or /." >&2
		exit 64
	fi

	exec /usr/bin/find -P "$1" -mindepth 1 -maxdepth 1 \
		! -name '.*' \( -type f -o -type d \) \
		-exec /bin/sh "$0" --candidate '{}' +
fi

shift
status=0
for candidate do
	# Include hidden descendants in the age check; never follow symlinks.
	if ineligible=$(/usr/bin/find -P "$candidate" \
		\( ! \( -type f -o -type d \) \
		-o ! -Btime +30d -o ! -mtime +30d -o ! -ctime +30d \
		-o -iname '*.download' -o -iname '*.crdownload' -o -iname '*.part' \) \
		-print -quit); then
		[ -z "$ineligible" ] || continue
	else
		printf 'Downloads cleanup: could not inspect %s; keeping it.\n' "$candidate" >&2
		status=1
		continue
	fi

	/usr/bin/trash --verbose "$candidate" || status=1
done
exit "$status"

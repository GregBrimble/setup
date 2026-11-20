#!/bin/sh
set -eu

export LC_ALL=C

/usr/sbin/system_profiler SPHardwareDataType | /usr/bin/awk -F ': ' '
	/Model Name:/ { model = $2 }
	/Chip:/ { chip = $2; sub(/^Apple /, "", chip) }
	END {
		if (model == "" || chip == "") {
			print "Could not determine Mac product and chip names." > "/dev/stderr"
			exit 1
		}
		printf "%s %s ", model, chip
	}
'
/bin/date +%Y

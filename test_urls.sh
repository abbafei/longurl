#!/bin/sh
for flags in '-f 0' '-a' '-f 0 -a' '-f 0 -a -p'; do
	printf 'Flags "%s"\n' "$flags"
	for url in 'plus.google.com/u/0/110933955439424623638/posts' 'www.opengroup.org/bookstore/catalog/c082.htm' 'gmail.com' 'fhwfw???.invaliddomainnamethisisone4testing'; do
		printf '\tURL "%s"\n' "$url"
		if [ "$flags" = '-f 0' ]; then
			(longurl "$url" $flags 2>&1 >/dev/null); printf '\t\tExit code %s\n' "$?"
		fi
		(longurl "$url" $flags) | while read line; do
			printf '\t\t'
			echo "$line"
		done
	done
done

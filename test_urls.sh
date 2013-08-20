#!/bin/sh
for flags in '-f 0' '-a' '-f 0 -a' '-f 0 -a -p'; do
	printf 'Flags "%s"\n' "$flags"
	# plus.google.com uses relative URL redirects currently.
	# opengroup URL redirects to empty string, which is a relative url meaning current url, therefore would loop forever
	# gmail is a regular URL which redirects a few times
	# fhwfw... is an invalid one since it uses invalid characters
	for url in 'plus.google.com/u/0/116899029375914044550/posts' 'www.opengroup.org/bookstore/catalog/c082.htm' 'gmail.com' 'fhwfw???.invaliddomainnamethisisone4testing'; do
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

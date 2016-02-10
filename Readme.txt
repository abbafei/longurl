B"H.

This utility follows HTTP redirects and tells you to where they go.


It can be used, for example to see where a short URL leads; hence the name "longurl".
It is similar to the Unix `readlink` command, but for URLs instead of files.

Backward-incompatible changes:
	2013/10/13 - changed "-f num" opt to "-f"


License: BSD




Usage: longurl <url> [-afhp] [-u user_agent] [-H http_header [-H http_header]...] [-r max_redirect_amount] [-n follow_amount] [-t timeout]

Resolves redirections for a URL.

INFO
Should always print one or more URLs (even if there was an error; in such a case a non-zero exit code should also be returned.).

If -h is provided, this message is displayed.

If -a is provided, list all the intermediate URIs which we are redirected through. Otherwise, just show the last.

If -n is provided, it should be the amount of redirects to follow, or 0 for all redirects.
If -f is provided, follow all redirects (equivalent to -n 0).
    Default is to follow only 1 redirect.
    Warning: following all redirects could loop infinitely when maximum redirect amount is also unlimited!

If -r is provided, it should be the maximum amount of redirects to follow, or 0 for unlimited (default 20). If this amount is
  exceeded without reaching a non-redirecting URI, a non-zero exit code is returned.

If -t is provided, it should be the amount of seconds to wait for a response from a server before continuing.

If -p is provided, it should show the original "raw" URI for each redirection (i.e. raw "Location"
  header value). If not, then the links which are (or would be) accessed to reach that URI are displayed.

If -u is provided, it should be a string to use for the "User-Agent" HTTP request header.

If -H is provided, it should be an HTTP header to add to the requests,
  for example "Cookie: yum". Use -H more than once to send more than one header.

EXIT CODES
Zero on success.
Non-zero on error; should return a code signifying what error occured...
 - 1: command line usage
 - 2: redirect loop. The last URL provided is the looping one (it was already previously accessed).
 - 3: unreachable server (timeout for example)
 - 4: invalid redirection. The page redirects to an invalid URI, or is not valid for a similar reason. If a valid
      URL is shown as the redirection target location, check if your internet connection is working.
 - 5: Too many redirects. The maximum redirect amount has been exceeded.

        

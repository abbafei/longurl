#!/usr/bin/env python2
import re
import urlparse
import httplib
import socket
import collections




class RedirectLoopError(Exception):
    pass

class UnreachableError(Exception):
    pass

class InvalidRedirectError(Exception):
    pass

class TooManyRedirects(Exception):
    pass



def url_parts(url, orig_url=None):
    p = urlparse.urlsplit(url)
    return dict(
        url2use = url,
        url = (url if (orig_url is None) else orig_url),
        scheme = p[0],
        server = p[1],
        page_location = urlparse.urlunsplit((('',)*2) + p[2:]),
    )


def url_fmt(input_url, format_url='', relative_url_format=True):
    if re.match(r'https?://', input_url):
        url = input_url
    else:
        url = (urlparse.urljoin(format_url, input_url) if relative_url_format else 'http://{url}'.format(url=input_url))
    return url
    

def location_header_from(server, page_location, scheme, url, timeout=None, http_headers=None, **kw):
    try:
        cer = (httplib.HTTPSConnection  if scheme.startswith('https') else httplib.HTTPConnection)
        c = (cer(server) if (timeout is None) else cer(server, timeout=timeout))
        try:
            c.request('GET', page_location, headers=({} if (http_headers is None) else http_headers))
            r = c.getresponse()
            o = (r.getheader('Location', None) 
                if (400 > r.status >= 300) else None
            )
            return o
        finally:
            c.close()
    except socket.timeout:
        raise UnreachableError
    except socket.gaierror:
        raise InvalidRedirectError


def di_redirs(url, timeout=None, http_headers=()):
    last_url = None
    while True:
        u = url_parts(url_fmt(url, format_url=last_url, relative_url_format=(False if (last_url is None) else True)), orig_url=url)
        yield u
        lh = location_header_from(timeout=timeout, http_headers=http_headers, **u)
        if lh is None:
            break
        last_url = url
        url = lh


def err_wraps(ii, exception):
    '''iterates over an iterable, checking for an error <exception>. returns a tuple with the iterator, and a callable which returns a boolean -- if an <exception> error is raised while iterating, the boolean is true, otherwise it is not.'''
    err = {None: None}
    _val = lambda: err[None]
    def _gen():
        try:
            for i in ii:
                yield i
        except exception:
            err[None] = True
    return (_gen(), _val)


def err_on_dups(ii, max_redirect, transform_fn=None):
    seen = collections.deque(maxlen=max_redirect)
    for i in ii:
        yield i
        tr = (transform_fn if (transform_fn is not None) else (lambda a: a))(i)
        if tr in seen:
            raise RedirectLoopError
        else:
            seen.append(tr)


def err_on_num(ii, max_redirect):
    redirect_num = 0
    for i in ii:
        redirect_num += 1
        if redirect_num > max_redirect:
            raise TooManyRedirects
        else:
            yield i






if __name__ == '__main__':
    import sys
    import collections
    import itertools
    import getopt
    import email

    get_optval = lambda params, n, default_val=None, to=(lambda val: val): (to(params[0][tuple(i[0] for i in params[0]).index(n)][1]) if (n in frozenset(i[0] for i in params[0])) else default_val)
    get_optlist = lambda params, n: tuple(i[1] for i in params[0] if (i[0] == n))
    get_optflag = lambda params, n: (n in frozenset(i[0] for i in params[0]))
    get_optparam = lambda params, i, default_val=None: (params[1][i] if (len(params[1]) > i) else default_val)

    max_redirect_default = 20 # firefox and chrome current default

    params = getopt.gnu_getopt(sys.argv[1:], 'afhH:r:n:t:pu:')
    resolve_all = get_optflag(params, '-f')
    timeout = get_optval(params, '-t', to=int)
    resolve_num = get_optval(params, '-n', 1, to=int)
    addl_headers = get_optlist(params, '-H')
    user_agent = get_optval(params, '-u', None)
    max_redirect = (get_optval(params, '-r', max_redirect_default, int) or None)
    list_all = get_optflag(params, '-a')
    do_help = get_optflag(params, '-h')
    show_raw = get_optflag(params, '-p')
    url = get_optparam(params, 0)

    if not (do_help or (url is None)):
        resolve_amt = (0 if resolve_all else resolve_num)
        http_headers_seq = (addl_headers + (() if (user_agent is None) else ('User-Agent: {0}'.format(user_agent),)))
        http_headers = dict(email.message_from_string('\r\n'.join(http_headers_seq)))
        urrs = err_wraps(di_redirs(url, timeout=timeout, http_headers=http_headers), UnreachableError)
        iurs = err_wraps(urrs[0], InvalidRedirectError)
        rlrs = err_wraps(err_on_dups(iurs[0], transform_fn=(lambda a: a['url2use']), max_redirect=max_redirect), RedirectLoopError)
        rnrs = err_wraps(err_on_num(rlrs[0], max_redirect=max_redirect), TooManyRedirects)
        sr = itertools.islice((i[('url' if show_raw else 'url2use')] for i in rnrs[0]), ((resolve_amt + 1) if (resolve_amt > 0) else None))
        so = (sr if list_all else collections.deque(sr, 1))
        for i in so:
            sys.stdout.write('{u}\n'.format(u=i))
        if rlrs[1]():
            exitcode = 2
        elif urrs[1]():
            exitcode = 3
        elif iurs[1]():
            exitcode = 4
        elif rnrs[1]():
            exitcode = 5
        else:
            exitcode = 0
        exit(exitcode)
    else:
        sys.stdout.write('''
Usage: {p} <url> [-afhp] [-u user_agent] [-H http_header [-H http_header]...] [-r max_redirect_amount] [-n follow_amount] [-t timeout]

Resolves redirections for a URL.

INFO
Should always print one or more URLs (even if there was an error; in such a case a non-zero exit code should also be returned.).

If -h is provided, this message is displayed.

If -a is provided, list all the intermediate URIs which we are redirected through. Otherwise, just show the last.

If -n is provided, it should be the amount of redirects to follow, or 0 for all redirects.
If -f is provided, follow all redirects (equivalent to -n 0).
    Default is to follow only 1 redirect.
    Warning: following all redirects could loop infinitely when maximum redirect amount is also unlimited!

If -r is provided, it should be the maximum amount of redirects to follow, or 0 for unlimited (default {max_redirect_default}). If this amount is
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

        \n'''.format(p=sys.argv[0], max_redirect_default=max_redirect_default))
        exit(1)

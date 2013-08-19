#!/usr/bin/env python2
import re
import urlparse
import httplib
import socket




class RedirectLoopError(Exception):
    pass

class UnreachableError(Exception):
    pass

class InvalidRedirectError(Exception):
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


def url_fmt(input_url, format_url=''):
    if re.match(r'https?://', input_url):
        url = input_url
    elif re.match(r'/', input_url):
        url = urlparse.urljoin(format_url, input_url)
    else:
        url = ''.join(('http://', input_url))
    return url
    

def location_header_from(server, page_location, scheme, url, timeout=None, **kw):
    try:
        cer = (httplib.HTTPSConnection  if scheme.startswith('https') else httplib.HTTPConnection)
        c = (cer(server) if (timeout is None) else cer(server, timeout=timeout))
        try:
            c.request('GET', page_location)
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


def di_redirs(url, timeout=None):
    last_url = None
    while True:
        u = url_parts(url_fmt(url, format_url=last_url), orig_url=url)
        yield u
        lh = location_header_from(timeout=timeout, **u)
        if lh is None:
            break
        last_url = url
        url = lh


def err_wraps(ii, exception):
    err = {None: None}
    _val = lambda: err[None]
    def _gen():
        try:
            for i in ii:
                yield i
        except exception:
            err[None] = True
    return (_gen(), _val)


def err_on_dups(ii, transform_fn=None):
    seen = set()
    for i in ii:
        yield i
        tr = (transform_fn if (transform_fn is not None) else (lambda a: a))(i)
        if tr in seen:
            raise RedirectLoopError
        else:
            seen.add((tr))





if __name__ == '__main__':
    import sys
    import collections
    import itertools
    import getopt

    get_optval = lambda params, n, default_val=None: (int(params[0][tuple(i[0] for i in params[0]).index(n)][1]) if (n in frozenset(i[0] for i in params[0])) else default_val)
    get_optflag = lambda params, n: (n in frozenset(i[0] for i in params[0]))
    get_optparam = lambda params, i, default_val=None: (params[1][i] if (len(params[1]) > i) else default_val)

    params = getopt.gnu_getopt(sys.argv[1:], 'af:t:p')
    resolve_amt = get_optval(params, '-f', 1)
    timeout = get_optval(params, '-t')
    list_all = get_optflag(params, '-a')
    show_raw = get_optflag(params, '-p')
    url = get_optparam(params, 0)

    if url is not None:
        urrs = err_wraps(di_redirs(url, timeout=timeout), UnreachableError)
        iurs = err_wraps(urrs[0], InvalidRedirectError)
        rlrs = err_wraps(err_on_dups(iurs[0], transform_fn=lambda a: a['url2use']), RedirectLoopError)
        sr = itertools.islice((i[('url' if show_raw else 'url2use')] for i in rlrs[0]), ((resolve_amt + 1) if (resolve_amt > 0) else None))
        so = (sr if list_all else collections.deque(sr, 1))
        for i in so:
            sys.stdout.write('{u}\n'.format(u=i))
        if rlrs[1]():
            exitcode = 2
        elif urrs[1]():
            exitcode = 3
        elif iurs[1]():
            exitcode = 4
        else:
            exitcode = 0
        exit(exitcode)
    else:
        sys.stdout.write('''
Usage: {p} <url> [-a] [-f num] [-t timeout]

Resolves redirections for a URL.

INFO
Should always print one or more URLs (even if there was an error; in such a case a non-zero exit code should also be returned.).

If -a is provided, list all URL which are redirected. Otherwise, just show the last.

If -f is provided, it should be the amount of redirects to follow, or 0 for all redirects (warning: this can go on forever!). 
    If not provided, default is to follow only 1 redirect.

If -t is provided, it should be the amount of seconds to wait for a response from a server before continuing.

If -p is provided, it should show the original "raw" data (i.e. original URI). If not, then the links which are (or would be) accessed are displayed.

EXIT CODES
Zero on success.
Non-zero on error; should return a code signifying what error occured...
 - 1: command line usage
 - 2: redirect loop. The last URL provided is the looping one (it was already previously accesses).
 - 3: unreachable server
 - 4: invalid redirection. The page redirects to an invalid URI, or similarly is not valid. If a valid URL is shown as the 
    redirection target location, check if your internet connection is working.

        \n'''.format(p=sys.argv[0]))
        exit(1)

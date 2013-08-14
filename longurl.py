#!/usr/bin/env python2
import re
import urlparse
import httplib
import socket




class RedirectLoopError(Exception):
    pass

class UnreachableError(Exception):
    pass



def url_parts(input_url):
    url = (input_url if re.match(r'https?://', input_url) else ''.join(('http://', input_url)))
    p = urlparse.urlsplit(url)
    return dict(
        url = input_url,
        url2use = url,
        scheme = p[0],
        server = p[1],
        page_location = urlparse.urlunsplit((('',)*2) + p[2:]),
    )


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
            op = (urlparse.urljoin(kw['url2use'], o) if ((o is not None) and o.startswith('/')) else o)
            return op
        finally:
            c.close()
    except socket.timeout:
        raise UnreachableError


def redirects_to_dest(url, timeout=None):
    u = url_parts(url)
    lh = location_header_from(timeout=timeout, **u)
    return (u['url'] if (lh is None) else redirects_to_dest(lh))


def di_redirs(url, timeout=None):
    while True:
        u = url_parts(url)
        yield u
        lh = location_header_from(timeout=timeout, **u)
        if lh is None:
            break
        url = lh


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

    get_optval = lambda params, n, default_value: (int(params[0][tuple(i[0] for i in params[0]).index(n)][1]) if (n in frozenset(i[0] for i in params[0])) else default_value)

    params = getopt.gnu_getopt(sys.argv[1:], 'af:t:')
    list_all = ('-a' in frozenset(i[0] for i in params[0]))
    resolve_amt = get_optval(params, '-f', 1)
    timeout = get_optval(params, '-t', None)
    url = (params[1][0] if (len(params[1]) > 0) else None)
    if url is not None:
        try:
            sr = itertools.islice((i['url'] for i in err_on_dups(di_redirs(url, timeout=timeout), transform_fn=lambda a: a['url2use'])), ((resolve_amt + 1) if (resolve_amt > 0) else None))
            so = (sr if list_all else collections.deque(sr, 1))
            for i in so: sys.stdout.write('{u}\n'.format(u=i))
        except RedirectLoopError:
            exit(2)
        except UnreachableError:
            exit(3)
    else:
        sys.stdout.write('''
Usage: {p} <url> [-a] [-f num] [-t timeout]

Resolves redirections for a URL.

INFO
Should always print one or more URLs (even if there was an error; in such a case a non-zero exit code should also be returned.).

If -a is provided, list all URL which are redirected. Otherwise, just show the last.

If -f is provided, it should be the amount of redirects to follow, or 0 for all redirects (warning: this can go on forever!). If not provided, default is to follow only 1 redirect.

If -t is provided, it should be the amount of seconds to wait for a response from a server before continuing.

EXIT CODES
Zero on success.
Non-zero on error; should return a code signifying what error occured...
 - 1: command line usage
 - 2: redirect loop. The last URL provided is the looping one (it was already previously accesses).
 - 3: unreachable server

        \n'''.format(p=sys.argv[0]))
        exit(1)

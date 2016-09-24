# graydns: 4/26/2012 2:57:31 PM
# get (and cache) a reasonable ip from an email address
# created to work with email addresses (no headers) with geoip
import os, sys, pickle, socket, atexit
import dns.resolver # dnspython.org

_cachefn = '.graydns_cache'
_cache = None # {'dns':'ip'}
_aliases = {
    # 'hostname_a':'hostname_b',
} 

def load_cache():
    print 'graydns: load'
    global _cache
    if os.path.isfile(_cachefn):
        f = open(_cachefn,'rb')
        _cache = pickle.load(f)
        assert type(_cache) == dict
    else:
        _cache = {}

def save_cache():
    print 'graydns: save'
    assert _cache != None
    f = open(_cachefn,'wb')
    pickle.dump(_cache, f)

def verify_cache():
    if _cache==None:
        load_cache()
    assert type(_cache) == dict
    
def get_ip(host):    
    host = host.lower()
    host = _aliases.get(host, host)    
    verify_cache()
    ip = _cache.get(host)
    if ip==None:
        ip = _lookup_ip(host)
        _cache[host] = ip
    return ip

def is_addr(s):
    if s.count('.')!=3:
        return False    
    result = False
    for octet in s.split('.'):
        try:
            i = int(octet)
        except ValueError:
            return False
    return True
assert is_addr('123.123.123.123')
assert not is_addr('123.123.x.123')

def is_host(s):
    return not is_addr(s)
assert is_host('dbyrne')
assert is_host('foo.bar')

def require_host(s):
    if not is_host(s):
        raise Exception('host required, this seems to be an ip: ' + s)

def require_ip(s):
    if not is_addr(s):
        raise Exception('ip addr required, this seems to be something else: ' + s)

def _get_ip(host):
    answers = dns.resolver.query(host, 'a')
    ip = answers[0].address
    require_ip(ip)
    #socketaddr = socket.gethostbyname(host)       
    #if ip != socketaddr:        
    #    msg = 'sanity anomaly for {0}: {1}, {2}'.format(host, ip, socketaddr) # load balanced, etc
    #    #raise Exception(msg)
    #    print msg
    return ip

# gray ip lookup, mx first, then prepend www.        
def _lookup_ip(host):
    print 'graydns: lookup'
    require_host(host)
    
    # http://en.wikipedia.org/wiki/List_of_DNS_record_types
    # a, mx | ns, soa, txt
    try:
        ip = _get_ip(host)
    except dns.resolver.NoAnswer:            
        try:
            answers = dns.resolver.query(host, 'mx')
            mxhost = answers[0].exchange.to_text()
            require_host(mxhost)
            ip = _get_ip(mxhost)
            print 'graydns: resorted to mx record for: {0}, being: {1}'.format(host, mxhost)
        except dns.resolver.NoAnswer:
            prefix = 'www.'
            if host.lower().startswith(prefix):
                pass
            else:                
                webhost = prefix + host
                ip = _lookup_ip(webhost)
                print 'graydns: resorted to www prefix for: {0}, being: {1}'.format(host, webhost)
            raise Exception('unable to find reasonable ip for host: ' + host)

    if ip.count('.') != 3:
        raise Exception('unexpected ip format: ' + ip)

    return ip
    
atexit.register(save_cache)    

if __name__=='__main__':
    print get_ip('google.com')
    print get_ip('amazon.com')
    print get_ip('nasa.gov')

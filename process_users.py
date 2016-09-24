import dns.resolver, dns.exception
import os

root = r'D:\usr\home\nkjesk\misc\users\\'

skip = (
    'proimageguide.com',
    'conceptthru.com',
    'justbackpack.com',
    'mhsamedia.com',
    'infomercial.tv',
    'tlcollective.com.au',
    'svtspace.com',
    'eylexis.com',
    'axialpraxis.com',
    'solunix.dnsalias.com',
    'bowsitemail.com',
    'intrapeople.com',
    'sparkleroad.com',
    'citymediastudios.com',
    'antiek-on-line.nl',
    'olympus.uk.com',
    'equinemail.net','easyproducts.co.uk','directplacement.com','fforesite.com.au','phil.com.fr','keystonestudio.co.uk','holiday-sd.com','emerald.fiserv.com','amercom.be','fleer.com','free2serve.com','nusensio.com','jonesinfo.com','neteffects.co.uk','bigsplashlittlepond.com','vandip.com','ezoutdoorsys.com','opusdeidesign.com','simple-cms.com','communicoserver.com','instasave.com','antidote909.com','frozen-pond.com','agilewebware.com','sad22.com','houseofsales.dk','peractoconsulting.com','lighthousedigital.co.uk','tahitipresse.pf','gombala.com','skoogle.com','blueridgewebservices.com','losc.patrick.af.mil','sjfusion.com','tcustomsys.com','wisevillage.com','thegapcompany.com','nuclear.inin.mx','networks-cs.com','northstarpei.com','webrefined.com','netadmin.ltd.uk','geist-enterprises.com',
)    

# [(domain, count)..]
def get_domains():
    domains = {}
    for fn in os.listdir(root):
        if fn.startswith('_'):
            continue
        domain = fn.split('@')[-1]        
        if domain in skip:
            continue
        count = domains.setdefault(domain, 0)
        domains[domain] = count + 1
    return domains

if __name__=='__main__':
    
    domains = get_domains()
    
    from graydns import get_ip
    
    errorfn = '_bad_domains.txt'
    
    with open(errorfn, 'wc') as errorf:
    
        for domain,count in domains.items():
    
            print 'getting ip for domain...', domain
    
            try:
                bad = False
                get_ip(domain)
            except dns.resolver.NXDOMAIN:
                bad = True            
            except dns.exception.Timeout:
                bad = True
                
            if bad:
                errorf.write(domain+'\r\n')
                errorf.flush()
                print 'bad domain logged'
    
    print 'domain count:', len(domains)
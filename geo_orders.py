# http://en.wikipedia.org/wiki/Robinson_Projection
# http://terraetl.blogspot.com/2007/10/robinson-projection-not-shaped-like-egg.html
# http://www.flashmap.org/robinson-projection-in-as3-gpl/
# todo: move origin to middle not middle left?
from __future__ import division
import pygeoip
from pygeoip import GeoIP
from pprint import pprint

_test = True

#gi = GeoIP(r'c:\3rd\geoip\GeoLiteCity.dat', pygeoip.MEMORY_CACHE)
# blah, some of these won't resolve anymore... and not just those that are dead
# '66.41.28.121' -> mpls

# (all normalized) latitude, parallel length, parallel distance from equator
table = [
    (00/90, 1.0000, 0.0000),
    (05/90, 0.9986, 0.0620),
    (10/90, 0.9954, 0.1240),
    (15/90, 0.9900, 0.1860),
    (20/90, 0.9822, 0.2480),
    (25/90, 0.9730, 0.3100),
    (30/90, 0.9600, 0.3720),
    (35/90, 0.9427, 0.4340),
    (40/90, 0.9216, 0.4958),
    (45/90, 0.8962, 0.5571),
    (50/90, 0.8679, 0.6176),
    (55/90, 0.8350, 0.6769),
    (60/90, 0.7986, 0.7346),
    (65/90, 0.7597, 0.7903),
    (70/90, 0.7186, 0.8435),
    (75/90, 0.6732, 0.8936),
    (80/90, 0.6213, 0.9394),
    (85/90, 0.5722, 0.9761),
    (90/90, 0.5322, 1.0000),
]
table.reverse()

def lerp(x1, x2, p):
    return x1 + ( x2 - x1 ) * p
if _test:
    assert lerp(10,20,0.5) == 15
    assert lerp(10,20,0.2) == 12
    assert lerp(12,24,0.75) == 21

def get_plen_pdfe(latitude):
    latitude = abs(latitude)
    if latitude > 1:
        latitude = 1 #raise Exception('expected latitude <= 1, got: ' + str(latitude))
    for i, row in enumerate(table):
        deg1, plen1, pdfe1 = row
        if latitude >= deg1:
            deg2, plen2, pdfe2 = table[i-1]
            p = (latitude-deg1)/(deg2-deg1)
            plen = lerp(plen1, plen2, p)
            pdfe = lerp(pdfe1, pdfe2, p)
            return plen, pdfe

# (input and outputs normalized [0..1])
# get robinson projection x, y
# origin is middle left, for now
def get_robinson_coord(longitude, latitude):
    assert longitude <= 1
    assert latitude <= 1
    plen, pdfe = get_plen_pdfe(latitude)
    
    long_start = (1 - plen) / 2
    x = long_start + longitude * plen
    y = pdfe
    if latitude<0:
        y *= -1

    return x, y

if _test:
    _test_dict = {}
    for deg, plen, pdfe in table:
        _test_dict[deg] = (plen, pdfe)
    for test_lat in range(0,95,5):
        lat = test_lat/90
        plen, pdfe = get_plen_pdfe(lat)
        #print test_lat, _test_dict[test_lat]
        assert _test_dict[lat] == (plen, pdfe)
    assert get_plen_pdfe(7.5/90) == (0.997, 0.093)

    assert get_robinson_coord(0.5, 0) == (0.5, 0)
    assert get_robinson_coord(0.5, 1) == (0.5, 1)
    assert get_robinson_coord(0.5, 1) == (0.5, 1)

    assert get_robinson_coord(0.25, 1) == ((1-0.5322)/2 + (0.5322*.25), 1)
    assert get_robinson_coord(0.75, 1) == ((1-0.5322)/2 + (0.5322*.75), 1)

# Best guess for Greenwich Coordinates is 51.4788 N, 0.0106 W
# [MIA] lat 25.82 lon -80.28 Miami Intl

# what is wikipedia offset? maybe 18 degrees? guess from 162e example
#
# the biercenator script should tell me
#
# WorldBase.py
#         self.greenwich = 1269.7627342
#
# BlankMap-World6.svg
#   viewBox="0 0 2752.766 1537.631"
#   version="1.0"
#   height="476.7276"
#   width="939.74725"
#
# >>> 0.5 - 1269.7627342 / 2752.766
# 0.03873204834700805
# this is about 7 degrees
# 
# http://en.wikipedia.org/wiki/Prime_Meridian
# match it up visually i guess, try this number first

    greenwich = [0.0106, 51.4788]
    miami = [-80.28, 25.82]
    
    lonlat = greenwich
    lonlat = miami
    
    # input normalized, output in map space
    def get_map_coord(lonlat):
        maprotate = -7
        lonlat[0] = (lonlat[0] + 180 + maprotate)/360
        lonlat[0] = lonlat[0] % 1
        lonlat[1] = lonlat[1]/180
    
        rx, ry = get_robinson_coord(*lonlat)
        #print rx, ry
        
        # bitmap coord
        mapoffset = 4 # map border
        width = 800 - mapoffset * 2
        height = 411 - mapoffset * 2
        x = rx * (width)
        y = (height/2) - ry*height
    
        x += mapoffset
        y += mapoffset
        
        return x, y

    print get_map_coord(miami)
    
if __name__=='__main__':
    pass
    #pprint( gi.record_by_name('www.nasa.gov') )
    #pprint( gi.record_by_addr('66.41.28.121') )
    #name = 'dogbytes.ch'
    #pprint( gi.record_by_name(name) )

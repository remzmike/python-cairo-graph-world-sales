# wish: separate or combine things whose origins are within diameter*.3 of each other
from __future__ import division
import math, sys, os
import cairo
import shpUtils
import pygeoip
from pygeoip import GeoIP
from pprint import pprint
import process_users, graydns

_MULTIPLY = 14
_SCREEN = 15
_OVERLAY = 16
_DARKEN = 17
_LIGHTEN = 18
_COLOR_DODGE = 19
_COLOR_BURN = 20
_HARD_LIGHT = 21
_SOFT_LIGHT = 22
_DIFFERENCE = 23
_EXCLUSION = 24
_HSL_HUE = 25
_HSL_SATURATION = 26
_HSL_COLOR = 27
_HSL_LUMINOSITY = 28

shpRecords = shpUtils.loadShapefile('data\TM_WORLD_BORDERS_SIMPL-0.3.shp')
gi = GeoIP(r'GeoLiteCity.dat', pygeoip.MEMORY_CACHE)

gscale = 3

img = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(360*gscale), int(180*gscale))
cr = cairo.Context(img)
cr.set_line_join(cairo.LINE_JOIN_BEVEL)
cr.scale(gscale,gscale)

cr.set_source_rgb(0.2,0.2,0.2)
cr.paint()

from geo_orders import get_robinson_coord

# [0..360], [-90..90]
def xform(point, do_robinson=True):
    x = point[0]/360 + 0.5
    y = point[1]/90
    if do_robinson:
        x, y = get_robinson_coord(x, y)
    result = [
        x * 360,
        180 - ( y * 90 + 90 )
    ]
    return result

def draw_countries(cr, fillcolor=(0.3,0.3,0.3,0.5), fillcolors={}):    
    for thing in shpRecords['features']:
        #break # nolive
        for part in thing['shape']['parts']:        
            points = part['points']
            assert len(points)>1
            for point in points:
                absx = abs(point[0])
                absy = abs(point[1])
                if 180 < absx < 181:
                    point[0] = round(point[0], 5) # meh, some data comes in slightly over 180
                    absx = abs(point[0])
                if not absx <= 180:
                    raise Exception('expected x <= 180, got ' + str(absx))
                    #print 'exceptional x value', repr(point)
                if not absy <= 90:
                    raise Exception('expected y <= 90, got ' + str(absy))
            
            start = xform(points[0])
            
            cr.move_to(*start)
            #print 'move to', start
            for point in points[1:]:
                xfpoint = xform(point)
                cr.line_to(*xfpoint)
                #print 'line to', point
            countrykey = thing['info']['ISO2']
            countrycolor = fillcolors.get(countrykey, fillcolor)

            cr.save()

            cr.set_source_rgba(*countrycolor)
            cr.fill_preserve()

            if fillcolors.has_key(countrykey):
                #cr.set_dash([],0)
                cr.set_source_rgba(1,1,1,0.2)
                cr.set_line_width(2)
            else:
                #cr.set_dash([1],0)                
                cr.set_source_rgba(0.5,0.5,0.5,0.2)
                cr.set_line_width(0.5)
            cr.clip_preserve()
            cr.stroke()    

            cr.restore()        

# returns (iso2, lon, lat)
def get_geo_by_ip(ip):
    record = gi.record_by_addr(ip)
    if record==None:
        return get_geo_by_ip('71.204.5.49') # for now, use me as null
    return record['country_code'], record['longitude'], record['latitude']

domains = process_users.get_domains()

country_values = {}
country_value_max = 0

for domain, count in domains.items():
    ip = graydns.get_ip(domain)
    iso2, lon, lat = get_geo_by_ip(ip)
    country_values[iso2] = country_values.setdefault(iso2, 0) + 1
    country_value_max = max(country_value_max, country_values[iso2])
    
fillcolors = {}
for country, value in country_values.items():
    mx = country_value_max
    #value = mx/4 + value/mx/4
    mx = math.sqrt(math.sqrt(country_value_max))
    value = math.sqrt(math.sqrt(value))
    
    red = 1 - (1-value/mx)*0.5
    fillcolors[country] = (red/1.6, 0.2, red, 1)

draw_countries(cr, fillcolors=fillcolors)

# robinson lines
quadrants = [(1,1),(1,-1),(-1,1),(-1,-1)]

for qx, qy in quadrants:
    cr.save()
    cr.scale(qx,qy)    
    cr.translate(
        0 if qx==1 else -360,
        0 if qy==1 else -180
    )
    cr.set_line_width(1)
    cr.set_source_rgba(0.3,0.3,0.3,0.5)
    move = True
    for i in range(90+1):
        nx = 0
        ny = (90 - i)/90
        #x, y = xform([nx, ny])
        #print x, y
        x, y = get_robinson_coord(nx, ny)
        x = x*360
        y = 180 - (y*90 + 90)
        if move:
            cr.move_to(x,y)
            move = False
        else:
            cr.line_to(x, y)
    cr.stroke()
    cr.restore()

# todo: top, bottom, left, right
# 0,1 to 1,1
# 0,-1 to 1,-1
# 

greenwich = [0.0106, 51.4788, 1]
miami = [-80.28, 25.82, 1]
homexy = get_geo_by_ip('71.204.5.49')[1:]
home = [homexy[0], homexy[1], 1]

spots = [] # [ [0,0,1], miami, greenwich, home ]
for domain, count in domains.items():
    ip = graydns.get_ip(domain)
    iso2, lon, lat = get_geo_by_ip(ip)
    spots.append([lon, lat, count, iso2])

# order spots biggest first, smallest last
spots = sorted(spots, key=lambda x: x[2])
spots.reverse()

#cr.set_operator(2)
cr.set_source_rgba(1,1,1,1)
cr.set_line_width(1)
for x, y, count, iso2 in spots:
    x, y = xform([x,y])    
    size = math.sqrt(count)
    cr.arc(x, y, size, 0, 2*math.pi)
    cr.stroke()
#cr.set_operator(2)

#cr.set_operator(2) #_SOFT_LIGHT) # 19 no border
for x, y, count, iso2 in spots:
    x, y = xform([x,y])    
    #if size>1:
    #    print size
    size = math.sqrt(count)

    # another border...
    #cr.set_operator(_SOFT_LIGHT)
    #cr.set_operator(_SCREEN)
    #cr.arc(x, y, size, 0, 2*math.pi)
    #cr.set_line_width(size)
    #cr.set_source_rgba(1,1,1,0.2)
    #cr.stroke()
    #cr.set_operator(2)
    
    spotcolor = fillcolors[iso2] # 0.3,0.6,1,0.75
    use_grad = True
    if use_grad:
        #grad = cairo.RadialGradient(x-size/2, y-size/2, size/4, x, y, size)
        grad = cairo.RadialGradient(x-size/2, y-size/2, size/4, x, y, size)
        r, g, b, a = spotcolor
        grad.add_color_stop_rgba(0, min(1,r*1.4), min(1, g*1.2), min(1, b*1.3), 1)    
        if size>2:
            grad.add_color_stop_rgba(0.8, r, g, b, 1)
            grad.add_color_stop_rgba(1, r/1.4, g/1.2, b/1.3, 1)        
        else:            
            grad.add_color_stop_rgba(1, r, g, b, 1)
        cr.set_source(grad)
    else:
        cr.set_source_rgba(*spotcolor)
    cr.arc(x, y, size, 0, 2*math.pi)
    cr.fill()

fn = 'test.png'
img.write_to_png(fn)

os.system(fn)

#>>> pprint( shpRecords['features'][0] )
#{'info': {'AREA': 44,
#          'FIPS': 'AC',
#          'ISO2': 'AG',
#          'ISO3': 'ATG',
#          'LAT': Decimal('17.078'),
#          'LON': Decimal('-61.783'),
#          'NAME': 'Antigua and Barbuda',
#          'POP2005': 83039,
#          'REGION': 19,
#          'SUBREGION': 29,
#          'UN': 28},
# 'shape': {'bounds': [[-61.88722200000001, 17.024441000000152],
#                      [-61.686668000000026, 17.703888000000077]],
#           'parts': [{'area': 0.009571241466346692,
#                      'bounds': [[-61.88722200000001, 17.024441000000152],
#                                 [-61.686668000000026, 17.1633300000001]],
#                      'center': [-61.78694500000002, 17.093885500000127],
#                      'centroid': [-61.789446333680445, 17.097681666762263],
#                      'extent': [0.20055399999998258, 0.1388889999999492],
#                      'points': [[-61.686668000000026, 17.024441000000152],
#                                 [-61.88722200000001, 17.105273999999966],
#                                 [-61.79444899999993, 17.1633300000001],
#                                 [-61.686668000000026, 17.024441000000152]]},
#                     {'area': 0.007740411570125616,
#                      'bounds': [[-61.873062000000004, 17.583054000000104],
#                                 [-61.72917199999989, 17.703888000000077]],
#                      'center': [-61.80111699999995, 17.64347100000009],
#                      'centroid': [-61.818430666342444, 17.631849999907256],
#                      'extent': [0.14389000000011265, 0.12083399999997368],
#                      'points': [[-61.72917199999989, 17.608608000000046],
#                                 [-61.853057999999976, 17.583054000000104],
#                                 [-61.873062000000004, 17.703888000000077],
#                                 [-61.72917199999989, 17.608608000000046]]}],
#           'type': 5}}
#>>>
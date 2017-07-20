import pygame, math, sys
from pygame.locals import *
from PIL import Image
from collections import deque

WIDTH          = 640
HEIGHT         = 200
DEG_PER_CIRCLE = 360
DEG_TO_RAD     = math.pi*2/DEG_PER_CIRCLE
UMAX           = 0.436
VMAX           = 0.615

ntscRGB   = [[(0, 0, 0) for y in xrange(4)] for p in xrange(32)]
ntscOutput = []

def yuv2rgb(y, u, v):
    u *= UMAX
    v *= VMAX
    r = max(0.0, y + 1.14  * v)
    g = max(0.0, y - 0.395 * u - 0.581 * v)
    b = max(0.0, y + 2.033 * u)
    return r, g, b

def luv2rgb(y, u, v):
    r = max(0.0, y + v)
    g = max(0.0, y - 0.707 * u - 0.707 * v)
    b = max(0.0, y + u)
    return r, g, b

def ntscInitRGB(angle):
    YScale = [0.0, 0.25, 0.50, 1.0]#[0.0, 0.3333, 0.6667, 1.0]
    redSum = 0.0
    grnSum = 0.0
    bluSum = 0.0
    rgb    = []
    for pix in xrange(32):
        #
        # U, V for this chroma angle
        #
        u = math.cos(angle * DEG_TO_RAD)
        v = math.sin(angle * DEG_TO_RAD)
        #
        # Calculate and NTSC RGB for this SHR pixel
        #
        red, grn, blu = luv2rgb(1.0, u, v)
        redSum += red
        grnSum += grn
        bluSum += blu
        rgb.append((red, grn, blu))
        #
        # Next NTSC chroma pixel
        #
        angle = angle - 78.75
        if angle > 360.0:
            angle -= 360.0
        if angle < 0.0:
            angle += 360.0
    #
    # Normalize the RGB values of each NTSC pixel component so they add up to white
    #
    redScale = 255.0 * 7.0 / redSum
    grnScale = 255.0 * 7.0 / grnSum
    bluScale = 255.0 * 7.0 / bluSum
    for lum in xrange(4):
        for pix in xrange(len(rgb)):
            ntscRGB[pix][lum] = (min(255,int(rgb[pix][0]*redScale*YScale[lum])), min(255,int(rgb[pix][1]*grnScale*YScale[lum])), min(255,int(rgb[pix][2]*bluScale*YScale[lum])))

def ntscInitPrev():
    global ntscOutput
    ntscOutput = deque([(128, 128, 128) for p in xrange(4)])

def ntscPrev():
    #
    # Return previous NTSC chroma cycle output
    #
    l = len(ntscOutput)
    red = ntscOutput[0][0] * 0.57
    grn = ntscOutput[0][1] * 0.57
    blu = ntscOutput[0][2] * 0.57
    for p in xrange(1, l):
        red += ntscOutput[p][0]
        grn += ntscOutput[p][1]
        blu += ntscOutput[p][2]
    return (min(255,red), min(255,grn), min(255,blu))
     
def ntscBest(ntsc, rgb):
    nearest = 195075
    lumBest = 0
    for lum in xrange(4):
        red = rgb[0] - ntsc[lum][0]
        grn = rgb[1] - ntsc[lum][1]
        blu = rgb[2] - ntsc[lum][2]
        dist = red*red + grn*grn + blu*blu
        if dist < nearest:
            nearest = dist
            lumBest = lum
    #
    # Update ouput list
    #
    ntscOutput.popleft()
    ntscOutput.append(ntsc[lumBest])
    return lumBest

def ntscMapRGB(rgb):
    shr = []
    for p in xrange(len(rgb)):
        prev = ntscPrev()
        red = max(0, rgb[p][0] - prev[0])
        grn = max(0, rgb[p][1] - prev[1])
        blu = max(0, rgb[p][2] - prev[2])
        shr.append(ntscBest(ntscRGB[p], (red, grn, blu)))
    return shr
    
def displayBars():
    for l in xrange(4):
        for bar in xrange(len(ntscRGB)):
            surface.fill(ntscRGB[bar][l], pygame.Rect(bar * 20, l * 50, 20, 50))
    pygame.display.flip()

if len(sys.argv) > 1:
    imagefile = sys.argv[1]
else:
    imagefile = "image.jpg"
image = Image.open(imagefile)
if image.size[0] <> WIDTH or image.size[1] <> HEIGHT:
    image = image.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
pygame.init()
surface = pygame.display.set_mode((WIDTH,HEIGHT))
surfpix = pygame.PixelArray(surface)
ntscInitRGB(103.0)
ntscInitPrev()
displayBars()
for y in xrange(HEIGHT):
    print '; scanline: ', y
    for x in xrange(0, WIDTH, len(ntscRGB)):
        rgb = []
        for p in xrange(len(ntscRGB)):
            rgb.append(image.getpixel((x + p, y)))
        shr = ntscMapRGB(rgb)
        #
        # Copy displayable SHR pixels
        #
        for p in xrange(len(shr)):
            surfpix[p + x][y] = (ntscRGB[p][shr[p]][0], ntscRGB[p][shr[p]][1], ntscRGB[p][shr[p]][2])
        #
        # Output SHR pixels for assembly
        #
        print '\t!BYTE\t$%02X, ' % ((shr[0]  << 6) | (shr[1]  << 4) | (shr[2]  << 2) | shr[3]),
        print '$%02X, '          % ((shr[4]  << 6) | (shr[5]  << 4) | (shr[6]  << 2) | shr[7]),
        print '$%02X, '          % ((shr[8]  << 6) | (shr[9]  << 4) | (shr[10] << 2) | shr[11]),
        print '$%02X, '          % ((shr[12] << 6) | (shr[13] << 4) | (shr[14] << 2) | shr[15]),
        print '$%02X, '          % ((shr[16] << 6) | (shr[17] << 4) | (shr[18] << 2) | shr[19]),
        print '$%02X, '          % ((shr[20] << 6) | (shr[21] << 4) | (shr[22] << 2) | shr[23]),
        print '$%02X, '          % ((shr[24] << 6) | (shr[25] << 4) | (shr[26] << 2) | shr[27]),
        print '$%02X'            % ((shr[28] << 6) | (shr[29] << 4) | (shr[30] << 2) | shr[31])
    pygame.display.flip()

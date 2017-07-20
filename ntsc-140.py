import pygame, math, sys
from pygame.locals import *
from PIL import Image

WIDTH          = 140
HEIGHT         = 200
DEG_PER_CIRCLE = 360
DEG_TO_RAD     = math.pi*2/DEG_PER_CIRCLE
UMAX           = 0.436
VMAX           = 0.615

ntscRGB   = [[(0, 0, 0) for y in xrange(4)] for p in xrange(32)]
ntscPixel = [[(0, 0, 0)] for m in xrange(7)]
ntscRange = [0, 4, 9, 13, 18, 23, 27]
shrPixels = []
ntscOutput = []

def yuv2rgb(y, u, v):
    u *= UMAX
    v *= VMAX
    r = max(0.0, y + 1.14  * v)
    g = max(0.0, y - 0.395 * u - 0.581 * v)
    b = max(0.0, y + 2.033 * u)
    return (r, g, b)

def luv2rgb(y, u, v):
    r = max(0.0, y + v)
    g = max(0.0, y - 0.707 * u - 0.707 * v)
    b = max(0.0, y + u)
    return (r, g, b)
    
def ntscInitRGB(angle):
    YScale = [0.0, 0.25, 0.50, 1.0]#[0.0, 0.3334, 0.6667, 1.0]
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

def lumInc(seq):
    s = 0
    seq[s] += 1
    while seq[s] == 4:
        seq[s] = 0
        s += 1
        if s == len(seq):
            return False
        seq[s] += 1
    return True

def ntscInitPixels():
    #
    # NTSC pixel mapping to SHR range
    #
    for pix7 in xrange(7):
        shrpix = [0 for p in xrange(5)]
        while lumInc(shrpix):
            red = 0
            grn = 0
            blu = 0
            for s in xrange(len(shrpix)):
                red += ntscRGB[ntscRange[pix7]+s][shrpix[s]][0]
                grn += ntscRGB[ntscRange[pix7]+s][shrpix[s]][1]
                blu += ntscRGB[ntscRange[pix7]+s][shrpix[s]][2]
            ntscPixel[pix7].append((min(255,int(red * 0.914)), min(255,int(grn * 0.914)), min(255,int(blu * 0.914)))) # 0.914 = 5 / 4.57

def ntscMapRGB(rgb, x):
    global shrPixels
    
    nearest = 195075
    nBest  = 0
    errRed = 0
    errGrn = 0
    errBlu = 0
    pix7 = x % 7
    if pix7 == 0:
        shrPixels = [0 for n in xrange(32)]
    #
    # Look for best RGB match
    #
    redMatch = rgb[0]
    grnMatch = rgb[1]
    bluMatch = rgb[2]
    for n in xrange(len(ntscPixel[pix7])):
        red = redMatch - ntscPixel[pix7][n][0]
        grn = grnMatch - ntscPixel[pix7][n][1]
        blu = bluMatch - ntscPixel[pix7][n][2]
        dist = red*red + grn*grn + blu*blu
        if dist < nearest:
            nearest = dist
            nBest   = n
            errRed = red
            errGrn = grn
            errBlu = blu
    rgbBest = ntscPixel[pix7][nBest]
    #
    # Convert to SHR pixels
    #
    for n in xrange(5):
        shrPixels[ntscRange[pix7] + n] = nBest & 0x03
        nBest >>= 2
    #
    # Output SHR pixels for assembly
    #
    if pix7 == 6:
        print '\t!BYTE\t$%02X, ' % ((shrPixels[0]  << 6) | (shrPixels[1]  << 4) | (shrPixels[2]  << 2) | shrPixels[3]),
        print '$%02X, '          % ((shrPixels[4]  << 6) | (shrPixels[5]  << 4) | (shrPixels[6]  << 2) | shrPixels[7]),
        print '$%02X, '          % ((shrPixels[8]  << 6) | (shrPixels[9]  << 4) | (shrPixels[10] << 2) | shrPixels[11]),
        print '$%02X, '          % ((shrPixels[12] << 6) | (shrPixels[13] << 4) | (shrPixels[14] << 2) | shrPixels[15]),
        print '$%02X, '          % ((shrPixels[16] << 6) | (shrPixels[17] << 4) | (shrPixels[18] << 2) | shrPixels[19]),
        print '$%02X, '          % ((shrPixels[20] << 6) | (shrPixels[21] << 4) | (shrPixels[22] << 2) | shrPixels[23]),
        print '$%02X, '          % ((shrPixels[24] << 6) | (shrPixels[25] << 4) | (shrPixels[26] << 2) | shrPixels[27]),
        print '$%02X'            % ((shrPixels[28] << 6) | (shrPixels[29] << 4) | (shrPixels[30] << 2) | shrPixels[31])
    return rgbBest

def displayBars():
    for bar in xrange(32):
        for lum in xrange(4):
            surface.fill(ntscRGB[bar][lum], pygame.Rect(bar*4.57, lum*50, 5, 50))
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
ntscInitPixels()
displayBars()
for y in xrange(HEIGHT):
    print '; scanline: ', y
    for x in xrange(WIDTH):
       surfpix[x][y] = ntscMapRGB(image.getpixel((x, y)), x)
    pygame.display.flip()

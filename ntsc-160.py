import pygame, math, sys
from pygame.locals import *
from PIL import Image

WIDTH          = 160
HEIGHT         = 200
DEG_PER_CIRCLE = 360
DEG_TO_RAD     = math.pi*2/DEG_PER_CIRCLE
UMAX           = 0.436
VMAX           = 0.615

ntscRGB   = [[(0, 0, 0) for y in xrange(4)] for p in xrange(32)]
ntscPixel = [[(0, 0, 0)] for m in xrange(8)]
shrPixels = []
ntscPrev = (0, 0, 0)

def yuv2rgb(y, u, v):
    u *= UMAX
    v *= VMAX
    r = max(0.0, y + 1.14  * v)
    g = max(0.0, y - 0.395 * u - 0.581 * v)
    b = max(0.0, y + 2.033 * u)
    return (r, g, b)

def luv2rgb(l, u, v):
    r = max(0.0, l + v)
    g = max(0.0, l - 0.707 * u - 0.707 * v)
    b = max(0.0, l + u)
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
    for pix8 in xrange(8):
        shrpix = [0 for p in xrange(4)]
        while lumInc(shrpix):
            red = 0
            grn = 0
            blu = 0
            for s in xrange(len(shrpix)):
                red += ntscRGB[pix8*4+s][shrpix[s]][0]
                grn += ntscRGB[pix8*4+s][shrpix[s]][1]
                blu += ntscRGB[pix8*4+s][shrpix[s]][2]
            ntscPixel[pix8].append((red, grn, blu))

def ntscMapRGB(rgb, x):
    global shrPixels
    global ntscPrev

    pix8 = x % 8
    if pix8 == 0:
        shrPixels = [0 for n in xrange(32)]
    #
    # Adjust source color based on reduced destination precision
    #
    redMatch = max(0,int(rgb[0] - ntscPrev[0] * 0.57))
    grnMatch = max(0,int(rgb[1] - ntscPrev[1] * 0.57))
    bluMatch = max(0,int(rgb[2] - ntscPrev[2] * 0.57))
    #
    # Look for best RGB match
    #
    nearest = 195075
    nBest  = 0
    for n in xrange(len(ntscPixel[pix8])):
        red = redMatch - ntscPixel[pix8][n][0]
        grn = grnMatch - ntscPixel[pix8][n][1]
        blu = bluMatch - ntscPixel[pix8][n][2]
        dist = red*red + grn*grn + blu*blu
        if dist < nearest:
            nearest = dist
            nBest   = n
    #
    # Update ouput list
    #
    rgbBest = ntscPixel[pix8][nBest]
    #
    # Convert to SHR pixels
    #
    for n in xrange(4):
        shr = nBest & 0x03
        shrPixels[pix8*4 + n] = shr
        nBest >>= 2
    #
    # Save last pixel
    #
    ntscPrev = ntscRGB[(x*4 + 3) & 0x1F][shr]
    #
    # Output SHR pixels for assembly
    #
    if pix8 == 7:
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
            surface.fill(ntscRGB[bar][lum], pygame.Rect(bar * 5, lum*50, 5, 50))
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

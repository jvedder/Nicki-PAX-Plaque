from HersheyFonts import HersheyFonts

# raw material size (all in mm)
width = 5 * 25.4
height = 2 * 25.4
size = '2x5'
gap = 7
stroke_width = '1.00'

# Font names = ['futural', 'futuram', 'rowmans', 'rowmand', 'rowmant', 'timesr', 'timesrb', 'timesi', 'timesib' ]

font_name_1 = 'timesr'
#font_name_1 = 'futural'
font_height_1 = 10

#font_name_2 = 'timesr'
#font_name_2 = 'futural'
font_name_2 = font_name_1
font_height_2 = 10


# svg offset to make (0,0) in the lower left of the screen
svg_offset_y = 100

DEMO = False


# -------------------
#  Common write_file
# -------------------
def write_file(lines, file):
    print('Writing file:', file, "with", len(lines), "lines of text")
    with open(file, 'w') as f:
        for line in lines:
            f.write(line + '\n')

# ------------------
#  Plot to SVG File
# ------------------
def svg_header(g, name=None):
    g.append('<?xml version="1.0" standalone="no"?>')
    #g.append('<svg width="{0}" height="{1}" version="1.1" xmlns="http://www.w3.org/2000/svg">'.format(svg_width, svg_height))
    g.append('<svg width="5000" height="1000" version="1.1" xmlns="http://www.w3.org/2000/svg">')
    
def svg_footer(g):
    g.append('</svg>')

def svg_stroke(g, stroke):
    if len(stroke):
        g.append('<polyline stroke="black" stroke-width="10" fill="transparent"')
        pts = 'points="'
        for (x,y) in stroke:
            x = round(x, 2) * 10
            y = round(svg_offset_y -y, 2) * 10 
            pts += str(x) + ' ' + str(y) + ' '
        pts += '"/>'
        g.append(pts)

def svg_write(strokes, file):
    lines = list()
    svg_header(lines)
    for stroke in strokes:
        svg_stroke(lines, stroke)
    svg_footer(lines)
    write_file(lines, file)

# ---------------------
#  Plot to Gerber File
# ---------------------
def gerb_round(x):
    #Multiply by 1000 for 2.3 format
    return int(round(x * 1000, 0))

def gerb_header(g, name=None):
    if name:       
        g.append("G04 " + name + " *")
        g.append("G04 *")
    g.append("G04 GERBER PLOT FILE *")
    g.append("G04 Format statement - leading zeroes omitted absolute coordinates, X2.3, Y2.3*")
    g.append("%FSLAX23Y23*%")
    g.append("G04 Set units to mm.*")
    g.append("%MOMM*% ")
    g.append("G04 No offset*")
    g.append("%OFA0B0*%")
    g.append("G04 Scale factor: A = 1.0, B=1.0*")
    g.append("%SFA1.0B1.0*% ")

    g.append("G04 Define aperture D-code 10 as " + stroke_width + " mm circle*")
    g.append("%ADD10C," + stroke_width + "*%")

    g.append("G04 Change to aperture D-code 10*")
    g.append("G54D10*")
    g.append("G01X0Y0D02*")

def gerb_footer(g):
    g.append("D02*")
    g.append("M02*")

def gerb_stroke(g, stroke):
    dcode = 'D02' #move
    for (x,y) in stroke:
        g.append("G01X{0:d}Y{1:d}{2:s}*".format(gerb_round(x), gerb_round(y), dcode))
        dcode = 'D01' # draw to

def gerb_write(strokes, file):
    lines = list()
    gerb_header(lines)
    for stroke in strokes:
        gerb_stroke(lines, stroke)
    gerb_footer(lines)
    write_file(lines, file)

# -------------------------
#  Plot to CNC G-Code File
# -------------------------
def cnc_header(g, name=None):
    if name:
        g.append('(' + name + ')')
        g.append('')
    g.append('G21 (Metric coordinates)')
    g.append('G90 (Abs Positioning)')
    g.append('G94 (Unit per Minute)')
    g.append('G40 (Tool Nose Compensation Cancel)')
    g.append('G17 (Circular Motion in XY plane)')
    g.append('M3S1000 (Spindle On Forward, Speed 1000)')
    g.append('G54 (Use Work Offset #1)')
    g.append('G0Z3 (Safe rapid height)')
    g.append('(start program)')

def cnc_footer(g):
    g.append('(end program)')
    g.append('G0Z5')
    g.append('M5')
    g.append('G0X0Y0')
    g.append('M30')
    g.append('(end)')

def cnc_xy(x, y):
    return 'X' + str(round(x,2)) + 'Y' + str(round(y,2))

def cnc_z(z):
    return 'Z' + str(round(z,2))

def cnc_strokes(g, strokes, offset=(0,0)):
    for stroke in strokes:
        cnc_stroke(g, stroke, offset)

def cnc_stroke(g, stroke, depth):
    if len(stroke):
        move = True
        for (x,y) in stroke:
            if move:
                g.append('G0' + cnc_z(0.5))
                g.append('G0' + cnc_xy(x,y))
                g.append('G1F50' + cnc_z(-depth))
                move = False
            else:
                g.append('G1F100' + cnc_xy(x,y))

def cnc_write(strokes, file, depth):
    lines = list()
    cnc_header(lines)
    for stroke in strokes:
        cnc_stroke(lines, stroke, depth)
    cnc_footer(lines)
    write_file(lines, file)
    
# -------------------
#  Utility functions
# -------------------

def scale_stroke(stroke, scale_x=1.0, scale_y=1.0):
    return list([(x*scale_x, y*scale_y) for (x,y) in stroke])

def scale_strokes(strokes, scale_x=1.0, scale_y=1.0):
    return list([scale_stroke(stroke, scale_x, scale_y) for stroke in strokes])

def offset_stroke(stroke, offset_x=0.0, offset_y=0.0):
    return list([(x+offset_x, y+offset_y) for (x,y) in stroke])

def offset_strokes(strokes, offset_x=0.0, offset_y=0.0):
    return list([offset_stroke(stroke, offset_x, offset_y) for stroke in strokes])

def get_draw_box(strokes):
    min_y = 99999
    min_x = 99999
    max_x = -99999
    max_y = -99999
    for stroke in strokes:
        for (x,y) in stroke:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    return ( min_x, min_y, max_x, max_y )

def inch_to_mm(inch):
    # Inches to mm conversion
    return round(inch *25.4, 2)

def mm_to_inch(mm):
    # mm to Inches conversion
    return round(mm / 25.4, 3)

def center_text(text, offset_y):
    strokes = list(thefont.strokes_for_text(text))
    (x1, y1, x2, y2) = get_draw_box(strokes)
    offset_x = ( width - (x2-x1) )/2 - x1
    print("Text:", text, "Box:", (x1, y1), (x2, y2), "Offset:", (offset_x, offset_y))
    return offset_strokes(strokes, offset_x, offset_y)
    
def make_circle(x, y, dia):
    r = dia / 2
    r45 = r / 1.414214
    stroke = [(x,y+r),(x+r45,y+r45),(x+r,y),(x+r45,y-r45),(x,y-r),(x-r45,y-r45),(x-r,y),(x-r45,y+r45),(x,y+r)]
    return stroke

def make_dot(x, y):
    stroke = [(x,y), (x,y)]
    return stroke


# -------------------------
#  Set-up the Hershey font
# -------------------------
thefont = HersheyFonts()
font_name_list = ['futural', 'futuram', 'rowmans', 'rowmand', 'rowmant', 'timesr', 'timesrb', 'timesi', 'timesib' ]
font_name = 'futural'

# ---------------------
#  Start file contents
# ---------------------
master_strokes = []

# --------------
#  Plot outline
# --------------
if DEMO:
    stroke = [(0,0), (width,0), (width,height), (0,height), (0,0)]
    master_strokes.append(stroke)

# ------
#  Name
# ------
thefont.load_default_font(font_name_1)
thefont.normalize_rendering(font_height_1)
#thefont.render_options.scalex *= 1.1
#thefont.render_options.spacing=0.1
#print('Render Options:', thefont.render_options)
offset_y = (height/2) + (gap/2)
strokes = center_text('Nicki Vedder PAX', offset_y)
master_strokes.extend(strokes)

# ------
#  Date
# ------
thefont.load_default_font(font_name_2)
thefont.normalize_rendering(font_height_2)
#thefont.render_options.scalex *= 1.1
#thefont.render_options.spacing=0.5
#print('Render Options:', thefont.render_options)
offset_y = (height/2) - (gap/2) - font_height_2
strokes = center_text('March 10, 2023', offset_y)
master_strokes.extend(strokes)

### ---------------
###  Mounting Hole 
### ---------------
##(x,y) = (width-6, height-6)
##hole = make_circle(x,y,4)
##dot = make_dot(x,y)
##if DEMO:
##    strokes = [hole, dot]
##else:
##    strokes = [dot]
##master_strokes.extend(strokes)
##print("Dot at", dot)


# ----------------
#  Report Margins
# ----------------
(min_x, min_y, max_x, max_y) = get_draw_box(strokes)
print ("Top Margin", height - max_y)
print ("Bot Margin", min_y)
print ("Left  Margin", min_x)
print ("Right Margin", width - max_x)


# --------------
#  Create Files
# --------------

#name = 'nicki_pax_' + size + '_' + font_name_1 +'_'+str(font_height_1) + '_' + font_name_2 +'_'+str(font_height_2)
name = 'nicki_pax'
gerb_write(master_strokes, name + ".grb")
svg_write(master_strokes, name + ".svg")
cnc_write(master_strokes, name + "_0.10.nc", 0.10)
cnc_write(master_strokes, name + "_0.20.nc", 0.20)
cnc_write(master_strokes, name + "_0.30.nc", 0.30)
cnc_write(master_strokes, name + "_0.40.nc", 0.40)
cnc_write(master_strokes, name + "_0.50.nc", 0.50)
   
print("Done")



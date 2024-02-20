import os
# import sys
# import json
# import subprocess

import tkinter as tk
from PIL import Image, ImageTk

# import nltk
import re


def header():
    return """
    // Persistence Of Vision raytracer version 3.1 sample file.

    global_settings { assumed_gamma 2.2 }

    #include "colors.inc"
    #include "textures.inc"
    #include "shapes.inc"

    #declare rseed = seed(123);

    camera {
        perspective
        location <0.0, 1.5, -12.0>
        direction <0, 0, 1>
        up y
        right x*1.77
        look_at <0.0, 0.5, 0.00>
    }

    light_source {
        <10.00, 15.00, -20.00>
        color White
        area_light <5, 0, 0>, <0, 0, 5>, 5, 5
        adaptive 1
        jitter
    }

    #default {
        pigment { White }
        finish {
            ambient .2
            diffuse .6
            specular .75
            roughness .1
        }
    }
    """


def initialize_dictionary():
    """
    load the translation file into memory
    """
    dictionary = {}
    with open("./data/NSL_Dictionary.data", "r") as handle:
        lines = handle.readlines()

    line_pattern = re.compile(r"^([A-Z]) ([A-Za-z0-9]+) (.+)$")
    for line in lines:
        match = line_pattern.match(line)
        if match:
            groups = match.groups()
            dictionary[groups[1]] = {'part': groups[0], 'code': groups[2]}

    return dictionary


def part_of_speech(record):
    return record['part']


def translate_record(record):
    return record['code']


def text_to_pov(text):
    modifiers = ""
    subject = ""

    line = re.split(" ", text.rstrip())

    print("LINE:", line)

    lookup = initialize_dictionary()
    print("LOOKUP:", lookup)

    for token in line:
        record = lookup.get(token, {"part": "X", "code": ""})

        if part_of_speech(record) == "A":
            modifiers += translate_record(record)
            modifiers += " "

        if part_of_speech(record) == "N":
            subject += translate_record(record)
            subject += " "
            subject += modifiers
            subject += " }\n"
            modifiers = ""

    print("SUBJECT:", subject)
    return subject


def render():
    with open("tmp.pov", "w") as handle:
        handle.write(header())
        handle.write(text_to_pov(editor.get("1.0", tk.END)))

    cmd = "povray "
    cmd += "+L/home/bsloan/povray-3.50b/include "
    cmd += "+D +SP16 -Q9 Antialias=on "
    cmd += "+A0.9 +R16 +J2.2 +UV +UL "
    cmd += "Output_File_Type=P "
    cmd += "-W1280 -H720 -Itmp.pov"
    os.system(cmd)

    image = ImageTk.PhotoImage(Image.open("tmp.ppm"))
    canvas.configure(image=image)
    canvas.image = image


app = tk.Tk()

sizex = 1280
sizey = 720
posx = 100
posy = 100

editor = tk.Text(height=10)
if os.path.exists("tmp.ppm"):
    pil_image = Image.open("tmp.ppm")
    image = ImageTk.PhotoImage(pil_image)

    canvas = tk.Label(image=image)
    canvas.configure(image=image)
else:
    canvas = tk.Label()

button = tk.Button(text="Go!")
button.config(command=render)

canvas.pack()
editor.pack()
button.pack()

app.title("Text to Image")
app.mainloop()

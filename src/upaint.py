import os
import sys
# import json
# import subprocess

import tkinter as tk
from PIL import Image, ImageTk

import nltk
import re


def default_camera():
    return """
    camera {
        perspective
        location <0.0, 1.5, -12.0>
        direction <0, 0, 1>
        up y
        right x*1.77
        look_at <0.0, 0.5, 0.00>
    }
    """


def default_light():
    return """
    light_source {
        <10.00, 15.00, -20.00>
        color White
        area_light <5, 0, 0>, <0, 0, 5>, 5, 5
        adaptive 1
        jitter
    }
    """


def header():
    return """
    #version 3.7;
    
    global_settings { assumed_gamma 2.2 }

    #include "colors.inc"
    #include "textures.inc"
    #include "shapes.inc"

    #declare rseed = seed(123);

    #default {
        pigment { White }
        finish {
            ambient .2
            diffuse .6
            specular .25
            roughness .1
        }
    }
    """


def parse_prompt(in_str):
    result = []
    grammar = r"""
                NP: {<DT|PP\$>?<JJ>*<NN.*>+} # noun phrase
                PP: {<IN><NP>}               # prepositional phrase
                VP: {<MD>?<VB.*><NP|PP>}     # verb phrase
                CLAUSE: {<NP><VP>}           # full clause
            """
    for sentence in re.split(r"\.", in_str):
        sentence = sentence.rstrip()
        if len(sentence) > 3:
            print( "[" + sentence + "]") 
            tokens = nltk.word_tokenize(sentence)
            tagged = nltk.pos_tag(tokens)
            entities = nltk.chunk.ne_chunk(tagged)
            cp = nltk.RegexpParser(grammar)
            temp = cp.parse(entities)
            result.append(temp)
    return result


def extract(part, tree):
    """
    given a phrase type or part-of-speech type and the parsed tree 
    of a sentence, return the associated fragment of text
    """

    result = []
    if part == "S":
        return tree.leaves()
    for child in tree:
        if isinstance(child, nltk.tree.tree.Tree):
            # print(child.label())
            if child.label() == part:
                result = child.leaves()
                result.append("|")
            else:    
                result.extend(extract(part, child))    
        else:
            # print(child[0])
            if child[1] == part:
                result.append(child)
                result.append("|")

    return result 


def on_closing():
    with open("tmp/tmp.txt", "w") as handle:
        handle.write(editor.get("1.0", tk.END))
        handle.write("\n")
    sys.exit(0)    


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

    no_camera = True
    no_light = True
    line = re.split(" ", text.rstrip())

    lookup = initialize_dictionary()

    for token in line:
        record = lookup.get(token, {"part": "X", "code": ""})

        if part_of_speech(record) == "A":
            modifiers += translate_record(record)
            modifiers += " "

        if part_of_speech(record) == "N":
            if token == "camera":
                no_camera = False
            if token == "light":
                no_light = False
            subject += translate_record(record)
            subject += " "
            subject += modifiers
            subject += " }\n"
            modifiers = ""

    if no_camera:
        subject += default_camera()
    if no_light:
        subject += default_light()

    return subject


def change_frame(frame):
    image = ImageTk.PhotoImage(Image.open("tmp/tmp{0}.ppm".format(frame)))
    canvas.configure(image=image)
    canvas.image = image


def render(_=None):
    parsed = parse_prompt(editor.get("1.0", tk.END))

    sentence = "" 
    for tree in parsed:
        tree.pretty_print()
        sentence += " ".join([x[0] for x in extract("S", tree)])
        print("CLAUSE:", " ".join([x[0] for x in extract("CLAUSE", tree)]))
        print("NOUN PHRASES:", " ".join([x[0] for x in extract("NP", tree)]))
        print("VERB PHRASE:", " ".join([x[0] for x in extract("VP", tree)]))
        print("PREPOSITIONAL PHRASE:", " ".join([x[0] for x in extract("PP", tree)]))
        print("ADJECTIVES:", " ".join([x[0] for x in extract("JJ", tree)]))
    # DEBUG

    print("SENTENCE:", sentence)
    with open("tmp/tmp.pov", "w") as handle:
        handle.write(header())
        handle.write(text_to_pov(sentence))

    cmd = "povray "
    cmd += "+Q10 "
    cmd += "+A0.5 +AM1 +R16 +J2.2 +UV +UL "
    cmd += "Output_File_Type=P "
    cmd += "-W1280 -H720 "

    frames = 1
    img_fname = "tmp/tmp.ppm"
    temp_frames = duration.get()
    if temp_frames[-1] == "s":
        frames = int(float(temp_frames[0:-1]) * 24)
    elif temp_frames[-1] == "f":
        frames = int(float(temp_frames[0:-1]))
    else:
        frames = int(float(temp_frames))

    if frames > 1:
        last_frame = 1001 + frames
        slider.configure(to=last_frame)
        cmd += "-KFI1001 -KFF{0} -KI0.0 -KF1.0 ".format(last_frame)
        img_fname = "tmp/tmp1001.ppm"

    cmd += "-Itmp/tmp.pov "

    print(cmd)
    os.system(cmd)

    image = ImageTk.PhotoImage(Image.open(img_fname))
    canvas.configure(image=image)
    canvas.image = image
    return 'break'

app = tk.Tk()
app.protocol("WM_DELETE_WINDOW", on_closing)

sizex = 1280
sizey = 720
posx = 100
posy = 100

editor = tk.Text(height=10)
if os.path.exists("tmp/tmp1001.ppm"):
    pil_image = Image.open("tmp/tmp1001.ppm")
    image = ImageTk.PhotoImage(pil_image)

    canvas = tk.Label(image=image)
    canvas.configure(image=image)
elif os.path.exists("tmp/tmp.ppm"):
    pil_image = Image.open("tmp/tmp.ppm")
    image = ImageTk.PhotoImage(pil_image)

    canvas = tk.Label(image=image)
    canvas.configure(image=image)
else:
    canvas = tk.Label()

frame = tk.Frame()
duration = tk.Entry(frame, width=5)
label = tk.Label(frame, text="Duration")

slider = tk.Scale(
    frame,
    orient=tk.HORIZONTAL,
    length=500,
    from_=1001,
    to=1002,
    command=change_frame)

button = tk.Button(text="Go!")
button.config(command=render)
duration.insert(0, "1")

label.pack(side=tk.LEFT)
duration.pack(side=tk.LEFT)
slider.pack(side=tk.LEFT)

canvas.pack()
editor.pack()
frame.pack()
button.pack()

app.title("Text to Image")

app.update_idletasks()
if os.path.exists("tmp/tmp.txt"):
    with open("tmp/tmp.txt", "r") as handle:
        editor.insert(tk.END, handle.read())

if not os.path.exists("tmp"):
    os.makedirs("tmp")

editor.bind("<Return>", render)
app.mainloop()




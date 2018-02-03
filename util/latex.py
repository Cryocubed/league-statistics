import os

def build_latex_file(filename):
    os.system("pdflatex " + filename)
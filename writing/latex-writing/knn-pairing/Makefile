# build the spiral essay
#   make           -> regenerate figures and build the PDF
#   make pdf       -> just build the PDF
#   make figures   -> just regenerate the PNGs
#   make clean     -> remove latex aux files (keeps figures and PDF)

REPO_ROOT := $(shell git rev-parse --show-toplevel)
SCRIPT    := $(REPO_ROOT)/coding/sampling_a_spiral.py
FIG_DIR   := figures
TEX       := main.tex
PDF       := main.pdf

.PHONY: all pdf figures clean

all: figures pdf

figures:
	python3 $(SCRIPT) --save-dir $(FIG_DIR) --seed 0

pdf: $(PDF)

$(PDF): $(TEX) $(wildcard $(FIG_DIR)/*.png)
	latexmk -pdf -interaction=nonstopmode $(TEX)

clean:
	latexmk -c $(TEX)

# Build the paper: figures (arch-figure toolkit), number macros from results/, then LaTeX.
FIGS := $(wildcard figs/fig_*.py)

all: main.pdf

numbers.tex:
	cd .. && .venv/bin/python -m agentipc.paper_numbers

main.pdf: main.tex refs.bib numbers.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

figures:
	cd figs && for f in $(notdir $(FIGS)); do archfig run $$f; done

clean:
	latexmk -C main.tex

.PHONY: all figures clean numbers.tex

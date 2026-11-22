# Build the paper from the committed generated inputs (numbers.tex, appendix_tables.tex, appendix/, figs/out/).
# `make numbers` regenerates them from results/. Some macros also need data/raw/ and results_raw/ (see the
# README); without those it writes fewer macros and the build fails until
# `git checkout paper/numbers.tex paper/appendix_tables.tex paper/appendix paper/figs/data`.
FIGS := $(wildcard figs/fig_*.py)

all: main.pdf

# Phony so latexmk, which tracks every input itself, decides whether to rebuild.
main.pdf:
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

numbers:
	cd .. && .venv/bin/python -m agentipc.paper_numbers
	cd .. && .venv/bin/python -m agentipc.figdata

figures:
	cd figs && for f in $(notdir $(FIGS)); do archfig run $$f; done

clean:
	latexmk -C main.tex

.PHONY: all main.pdf numbers figures clean

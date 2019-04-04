The user documentation is generated using LaTeX.
The user_manual.tex file is transformed to a user_manual.pdf file.

* system requirements
  * Make sure the PSI supported tex live distribution is available
    []$ module add texlive/2015
    It provides pdflatex, bibtex and gitinfo2
  * inkscape (tool to convert svg files to pdf files)

* how to write the doc
  * put svg images into img folder
  * edit user_manual.tex

* how to build the doc
  * []$ make

* how to clean up
  * []$ make clean
  * []$ make cleaner


# Documents

LaTeX documents for the QML Lab, all with Harvard (author-date) referencing.

```
docs/
  overview/main.tex     The four quadrants of quantum machine learning
  shared/               master copies, edit these:
    qmlproject.sty        look and feel, quadrant colours, citation setup
    harvardqml.bst        Harvard reference style (natbib), DOIs as "Available at"
    references.bib        one bibliography for every document
  build_all.sh          copies shared/ into every document folder and builds all PDFs
  pdf/                  compiled PDFs with readable names

qml_projects/<slug>/docs/main.tex   one living document per project
```

Build everything:

```bash
bash docs/build_all.sh
```

Each document folder also holds copies of the three shared files, so any single folder compiles
on its own (`latexmk -pdf main.tex`) or can be uploaded to Overleaf. Always edit the files in
`docs/shared/` and re-run the build script; it overwrites the copies.

Citing:

| Command | Output |
| --- | --- |
| `\citep{havlicek2019}` | (Havlíček et al., 2019) |
| `\citet{havlicek2019}` | Havlíček et al. (2019) |
| `\citeyearpar{havlicek2019}` | (2019) |
| `\citep[p.~210]{havlicek2019}` | (Havlíček et al., 2019, p. 210) |

New project created with `python manage.py new_project <slug>`: copy any existing
`qml_projects/*/docs/main.tex` into its `docs/` folder as a starting point and run the build script.

# PDF Tool Benchmarking

## Lazy-man’s overview

---

| Rank | Speed | Reliability | Support | Code-"containment"| Structured extraction |
| ---- | ----- | ----------- | ------- | ----------------- | --------------------- |
| #1   | PDFBox | PDFBox     | PDFBox  | PDFBox            | Grobid                |
| #2   | Grobid | Grobid     | Grobid  | PDFMiner          | -                     |
| #3   | PDFMiner | PDFMiner | PDFMiner | Grobid           | -                     |

---

##### Table of Contents

  1. [Specification](#specification)
  1. [PDFs used for "benchmarking"](#PDFs used for "benchmarking")
  1. [PDF Packages](#PDF Packages)
  1. [Speed](#Speed)
  1. [Reliability](#Reliability)
  1. [Software and user support](#Software and user support)
  1. [Code-"containment"](#Code-"containment")
  1. [Conclusions](#Conclusions)


## Specification
The requirements of the PDF extraction tool can be simplified into the following:

  1. Extract full text content.
  1. Reliable extraction, such that it requires little intervention.
  1. Fast extraction, < seconds (minutes for a “normal” PDF is not acceptable, size dependent of course)
  1. Good user support, or at least activity in the project - ensures bug fixes, places to find solutions, source of troubleshooting issues that may arise.
  1. Work as a self contained library rather than being called externally.
  1. Bonus: structured extraction of the text as a feature

## PDFs used for "benchmarking"
To get the widest range of coverage of the types of PDFs we could expect to get, I tried to look for the largest range of publishers that provide us with PDF Documents. The following publishers are in the full text file list, as ‘unique’ PDF providers:

  * AAA
  * ADS
  * arXiv
  * ASJ
  * EGU
  * IOP
  * JACoW
  * LPI
  * SARA
  * SPIE
  * SPIEjournals
  * Springer

They were obtained in the following way:
```
providers=`awk 'if($2~"pdf$"){print $3}' article_list.txt | sort -u`;
for prov in $providers;
do
  grep "$prov" PATH/all.links | tail -1;
done
```

  * 2013BAAA...56..473F     AAA
  * 2015MPBu...42...83W     ADS
  * 2015arXiv150301768G     arXiv
  * 2013PASJ...65L..12T     ASJ
  * 2014TCry....8..215L     EGU
  * 2014TDM.....1c5001R     IOP
  * 2003pac..conf.3569S     JACoW
  * 2014LPICo1774.4095C     LPI
  * 2012JSARA...7...60A     SARA
  * 2015SPIE.9450E..1XZ     SPIE
  * 2014SPIE.8731E..62K     SPIEjournals
  * 2015ZaMP...66..239S     Springer


## PDF Packages
  1. PDFBox: https://pdfbox.apache.org/
  1. Grobid: https://github.com/kermitt2/grobid
  1. PDFMiner: https://github.com/euske/pdfminer/ (https://github.com/jonnybazookatone/PDFMiner-tools)

N.B. how to run them once installed:
  * PDFBox
    * java -jar pdfbox-1.8.8/app/target/pdfbox-app-1.8.8.jar ExtractText <PDF_FILE_NAME>
  * Grobid
    * java -Xmx1024m -jar grobid-core/target/grobid-core-0.3.3-SNAPSHOT.one-jar.jar -gH grobid-home/ -gP grobid-home/config/grobid.properties -dIn pdf_papers/ -dOut pdf_papers/ -exe processFullText
  * PDFMiner
    * python PDFMiner-tools/extract.py -i pdf_papers/ -o pdf_papers/

## Speed

For the set of files looked at, they perform at the current average rate:

  * Grobid: Average time taken: 3.25 sec
  * PDFBox: Average time taken: 1.75 sec
  * PDFMiner: Average time taken: 8.83 sec

PDF average size: 1.33M, translates to:

  * Grobid: 2.44 MB/s or 0.31 pdf/s
  * PDFBox: 1.31 MB/s or 0.57 pdf/s
  * PDFMiner: 6.62 MB/s or 0.11 pdf/s

## Reliability
The question to answer is at what quality and level of consistency, are the files extracted. Below are some general notes on each of the PDFs when looking at the extracted text.

  1. 2013BAAA...56..473F
    * PDFBox: Gets confused on quotations "", and also some foreign letters with accents
    * Grobid: Seems to handle the accents fairly well
    * PDFMiner: This seemingly stopped extraction after page 1??

  1. 2015MPBu...42...83W
    * PDFBox: Struggles still with fonts that are from latex, e.g., $\alpha$ - otherwise it is fine
    * Grobid: Does not handle when a paper starts on the same page as another. As expected, only one      title/abstract is selected, and the references are for the incorrect paper.
    * PDFMiner: Seemingly stopped extracting after page 1 (again....? works on one of 'normal' files though)

  1. 2015arXiv150301768G
    * PDFBox: Cannot handle the equations, just dumps random text
    * Grobid: Cannot handle the table of contents extraction, thinks some headings are part of the content of the other headings. Handles quite well the formula, but they are still nonsensical afterwards
    * PDFMiner: Not too disimilar to that of

  1. 2013PASJ...65L..12T
    * PDFBox: Works OK, gets confused on unknown characters, ^{-1} in math, or $\sim$, for example. A lot of TeX fonts seem to be an issue.
    * Grobid: As the others it struggles with equations, otherwise does a good job.
    * PDFMiner: Gets confused easily with some words, e.g. ampliï¬cation rather than 'amplification'. Similar output to PDFBox.

  1. 2014TCry....8..215L
    * PDFBox: As normal, failing on latex glyphs - maybe there exists a solution to this?
    * Grobid: Perfect case study for grobid
    * PDFMiner: Similar standard to PDFBox

  1. 2014TDM.....1c5001R
    * PDFBox: Normal reduction, same standard problems with glyphs.
    * Grobid: Normal reduction.
    * PDFMiner: Normal reduction, same standard problems with glyphs.

  1. 2003pac..conf.3569S
    * PDFBox: Normal reduction, same standard problems with glyphs.
    * Grobid: Also mis-identifies 1,2,3
    * PDFMiner: Again, struggles with some normal words 'ff', 'f', etc. Also adds some extra letters that don't exist, seemingly mistaking circled numbers 1, 2, 3 as k, j, l.

  1. 2014LPICo1774.4095C
    * PDFBox: All works, file is very simple.
    * Grobid: All works, file is very simple.
    * PDFMiner: All works, file is very simple.

  1. 2012JSARA...7...60A
    * PDFBox: Normal reduction, same standard problems with glyphs.
    * Grobid: Normal.
    * PDFMiner: Normal reduction, same standard problems with glyphs.

  1. 2015SPIE.9450E..1XZ
    * PDFBox: Gets confused by the figure, thinks that the figure letters mean it is column-like.
    * Grobid: Gets confused by the figure, thinks that the figure letters mean it is column-like.
    * PDFMiner: Gets confused by the figure, thinks that the figure letters mean it is column-like.

  1. 2014SPIE.8731E..62K
    * PDFBox: Normal reduction, same standard problems with glyphs.
    * Grobid: Cannot handle author descriptions that follow the acknnowledgements.
    * PDFMiner: Normal reduction, same standard problems with glyphs.

  1. 2015ZaMP...66..239S
    * PDFBox: Normal reduction, same standard problems with glyphs.
    * Grobid: Normal.
    * PDFMiner: Normal reduction, same standard problems with glyphs.

## Software and user support
  * PDFBox is an Apache open source project, there is a mailing list, issue tracker, and ~ 2,546 results on stackoverflow
  * Grobid is a private side-project of around ~4 developers (mainly 1), there is activity on the github issues page (1 person usually answering), and 2 results on stackoverflow (17 for pdf2xml)
  * PDFMiner is an open source project, ~11 developers (1 primarily active), however, it is difficult to see if the author wants to continue upkeep of the software

## Code-"containment"

  * PDFBox is a java tool, and is self-contained
  * Grobid calls pdf2xml externally via bash and therefore waits for a child process
  * PDFMiner is a python tool, and is self-contained

## Conclusions

Below is the overall table of properties. PDFBox scores the best on all of the criteria, bar structured extraction, for which it does not have any vanilla code to do this. Further extensions would have to take advantage of Grobid's structured extraction, or develop a semi-sensible way in tandem with PDFBox.

---

| Rank | Speed | Reliability | Support | Code-"containment"| Structured extraction |
| ---- | ----- | ----------- | ------- | ----------------- | --------------------- |
| #1   | PDFBox | PDFBox     | PDFBox  | PDFBox            | Grobid                |
| #2   | Grobid | Grobid     | Grobid  | PDFMiner          | -                     |
| #3   | PDFMiner | PDFMiner | PDFMiner | Grobid           | -                     |

---

# alkis-sh
A compilation of scripts for acquiring a complete list of downloadable ALKIS files from GDI-SH, enabling bulk download of these files, and converting them into [shapefile](https://en.wikipedia.org/wiki/Shapefile).

# Introduction
The German federal state of Schleswig-Holstein offers a free download of their [ALKIS](https://de.wikipedia.org/wiki/Amtliches_Liegenschaftskatasterinformationssystem) data on [their website](https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/dl-alkis.html). Unfortunately, the interactive download client only allows the download of one _Flur_ (containing multiple _Flurstücke_) at a time.

Needing all ALKIS files for a specific city in Schleswig-Holstein and wanting to avoid individual downloads, I examined the download process, which always involves three steps:
1. Send a download request with the _Flur_'s unique ID and a second `ogc_fid` to a specific URL
2. The server then generates an archive, assigns a download ID, while the browser checks for sucess every 5 seconds
3. Once ready, the archive is downloadable at a new download-URL for one hour upon receiving a "success" response

Here's an example of such a request-URL: ```https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/_ajax/details.php?gemarkung=Stafstedt&flur=010402001&a_datum=2023-11-06&a_datum_dmy=06.11.2023&quartal=11_2023&gemeinde=Stafstedt&ogc_fid=8228&type=alkis&id=8228&_uid=alkis8228```

Most data in the download request isn't necessary for initiating the download of the latest file, but two IDs - _Flur_: ```ogc_fid``` and ```flur```– connected to the desired _Flur_ are essential. Mismatched or missing IDs result in failed requests.

Since no list of these IDs existed, my first task was creating a database containing all IDs and additional information like _Gemarkung_, _Gemeinde_ and date of the last update. The script **gather-ids.py** accomplishes this. 

Afterwards, one can filter and sort these IDs as needed and initiate a batch download. This is where the script **dl-flur.py** comes into play. 

Finally, I needed the data in shapefile format, hence the script **convert-to-shape.py** handles the conversion from NAS-XML (the file format used by German organisations working with geodata) to shapefile.

# Disclaimer

All scripts where tested in November 2023 and may no longer work because of changes by GDI-SH to the way their website and server handles the download of ALKIS data. 

Please be cautious as improper usage of these scripts can result in putting a huge load on the infrastructure of GDI-SH and your local machine and network. The `dl-flur.py` script includes mechanisms to limit request frequency, and I strongly advise only requesting necessary data.

Always check scripts before running them. `dl-flur.py` displays a overview of the set parameters before continuing 

# Requirements
General requirements for all scripts:
- python
- Python modules/libraries:
	- csv
	- os

## gather-ids.py
Python modules/libraries:
- requests
- json
- time

You need about 20MB of storage space and an internet connection.

## dl-flur.py
Python modules/libraries:
- requests
- datetime
- collections

You ned a list of IDs that you want to download as CSV file. See file `id-sample.csv` for structure or use the latest dump performed with `gather-ids.py`. Alternatively simply run `gather-ids.py` yourself and use the output.

Depending on the number of downloaded files, you need between a few MBs to a few dozen to 200 GBs of storage. Also, you need an internet connection. Please note, that the download size can exceed the allowance of most mobile data plans.

## convert-to-shape.py
Python modules/libraries:
- gzip
- datetime
- glob
- subprocess
- zipfile

You need to have [GDAL](https://gdal.org/api/python_bindings.html) installed in order to use [ogr2ogr](https://gdal.org/programs/ogr2ogr.html). The script will fail if ogr2ogr is not installed.

# Usage
## gather-ids.py
Running the script will create a folder `IDs` containing a txt-file for each ID with the output for that specific ID. This is mainly a backup in case anything goes wrong. The main output is a `responses.csv` file, that contains a data column for every class returned by the website.

During my tests, I never found files with an ID larger than 18171 so the `range()` is set to that value. In case your script stops due to internet issues or timeouts, please check for the already downloaded IDs and adjust `range(x)` accordingly so that you don't send the same requests all over again.

IDs don't change that often or get added so it may not be necessary to run this script and instead use the export of the latest run in this repo for downloading the files with `dl-flur.py`.

## dl-flur.py
Place in same folder as your list with IDs.

I did not find any rate limiting mechanisms in place on side of GDI-SH's server other than the wait time between a request and the file being ready for download. That being said, your are not the only person downloading files which is why I put some rate limiting mechanisms in place that prevent sending too many requests by accident. The default values are set so that you could still download all 18171 files in less than a day while not putting too much strain on the server. **Please be considerate**!

In order to not overwhelm the server with too many requests, download requests are sent in chunks of 20. Adjust variable `chunk_size` if needed though you may run into performance issues later when preparing the files for download takes longer than usual.

When sending a download request, the server needs some time to prepare the file. Usually this takes between 5 to 10 seconds but sometimes there is a longer wait time. The script checks for the status periodically but we don't want to send a check request every other second so the wait time increases by a fixed multipler after each failed check. There is also a termination threshold set after which a download is no longer attempted.

Default values:
```
chunk_size = 20
initial_wait_time = 5
multiplier = 1.2
termination_threshold = 50
```


## convert-to-shape.py
Documentation still work in progress.

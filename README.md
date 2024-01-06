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

All scripts were tested in November 2023. They may cease to function due to future modifications by GDI-SH in their website and server protocols for downloading ALKIS data.

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

Requires a CSV file list of IDs for download. Refer to `id-sample.csv` for the format or use the latest data dump made with `gather-ids.py`. Alternatively, you can run `gather-ids.py` yourself.

Storage needs range from a few MBs to over 200 GBs, depending on the number of files downloaded. An internet connection is necessary. Be aware that the download size could exceed most mobile data plan limits.

## convert-to-shape.py
Python modules/libraries:
- gzip
- datetime
- glob
- subprocess
- zipfile

Requires [GDAL](https://gdal.org/api/python_bindings.html) installed in order to use [ogr2ogr](https://gdal.org/programs/ogr2ogr.html). The script will run if ogr2ogr is not installed but not output anything.

# Usage
## gather-ids.py
Running the script creates a folder `IDs`, holding a txt-file for each ID with the output for that specific ID. This is mainly a backup in case anything goes wrong. The main output is a `responses.csv` file, that contains a data column for every class returned by the website.

During my tests, I never found files with an ID larger than 18171 so the `range()` is set to that value. In case your script stops due to internet issues or timeouts, please check for the already downloaded IDs and adjust `range(x)` accordingly so that you don't send the same requests all over again.

Given the infrequent changes and additions of IDs, it might be unnecessary to rerun this script. Instead, use the latest export from this repository.

## dl-flur.py
Place in same folder as your list with IDs.

I did not find any rate limiting mechanisms in place on side of GDI-SH's server other than the wait time between a request and the file being ready for download. That being said, your are not the only person downloading files which is why I put some rate limiting mechanisms in place that prevent sending too many requests by accident. The default settings allow downloading all 18171 files in less than a day without overburdening the server. **Please be considerate**!

To avoid server overload, download requests are sent in batches of 20. Adjust the `chunk_size` if necessary, but be aware of potential performance issues if file preparation takes longer than usual.

The server takes time to prepare files, typically 5 to 10 seconds per file, but occasionally longer. The script periodically checks the status, with increasing intervals after each failed check. A termination threshold is set beyond which the script ceases download attempts.

Default values:
```
chunk_size = 20
initial_wait_time = 5
wait_time_multiplier = 1.2
termination_threshold = 50
```


## convert-to-shape.py
Documentation still work in progress.

short introduction to NAS-XML

short introduction to ogr2ogr

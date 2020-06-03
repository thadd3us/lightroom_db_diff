# Lightroom Catalog Database Diff

## Intro

Adobe Lightroom is one of my favorite tools for organizing and editing photographs.
I switched to it when Google discontinued Picasa.  One of Lightroom's coolest features
is that a Lightroom catalog, which contains all the information Lightroom known about 
your photos, is just a SQLite database.

Lightroom also encourages you to keep backup snapshots of your database, offering to do this
every time you exit the program.  This is great in case you make a mistake, and I once recovered
some photo captions I'd lost years ago from an old Lightroom Catalog backup.

However, the number of backup Catalogs can grow quickly, and they can take a lot of space.
This tool helps me figure out whether I'm comfortable deleting some of the older catalog backups.

## db_dff.py
This tool compares the contents of a sequence of Lightroom Catalogs, to show you information
that was REMOVED in the transition from one catalog to the next.  It DOES NOT show you things that
were added--that would produce lots of noise as more photos are added to the catalog.  If you want
to see them, though, you could run the tool in the other direction.

IMPORTANT: It doesn't exhaustively compare
all information, just some of the metadata fields that I happen to use.

### Example command
```
python db_diff.py \
    testdata/test_catalogs/test_catalog_01/test_catalog_01_fresh.lrcat \
    testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat \
    testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat \
    testdata/test_catalogs/test_catalog_04/test_catalog_04_more_face_tags_gps_edit.lrcat > z.html
```
### Sample output

<div>

<h1>Compare 0 vs 1</h1>
<ul>
<li> db1: testdata/test_catalogs/test_catalog_01/test_catalog_01_fresh.lrcat
<li> db2: testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat
</ul>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: left;">
      <th style="min-width: 100px;">DIFF_TYPE</th>
      <th style="min-width: 100px;">value_db1</th>
      <th style="min-width: 100px;">value_db2</th>
      <th style="min-width: 100px;">AgLibraryFile_idx_filename_db1</th>
      <th style="min-width: 100px;">AgLibraryFolder_pathFromRoot_db1</th>
      <th style="min-width: 100px;">AgLibraryRootFolder_absolutePath_db1</th>
      <th style="min-width: 100px;">IMAGE_LINK_db1</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
<p>
If the above looks OK, you can remove the left catalog (db1) using:
<pre>
rm "testdata/test_catalogs/test_catalog_01/test_catalog_01_fresh.lrcat"
</pre>
<h1>Compare 1 vs 2</h1>
<ul>
<li> db1: testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat
<li> db2: testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat
</ul>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: left;">
      <th style="min-width: 100px;">DIFF_TYPE</th>
      <th style="min-width: 100px;">value_db1</th>
      <th style="min-width: 100px;">value_db2</th>
      <th style="min-width: 100px;">value_delta</th>
      <th style="min-width: 100px;">AgLibraryFile_idx_filename_db1</th>
      <th style="min-width: 100px;">AgLibraryFolder_pathFromRoot_db1</th>
      <th style="min-width: 100px;">AgLibraryRootFolder_absolutePath_db1</th>
      <th style="min-width: 100px;">IMAGE_LINK_db1</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>CAPTION</td>
      <td>The Golden Gate Bridge in San Francisco, CA at sunset.</td>
      <td>The Golden Gate Bridge in San Francisco, CA at sunset.  Taken from Marin.</td>
      <td></td>
      <td>GoldenGateBridge-001.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg</a></td>
    </tr>
    <tr>
      <td>GPS_LATITUDE</td>
      <td>48.1375</td>
      <td>48.1373</td>
      <td>-0.00014153557999918576</td>
      <td>1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg</a></td>
    </tr>
    <tr>
      <td>GPS_LATITUDE</td>
      <td>37.8269</td>
      <td>37.8278</td>
      <td>0.0009617301183340032</td>
      <td>GoldenGateBridge-001.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg</a></td>
    </tr>
    <tr>
      <td>GPS_LONGITUDE</td>
      <td>11.5754</td>
      <td>11.5756</td>
      <td>0.00012749997833338966</td>
      <td>1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg</a></td>
    </tr>
    <tr>
      <td>GPS_LONGITUDE</td>
      <td>-122.486</td>
      <td>-122.488</td>
      <td>-0.0013783787833290262</td>
      <td>GoldenGateBridge-001.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg</a></td>
    </tr>
    <tr>
      <td>RATING</td>
      <td>3</td>
      <td>4</td>
      <td>1.0</td>
      <td>1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg</a></td>
    </tr>
    <tr>
      <td>RATING</td>
      <td>3</td>
      <td></td>
      <td></td>
      <td>GoldenGateBridge-001.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg</a></td>
    </tr>
    <tr>
      <td>RATING</td>
      <td>4</td>
      <td>5</td>
      <td>1.0</td>
      <td>Hermann_Hesse_2.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Hermann_Hesse_2.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Hermann_Hesse_2.jpg</a></td>
    </tr>
    <tr>
      <td>REMOVED FROM COLLECTION</td>
      <td>Heroes</td>
      <td>None</td>
      <td></td>
      <td>Hermann_Hesse_2.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Hermann_Hesse_2.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Hermann_Hesse_2.jpg</a></td>
    </tr>
    <tr>
      <td>REMOVED FROM COLLECTION</td>
      <td>Heroes</td>
      <td>None</td>
      <td></td>
      <td>Martin_Luther_King,_Jr..jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Martin_Luther_King%2C_Jr..jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Martin_Luther_King%2C_Jr..jpg</a></td>
    </tr>
    <tr>
      <td>REMOVED FROM KEYWORD</td>
      <td>Erde</td>
      <td>None</td>
      <td></td>
      <td>1200px-The_Earth_seen_from_Apollo_17.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-The_Earth_seen_from_Apollo_17.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/1200px-The_Earth_seen_from_Apollo_17.jpg</a></td>
    </tr>
    <tr>
      <td>REMOVED FROM KEYWORD</td>
      <td>Hermann Hesse</td>
      <td>None</td>
      <td></td>
      <td>Hermann_Hesse_2.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Hermann_Hesse_2.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/Hermann_Hesse_2.jpg</a></td>
    </tr>
  </tbody>
</table>
<p>
If the above looks OK, you can remove the left catalog (db1) using:
<pre>
rm "testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat"
</pre>
<h1>Compare 2 vs 3</h1>
<ul>
<li> db1: testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat
<li> db2: testdata/test_catalogs/test_catalog_04/test_catalog_04_more_face_tags_gps_edit.lrcat
</ul>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: left;">
      <th style="min-width: 100px;">DIFF_TYPE</th>
      <th style="min-width: 100px;">value_db1</th>
      <th style="min-width: 100px;">value_db2</th>
      <th style="min-width: 100px;">value_delta</th>
      <th style="min-width: 100px;">AgLibraryFile_idx_filename_db1</th>
      <th style="min-width: 100px;">AgLibraryFolder_pathFromRoot_db1</th>
      <th style="min-width: 100px;">AgLibraryRootFolder_absolutePath_db1</th>
      <th style="min-width: 100px;">IMAGE_LINK_db1</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GPS_LATITUDE</td>
      <td>37.827827756526666</td>
      <td>37.827544289161665</td>
      <td>-0.0002834673650013997</td>
      <td>GoldenGateBridge-001.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg</a></td>
    </tr>
    <tr>
      <td>GPS_LONGITUDE</td>
      <td>-122.48773672802666</td>
      <td>-122.48189497883833</td>
      <td>0.005841749188334688</td>
      <td>GoldenGateBridge-001.jpg</td>
      <td></td>
      <td>/Users/thad/Google Drive/src/lightroom/testdata/test_photos/</td>
      <td><a href="file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg" target="_blank">file:///Users/thad/Google%20Drive/src/lightroom/testdata/test_photos/GoldenGateBridge-001.jpg</a></td>
    </tr>
  </tbody>
</table>
<p>
If the above looks OK, you can remove the left catalog (db1) using:
<pre>
rm "testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat"
</pre>

</div>


## Available column names

Sadly, image title is only buried deep in the XMP field:
https://community.adobe.com/t5/user/viewprofilepage/user-id/10375732/user-messages-feed/latest-contributions

* AgLibraryIPTC_id_local
* AgLibraryIPTC_caption
* AgLibraryIPTC_copyright
* AgLibraryIPTC_image
* AgHarvestedExifMetadata_id_local
* AgHarvestedExifMetadata_image
* AgHarvestedExifMetadata_aperture
* AgHarvestedExifMetadata_cameraModelRef
* AgHarvestedExifMetadata_cameraSNRef
* AgHarvestedExifMetadata_dateDay
* AgHarvestedExifMetadata_dateMonth
* AgHarvestedExifMetadata_dateYear
* AgHarvestedExifMetadata_flashFired
* AgHarvestedExifMetadata_focalLength
* AgHarvestedExifMetadata_gpsLatitude
* AgHarvestedExifMetadata_gpsLongitude
* AgHarvestedExifMetadata_gpsSequence
* AgHarvestedExifMetadata_hasGPS
* AgHarvestedExifMetadata_isoSpeedRating
* AgHarvestedExifMetadata_lensRef
* AgHarvestedExifMetadata_shutterSpeed
* Adobe_images_id_local
* Adobe_images_id_global
* Adobe_images_aspectRatioCache
* Adobe_images_bitDepth
* Adobe_images_captureTime
* Adobe_images_colorChannels
* Adobe_images_colorLabels
* Adobe_images_colorMode
* Adobe_images_copyCreationTime
* Adobe_images_copyName
* Adobe_images_copyReason
* Adobe_images_developSettingsIDCache
* Adobe_images_fileFormat
* Adobe_images_fileHeight
* Adobe_images_fileWidth
* Adobe_images_hasMissingSidecars
* Adobe_images_masterImage
* Adobe_images_orientation
* Adobe_images_originalCaptureTime
* Adobe_images_originalRootEntity
* Adobe_images_panningDistanceH
* Adobe_images_panningDistanceV
* Adobe_images_pick
* Adobe_images_positionInFolder
* Adobe_images_propertiesCache
* Adobe_images_pyramidIDCache
* Adobe_images_rating
* Adobe_images_rootFile
* Adobe_images_sidecarStatus
* Adobe_images_touchCount
* Adobe_images_touchTime
* AgLibraryFile_id_local
* AgLibraryFile_id_global
* AgLibraryFile_baseName
* AgLibraryFile_errorMessage
* AgLibraryFile_errorTime
* AgLibraryFile_extension
* AgLibraryFile_externalModTime
* AgLibraryFile_folder
* AgLibraryFile_idx_filename
* AgLibraryFile_importHash
* AgLibraryFile_lc_idx_filename
* AgLibraryFile_lc_idx_filenameExtension
* AgLibraryFile_md5
* AgLibraryFile_modTime
* AgLibraryFile_originalFilename
* AgLibraryFile_sidecarExtensions
* AgLibraryFolder_id_local
* AgLibraryFolder_id_global
* AgLibraryFolder_parentId
* AgLibraryFolder_pathFromRoot
* AgLibraryFolder_rootFolder
* AgLibraryFolder_visibility
* AgLibraryRootFolder_id_local
* AgLibraryRootFolder_id_global
* AgLibraryRootFolder_absolutePath
* AgLibraryRootFolder_name
* AgLibraryRootFolder_relativePathFromCatalog
* PARSED_CAPTURE_TIME
* IMAGE_LINK

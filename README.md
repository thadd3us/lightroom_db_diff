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
that was removed in the transition from one catalog to the next.

IMPORTANT: It doesn't exhaustively compare
all information, just some of the metadata fields that I happen to use.

```
python db_diff.py 
    testdata/test_catalogs/test_catalog_01/test_catalog_01_fresh.lrcat
    testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat
    testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat
    testdata/test_catalogs/test_catalog_04/test_catalog_04_more_face_tags_gps_edit.lrcat
```

## Available column names

TODO
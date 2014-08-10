Requires:  
Python3  
  
Python modules required:  
gir libraries Gtk, Gdk, GLib, AppIndicator3  
cairo, transmissionrpc, psutil,   
These are standard but listed in case of packing up a portable interpreter....  
subprocess, signal, os, json, cgi  

Getting started:  
Close transmission-gtk for the first run.  
Launch transmissionWidget.py  
 - reason is that it modifies the config.json and transmission saves it on shutdown...  
 - from here on out, you should be fine to start the widget before or after launching the gtk front-end  

Prettying up the sidebar and sequential downloading, color/transparency configuration -  
all coming, but I had to get it sort of working first.

TODOs:  
1) sequential downloading:  
Say you want "lecture videos.torrent" that contains  
Lec_semester01_class01  
Lec_semester01_class02  
Lec_semester01_class03  
Lec_semester01_class04  
Lec_semester01_class05  
Lec_semester01_class06  
Lec_semester02_class01  
Lec_semester02_class02  
Lec_semester02_class03  
Lec_semester02_class04  
Lec_semester02_class05  
Lec_semester02_class06  
  
It will automatically adjust high/low priorities of all files to get the next incomplete file as quickly as possible without ignoring the others.  
   
2) configuration options for text and background coloration, window position, and transparency  
  
3) notification on individual file completion  
  
4) anything else?
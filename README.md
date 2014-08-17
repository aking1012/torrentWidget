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
1) configuration options for text and background coloration, window position, and transparency  
  
2) notification on individual file completion  
  
3) anything else?

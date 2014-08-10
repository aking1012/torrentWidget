#!/usr/bin/env python3

#UI stuff
import cairo
from gi.repository import Gtk, Gdk, GLib
from gi.repository import AppIndicator3 as appindicator

#Connector for the transmissionrpc service
import transmissionrpc

#Other things we need
import subprocess, psutil, signal, os, json, cgi

signal.signal(signal.SIGINT, signal.SIG_DFL)

'''
#TODO
config win UI
  ?hands-off list
  toggle in order
  set max-file
'''

class EnvCheck:
  '''
  Make sure everything we need is in place
  '''
  def __init__(self, root):
    self.app = root
    self.daemon_installed = self.__is_transmission_gtk_installed()
    self.try_connect()

  def try_connect(self):
    self.can_connect = self.__can_i_connect()

  def kill_transmission_process(self):
    try:
      self.app.transmission_proc.terminate()
      outs, errs = self.app.transmission_proc.communicate(timeout=30)
    except:
      try:
        self.app.transmission_proc.kill()
        outs, errs = proc.communicate()
      except:
        pass

  def __is_transmission_gtk_installed(self):
    return subprocess.check_output(["which", "transmission-gtk"])

  def __is_running(self):
    for proc in psutil.process_iter():
      try:
        pinfo = proc.as_dict(attrs=['pid', 'name'])
      except psutil.NoSuchProcess:
        pass
      else:
        if pinfo['name'] == 'transmission-gtk':
          self.app.config.tran_pid = pinfo['pid']
          return True
    return False

  def __can_i_connect(self):
    if not self.__is_running():
      self.app.transmission_proc = subprocess.Popen(['transmission-gtk','--minimized'])
      self.__is_running()
    try:
      print("Trying to connect...")      
      print(self.app.config.config_params['rpc-port'])
      self.app.tc = transmissionrpc.Client('localhost', port=int(self.app.config.config_params['rpc-port']))
      return True
    except:
      print("Failed to connect...")      
      return False

class MyIndicator:
  def __init__(self, root):
    self.app = root

    icon_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons')
    self.ind = appindicator.Indicator.new(
                self.app.name,
                "indicator-messages",
                appindicator.IndicatorCategory.APPLICATION_STATUS)
    self.ind.set_icon_theme_path(icon_folder)
    self.ind.set_icon('TransmissionWidgetIcon')
    self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
    self.menu = Gtk.Menu()
    item = Gtk.MenuItem()
    item.set_label("Toggle Widget")
    item.connect("activate", self.app.main_win.cb_show, '')
    self.menu.append(item)

    item = Gtk.MenuItem()
    item.set_label("Configuration")
    item.connect("activate", self.app.conf_win.cb_show, '')
    self.menu.append(item)

    item = Gtk.MenuItem()
    item.set_label("Exit")
    item.connect("activate", self.cb_exit, '')
    self.menu.append(item)

    self.menu.show_all()
    self.ind.set_menu(self.menu)

  def cb_exit(self, w, data):
    self.app.env_check.kill_transmission_process()
    Gtk.main_quit()

class MyConfigWin(Gtk.Window):
  def __init__(self, root):
    super().__init__()
    self.app = root
    self.set_title(self.app.name + ' Config Window')

  def cb_show(self, w, data):
    if self.get_visible():
      self.hide()
    else:
      self.show()

class MyMainWin(Gtk.Window):
  def __init__(self, root):
    super().__init__()
    self.app = root
    self.set_decorated(False)
    self.set_title(self.app.name)
    self.set_skip_taskbar_hint(True)
    self.set_keep_below(True)
    self.root_box = Gtk.VBox()
    self.root_box.pack_start(self.app.worker.box, False, 0, 0)
    self.add(self.root_box)
    self.screen = self.get_screen()
    self.visual = self.screen.get_rgba_visual()
    if self.visual != None and self.screen.is_composited():
      self.set_visual(self.visual)
    self.set_app_paintable(True)
    self.connect("draw", self.area_draw)
    screen = self.get_screen()
    self.set_size_request(200, Gdk.Screen.height())
    self.move(Gdk.Screen.width() - 200, 0)
    self.show_all()

  def area_draw(self, widget, cr):
    cr.set_source_rgba(.2, .2, .2, 0.2)
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)

  def cb_show(self, w, data):
    if self.get_visible():
      self.hide()
    else:
      self.show_all()

class MyConfig:
  def __init__(self, root):
    self.app = root
    with open(os.path.join(os.getenv('HOME'), '.config/transmission/settings.json')) as settings_file:
      self.config_params = json.loads(settings_file.read())
    self.config_params["rpc-authentication-required"] = False
    self.config_params["rpc-bind-address"] = "0.0.0.0"
    self.config_params["rpc-enabled"] = True
    self.config_params["rpc-port"] = 9091
    self.config_params["rpc-url"] = "/transmission/"
    self.config_params["rpc-username"] = ""
    self.config_params["rpc-whitelist"] = "127.0.0.1"
    self.config_params["rpc-whitelist-enabled"] = True
    self.write()

  def write(self):
    with open(os.path.join(os.getenv('HOME'), '.config/transmission/settings.json'), 'w') as settings_file:
      settings_file.write(json.dumps(self.config_params))


class MyWorker:
  def __init__(self, root):
    self.app = root
    self.box = Gtk.VBox()

  def get_torrents(self):
    box = Gtk.VBox()
    try:
      torrents = self.app.tc.get_torrents()
      for torrent in torrents:
        item_box = Gtk.VBox()
        label = Gtk.Label()

        if len(torrent.name) > 20:
          name = torrent.name[:20]
        else:
          name = torrent.name
        t = cgi.escape(name)
        label.set_markup ("<span fgcolor='white'>{0}</span>".format(t))
        item_box.pack_start(label, False, 0 ,0)
        label = Gtk.Label()
        completed = str(torrent.percentDone * 100)
        if len(completed) > 18:
          completed = completed[:18] + ' %'
        t = cgi.escape(completed)
        label.set_markup ("<span fgcolor='white'>{0}</span>".format(t))
        item_box.pack_start(label, False, 0 ,0)
        box.pack_start(item_box, False, 0, 0)
      self.app.main_win.root_box.remove(self.box)
      self.box = box
      self.app.main_win.root_box.pack_start(self.box, False, 0, 0)
      self.app.main_win.root_box.show_all()    
    except:
      self.app.env_check.try_connect()


    GLib.timeout_add_seconds(5, self.get_torrents)

class MyApp(Gtk.Application):
  def __init__(self, app_name):
    super().__init__()
    self.name = app_name
    self.config = MyConfig(self)
    self.env_check = EnvCheck(self)
    self.worker = MyWorker(self)
    self.main_win = MyMainWin(self)
    self.conf_win = MyConfigWin(self)
    self.indicator = MyIndicator(self)

  def run(self):
    GLib.timeout_add_seconds(5, self.worker.get_torrents)
    Gtk.main()

if __name__ == '__main__':
  app = MyApp('Transmission Service Widget')
  app.run()
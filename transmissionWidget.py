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

class EnvCheck:
  '''
  Make sure everything we need is in place
  '''
  def __init__(self, root):
    self.app = root
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
      self.app.tc = transmissionrpc.Client('localhost', port=int(self.app.config.config_params['rpc-port']))
      return True
    except:
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
  #Needs to be prettified
  def __init__(self, root):
    super().__init__()
    self.app = root
    self.set_title(self.app.name + ' Config Window')
    self.set_position(Gtk.WindowPosition.CENTER)    

    grid = Gtk.Grid()
    #There's a better way to do this it's just temporary kludge
    spacer_a = Gtk.Box()
    spacer_b = Gtk.Box()
    spacer_a.set_size_request(400, 1)
    spacer_b.set_size_request(400, 1)
    grid.attach(spacer_a, 1, 1, 1, 1)
    grid.attach(spacer_b, 2, 1, 1, 1)

    grid.attach(Gtk.Label(label='Transparency'), 1, 2, 1, 1)
    scale = Gtk.HScale.new_with_range(min=0, max=100, step=1)
    scale.set_value(self.app.config.opacity*100)
    scale.connect("value-changed", self.set_opacity)
    grid.attach(scale, 2, 2, 1, 1)

    grid.attach(Gtk.Label(label='Background Color'), 1, 3, 1, 1)
    bgcol = Gtk.ColorButton.new_with_color(self.color_cairo_to_gdk(self.app.config.rb, self.app.config.gb, self.app.config.bb))
    bgcol.connect("color-set", self.set_bg_col)
    grid.attach(bgcol, 2, 3, 1, 1)

    grid.attach(Gtk.Label(label='Foreground Color'), 1, 4, 1, 1)
    #Move this to a method
    col_nums = []    
    n=2
    line = self.app.config.fg_col.lstrip('#')
    for item in [line[i:i+n] for i in range(0, len(line), n)]:
      col_nums.append(int(item, 16)*257)
    #End move this
    fgcol = Gtk.ColorButton.new_with_color(Gdk.Color(col_nums[0],col_nums[1],col_nums[2]))
    fgcol.connect("color-set", self.set_fg_col)
    grid.attach(fgcol, 2, 4, 1, 1)

    grid.attach(Gtk.Label(label='Always below'), 1, 5, 1, 1)
    below = Gtk.Switch()
    below.set_active(self.app.config.below)
    below.connect("notify::active", self.set_below)
    grid.attach(below, 2, 5, 1, 1)

    grid.attach(Gtk.Label(label='Show on all workspaces'), 1, 6, 1, 1)
    sticky = Gtk.Switch()
    sticky.set_active(self.app.config.stick)
    sticky.connect("notify::active", self.set_sticky)
    grid.attach(sticky, 2, 6, 1, 1)

    grid.attach(Gtk.Label(label='Sequential downloads'), 1, 7, 1, 1)
    sequential = Gtk.Switch()
    sequential.set_active(self.app.config.sequential)
    sequential.connect("notify::active", self.set_sequential)
    grid.attach(sequential, 2, 7, 1, 1)

    grid.set_row_homogeneous(True)
    grid.set_column_homogeneous(True)

    self.add(grid)
    grid.show_all()
    self.connect('delete-event', self.cb_show)
  def set_sequential(self, w, data):
    self.app.config.sequential = w.get_active()
  def set_opacity(self, w):
    self.app.config.opacity = w.get_value()/100
    self.app.main_win.queue_draw()
  def set_below(self, w, data):
    self.app.config.below = w.get_active()
    self.app.main_win.set_below()
  def set_sticky(self, w, data):
    self.app.config.stick = w.get_active()
    self.app.main_win.set_sticky()

  #Cherry picked these out of pygtk graphing module
  def color_cairo_to_gdk(self, r, g, b):
    return Gdk.Color(int(65535 * r), int(65535 * g), int(65535 * b)) 
  def color_gdk_to_cairo(self, color): 
    return (color.red / 65535.0, color.green / 65535.0, color.blue / 65535.0) 

  def set_bg_col(self, w):
    self.app.config.rb, self.app.config.gb, self.app.config.bb = self.color_gdk_to_cairo(w.get_color())
    self.app.main_win.queue_draw()

  def color_gdk_to_markup(self, color):
    temp = []
    for item in (color.red, color.green, color.blue):
      temp.append(hex(int(item/257)).split('x')[1].zfill(2))
    return '#' + ''.join(temp)
  def set_fg_col(self, w):
    self.app.config.fg_col = self.color_gdk_to_markup(w.get_color())
    self.app.worker.get_torrents()

  def cb_show(self, w, data=''):
    if self.get_visible():
      self.hide()
    else:
      self.show()
    return True

class MyMainWin(Gtk.Window):
  def __init__(self, root):
    super().__init__()
    self.app = root
    self.set_decorated(False)
    self.set_title(self.app.name)
    self.set_skip_taskbar_hint(True)
    self.set_below()
    self.set_sticky()
    #Should probably make this a scrollable and the window not resizable...
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
    self.set_size_request(200, Gdk.Screen.height()-25)
    self.move(Gdk.Screen.width() - 200, 25)
    self.show_all()
    self.hide()
    self.connect('delete-event', self.cb_show)

  def area_draw(self, widget, cr):
    cr.set_source_rgba(self.app.config.rb, self.app.config.gb, self.app.config.bb, self.app.config.opacity)
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)

  def set_below(self):
    if self.app.config.below:
      self.set_keep_above(False)
      self.set_keep_below(True)
    else:
      self.set_keep_below(False)
      self.set_keep_above(True)
    self.queue_draw()
  def set_sticky(self):
    if self.app.config.stick:
      self.stick()
    else:
      self.unstick()
    self.queue_draw()

  def cb_show(self, w, data=''):
    if self.get_visible():
      self.hide()
    else:
      self.show_all()
    return True



class MyConfig:
  def __init__(self, root):
    '''
    options to expose:
    ?position(left or right/top spacing)

    Activity:
    number of files per torrent to give high priority and set the rest to low
    toggle that behavior on or off "hands-off mode"
    '''
    self.app = root
    self.opacity = 0.2
    self.rb = .2
    self.gb = .2
    self.bb = .2
    self.fg_col = '#FFFFFF'
    self.below = True
    self.stick = True
    self.sequential = False
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

  def is_sequential(self, torrents):
    if self.app.config.sequential:
      print("Trying sequential")
      for torrent in torrents:
        if torrent.status == 'downloading':
          low = []
          torrent_files = torrent.files()
          for item in torrent_files:
            low.append(item)
          high = []
          for item in sorted(torrent_files, key=lambda x: torrent_files[x]['name']):
            if torrent_files[item]['size'] - torrent_files[item]['completed'] > 0:
              high.append(item)
              break
          try:
            low.pop(low.index(high[0]))
            self.app.tc.change(torrent.id, priority_high=high, priority_low=low)
          except:
            self.app.tc.change(torrent.id, priority_low=low)

  def get_torrents(self):
    box = Gtk.VBox()
    try:
      torrents = self.app.tc.get_torrents()
      self.is_sequential(torrents)
      print("Trying screen")
      for torrent in torrents:
        item_box = Gtk.VBox()
        label = Gtk.Label()
        if len(torrent.name) > 20:
          name = torrent.name[:20]
        else:
          name = torrent.name
        t = cgi.escape(name)
        label.set_markup ("<span fgcolor='{0}'>{1}</span>".format(self.app.config.fg_col,t))
        item_box.pack_start(label, False, 0 ,0)
        label = Gtk.Label()
        completed = str(torrent.percentDone * 100)
        if len(completed) > 18:
          completed = completed[:18] + ' %'
        t = cgi.escape(completed)
        label.set_markup ("<span fgcolor='{0}'>{1}</span>".format(self.app.config.fg_col,t))
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

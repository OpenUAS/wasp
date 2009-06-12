import sys
import os
import datetime
import math
import gtk.gdk
import osmgpsmap
import gobject
import logging

import gs.data as data

from gs.database import Database
from gs.config import Config

from gs.managers.turretmanager import TurretManager
from gs.managers.sourcemanager import SourceManager
from gs.managers.testmanager import TestManager
from gs.managers.mapmanager import MapManager
from gs.managers.graphmanager import GraphManager
from gs.ui.graph import Graph
from gs.ui.tree import DBWidget, TelemetryTreeModel
from gs.ui.msgarea import MsgAreaController
from gs.ui.plane_view import PlaneView
from gs.ui.horizon import HorizonView
from gs.ui.camera import CameraWindow
from gs.ui.preferences import PreferencesWindow
from gs.ui.statusbar import StatusBar

LOG = logging.getLogger('groundstation')

class Groundstation:

    def __init__(self, uifile="data/groundstation.xml", prefsfile="prefs.ini"):
        gtk.gdk.threads_init()
        try:
            self._builder = gtk.Builder()
            self._builder.add_from_file(uifile)
        except Exception:
            LOG.critical("Could not find xml file")
            sys.exit(1)
        self._window = self._builder.get_object("window1")
        self._gps_coords = self._builder.get_object("gps_coords")

        #The Main application elements
        self._config = Config(filename=prefsfile)
        self._sm = SourceManager(self._config)
        self._map = MapManager(self._config)
        self._tm = TurretManager(self._config)
        self._test = TestManager(self._config)
        self._gm = GraphManager(self._config, self._builder.get_object("graphs_box"), self._window)
        self._msg = MsgAreaController()
        self._sb = StatusBar()

        #Setup all those elements that are updated whenever data arrives from
        #the UAV
        self._updateable = [
            self._sb,
            self._map,
            self._tm,
            self._gm,
            #self._plane_view               get added when constructed
            #self._horizon_view             get added when constructed
            #self._*_graph                   added in create_graphs()
            #self._telemetry_tree_model     added in create_datatree()
        ]

        #Lazy initialize the following when first needed
        self._plane_view = None
        self._horizon_view = None
        self._camera_window = None
        self._prefs_window = None
    
        #Create final UI elements
        self._create_map()
        self._create_datatree()
        self._create_graphs()

        #Setup those items which are configurable, or depend on configurable
        #information, and implement config.ConfigurableIface
        self._configurable = [
            self._map,
            self._sm,
            self._gm,
            self._tm,
            self._test,
        ]
        for c in self._configurable:
            if c:
                c.update_state_from_config()

        for u in self._updateable:
            u.set_source_manager(self._sm)

        self._builder.get_object("vbox2").pack_start(self._msg, False, False)
        self._builder.get_object("vbox1").pack_start(self._sb, False, False)
        self._builder.get_object("menu_item_disconnect").set_sensitive(False)
        self._builder.get_object("menu_item_autopilot_disable").set_sensitive(False)
        self._builder.get_object("add_graph_menu_item").connect("activate", self._gm.on_add_graph)
        self._builder.connect_signals(self)

    def _create_map(self):
        self._builder.get_object("map_holder").add(self._map.get_widget())
        self._map.connect("notify::auto-center", self.on_map_autocenter_property_change)
        self._map.connect("notify::show-trip-history", self.on_map_show_trip_history_property_change)
        self._map.connect("button-press-event", self.map_click_callback)
    
    def _create_datatree(self):
        data_treeview = self._builder.get_object("data_tree")

        i = 0
        for name in ("Name", "Value"):
            col = gtk.TreeViewColumn(name)
            data_treeview.append_column(col)
            cell = gtk.CellRendererText()
            col.pack_start(cell, True)
            col.add_attribute(cell, 'text', i)
            i += 1

        self._telemetry_tree_model = TelemetryTreeModel()
        data_treeview.set_model(self._telemetry_tree_model)
        self._updateable.append(self._telemetry_tree_model)

    def _create_graphs(self):
        graphs_notebook = self._builder.get_object("plots_notebook")

        self._accel_graph = Graph(self._window, graphs_notebook, 
                                    lines=(data.AX, data.AY,data.AZ),
                                    label="Acceleratons",
                                    yrange=[0,1])
        self._updateable.append(self._accel_graph)

        self._attitude_graph = Graph(self._window, graphs_notebook,
                                    lines=(data.PITCH, data.ROLL, data.YAW),
                                    label="Attitudes",
                                    yrange=[0,10])
        self._updateable.append(self._attitude_graph)

        self._rotational_graph = Graph(self._window, graphs_notebook,
                                    lines=(data.P, data.Q, data.R),
                                    label="Rotational Velocities",
                                    yrange=[0,1])
        self._updateable.append(self._rotational_graph)

    def _error_message(self, message, secondary=None):
        m = gtk.MessageDialog(
                    self._window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_OK,
                    message)
        if secondary:
            m.format_secondary_text(secondary)
        m.run()
        m.destroy()

    def on_window_destroy(self, widget):
        self._sm.get_source().quit()
        for c in self._configurable:
            if c:
                c.update_config_from_state()
        self._config.save()
        gtk.main_quit()

    def on_menu_item_home_activate(self, widget):
        self._map.set_mapcenter(-43.520451,172.582377,12)

    def on_menu_item_zoom_in_activate(self, widget):
        self._map.set_zoom(self._map.props.zoom+1)

    def on_menu_item_zoom_out_activate(self, widget):
        self._map.set_zoom(self._map.props.zoom-1)    

    def on_menu_item_cache_map_activate(self, widget):

        def update_download_count(msg, msgarea, gpsmap):
            remaining = gpsmap.get_property("tiles-queued")
            msg.update_text(
                    primary_text=None,
                    secondary_text="%s tiles remaining" % remaining)
            if remaining > 0:
                return True
            else:
                msgarea.clear()
                return False

        dlg = self._builder.get_object("cache_maps_dialog")

        #widgets
        pt1la = self._builder.get_object("pt1_lat_entry")
        pt1lo = self._builder.get_object("pt1_lon_entry")
        pt2la = self._builder.get_object("pt2_lat_entry")
        pt2lo = self._builder.get_object("pt2_lon_entry")
        z = self._map.get_property("zoom")
        mz = self._map.get_property("max-zoom")

        #preload with the current bounding box
        pt1_lat, pt1_lon,pt2_lat,pt2_lon = self._map.get_bbox()
        pt1la.set_text(str(math.degrees(pt1_lat)))
        pt1lo.set_text(str(math.degrees(pt1_lon)))
        pt2la.set_text(str(math.degrees(pt2_lat)))
        pt2lo.set_text(str(math.degrees(pt2_lon)))

        #get the zoom ranges
        zoom_start = self._builder.get_object("zoom_start_spinbutton")
        zoom_stop = self._builder.get_object("zoom_stop_spinbutton")
        
        #default to caching from current -> current + 2
        zoom_start.set_range(1, mz)
        zoom_start.set_value(z)
        zoom_stop.set_range(1, mz)
        zoom_stop.set_value(min(z+2,mz))

        resp = dlg.run()
        if resp == gtk.RESPONSE_OK:
            self._map.download_maps(
                        math.radians(float(pt1la.get_text())),
                        math.radians(float(pt1lo.get_text())),
                        math.radians(float(pt2la.get_text())),
                        math.radians(float(pt2lo.get_text())),
                        int(zoom_start.get_value()),
                        int(zoom_stop.get_value()))
            
            msg = self._msg.new_from_text_and_icon(
                                gtk.STOCK_CONNECT,
                                "Caching Map Tiles",
                                "Calculating...")
            msg.show_all()
            gobject.timeout_add(500, update_download_count, msg, self._msg, self._map)

        dlg.hide()

    def on_menu_item_preferences_activate(self, widget):
        if not self._prefs_window:
            self._prefs_window = PreferencesWindow(self._window, self._configurable)

        resp = self._prefs_window.show(self._config)
        #If the user clicked ok to the dialog, update all 
        #objects which are configuration dependant
        if resp == gtk.RESPONSE_ACCEPT:
            for obj in self._configurable:
                obj.update_state_from_config()
            
    def on_menu_item_connect_activate(self, widget):
        source = self._sm.get_source()
        source.connect_to_craft()

    def on_menu_item_disconnect_activate(self, widget):
        self._sm.get_source().disconnect_from_aircraft()
        
    def on_autopilot_enable_activate(self, widget):
        self._builder.get_object("menu_item_autopilot_disable").set_sensitive(True)
        self._builder.get_object("menu_item_autopilot_enable").set_sensitive(False)
    
    def on_autopilot_disable_activate(self, widget):
        self._builder.get_object("menu_item_autopilot_disable").set_sensitive(False)
        self._builder.get_object("menu_item_autopilot_enable").set_sensitive(True)
        

    def on_menu_item_about_activate(self, widget):
        dlg = gtk.AboutDialog()
        dlg.set_authors(("Mark Cottrell", "John Stowers"))
        dlg.set_version("0.1")
        dlg.run()
        dlg.destroy()
        
    def on_menu_item_dock_all_activate(self, widget):
        for p in (self._accel_graph, self._attitude_graph, self._rotational_graph):
            p.dock_handler(True)
        
    def db_chooser_callback(self, widget):
        filename = widget.get_filename()
        if filename:
            #tell the database to load from a new file
            db = Database(filename)
            
            db_notes = self._builder.get_object("db_notes")
            buff = db_notes.get_buffer()
            
            notes = db.fetchall("select notes from flight where rowid=1")[0][0]
            if (notes):
                buff.set_text(notes)

            sw = self._builder.get_object("dbscrolledwindow")
            for c in sw.get_children():
                sw.remove(c)
            dbw = DBWidget(db)
            dbw.show()
            sw.add(dbw)
            db.close()

    def on_flight_props_activate(self, widget):
        self._error_message("Not Implemented")
        #dlg = self._builder.get_object("db_dialog")
        #sw = self._builder.get_object("dbscrolledwindow")
        #db_notes = self._builder.get_object("db_notes")
        #buff = gtk.TextBuffer()
        #file_chooser = self._builder.get_object("db_file_chooser")
        
        #db_notes.set_buffer(buff)
                
        #file_chooser.connect("file-set", self.db_chooser_callback)
        #file_chooser.unselect_all()

        #file_filter = gtk.FileFilter()
        #file_filter.set_name("sqlite filter")
        #file_filter.add_mime_type("application/x-sqlite3")
        #file_chooser.set_filter(file_filter)
        
        #source = self._sm.get_source()
        #db = source.get_db()
        
        #if db.is_open():
        #    file_chooser.set_filename(db.get_filename())
        #    notes = db.fetchall("select notes from flight where rowid=1")[0][0]
        #    if (notes):
        #        buff.set_text(notes)
        #    dbw = DBWidget(db)
        #    dbw.show()
        #    sw.add(dbw)
        #resp = dlg.run()
        #if resp == gtk.RESPONSE_OK:
        #    filename = file_chooser.get_filename()
        #    if db.is_open() and db.get_filename() != filename:
        #        source.disconnect_from_aircraft()
        #        source.connect_to_aircraft(filename)
        #    else:
        #        source.get_db().open_from_file(filename)
        #    db = source.get_db()
        #    if db.is_open():
        #        buff = db_notes.get_buffer()
        #        notes = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
        #        db.execute("update flight set notes=? where rowid=1", (notes,))
        #for c in sw.get_children():
        #    sw.remove(c)
        #dlg.hide()
        #db.close()

    def on_menu_item_show_previous_activate(self, widget):
        dlg = self._builder.get_object("db_dialog")
        sw = self._builder.get_object("dbscrolledwindow")
        db_notes = self._builder.get_object("db_notes")
        buff = gtk.TextBuffer()
        file_chooser = self._builder.get_object("db_file_chooser")
        
        db_notes.set_buffer(buff)
                
        file_chooser.connect("file-set", self.db_chooser_callback)
        file_chooser.unselect_all()

        file_filter = gtk.FileFilter()
        file_filter.set_name("sqlite filter")
        file_filter.add_mime_type("application/x-sqlite3")
        file_chooser.set_filter(file_filter)
        
        resp = dlg.run()
        if (resp == gtk.RESPONSE_OK):
            filename = file_chooser.get_filename()
            db = Database(filename)
            track = []
            for r in db.fetchall("SELECT %s, %s FROM flight_data" % (data.LAT, data.LON)):
                track.append( (math.radians(r[0]),math.radians(r[1])) )
            self._map.add_track(track)
        for c in sw.get_children():
            sw.remove(c)
        dlg.hide()
        db.close()

    def on_menu_item_plane_view_activate(self, widget):
        if self._plane_view == None:
            self._plane_view = PlaneView()
        self._plane_view.show_all()
        self._updateable.append(self._plane_view)
        self._plane_view.set_source_manager(self._sm)
        
    def on_menu_item_horizon_view_activate(self, widget):
        if self._horizon_view == None:
            self._horizon_view = HorizonView()
        self._horizon_view.show_all()
        self._updateable.append(self._horizon_view)
        self._horizon_view.set_source_manager(self._sm)

    def on_menu_item_camera_view_activate(self, widget):
        if self._camera_window == None:
            self._camera_window = CameraWindow()
        self._camera_window.start()
        self._camera_window.show()

    def cell_edited_cb(self, cell, path, new_text, user_data):
        ls, col = user_data
        ls[path][col] = float(new_text)
        return

    def record_flight_map_click_callback(self, osmMap, event, coordModel):
        mouse_x = event.x
        mouse_y = event.y
        lat,lon = osmMap.get_co_ordinates(mouse_x, mouse_y)
        lat = math.degrees(lat)
        lon = math.degrees(lon)
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            coordModel.prepend( (lat,lon,0) )
            osmMap.draw_gps(lat,lon,0)

    def on_stop_record_flight(self, widget):
        pass

    def on_record_flight_activate(self, widget):
        win  = self._builder.get_object("record_flight_window")
        record_hbox  = self._builder.get_object("record_vbox")
        coordview = self._builder.get_object("coordview")
        lm = gtk.ListStore(float,float,float)

        idx = 0
        for name in ("Lat","Lon","Alt"):
            col = gtk.TreeViewColumn(name)
            cell = gtk.CellRendererText()
            if (name == "Alt"):
                cell.set_property('editable', True)
                cell.connect('edited', self.cell_edited_cb, (lm, idx))
                col.pack_start(cell, True)
                col.add_attribute(cell, "text", idx)
            else:
                col.pack_start(cell, True)
                col.add_attribute(cell, 'text', idx)
            coordview.append_column(col)
            idx += 1

        m = osmgpsmap.GpsMap(
                repo_uri=self._map.props.repo_uri,
                proxy_uri=self._map.props.proxy_uri,
                tile_cache=self._map.props.tile_cache)

        m.props.auto_center = False
        record_hbox.pack_start(m)
        m.connect("button-press-event", self.record_flight_map_click_callback, lm)
        coordview.set_model(lm)
        win.show_all()
        m.set_mapcenter(self._map.props.latitude, self._map.props.longitude, self._map.props.zoom)
        
    def on_record_flight_window_delete(self, widget, event):
        widget.hide_all()
        return True

    def on_menu_item_clear_path_activate(self, widget):
        self._map.clear_gps()

    def on_menu_item_clear_previous_activate(self, widget):
        self._map.clear_tracks()

    def on_map_autocenter_property_change(self, osm, param):
        self._builder.get_object("menu_item_auto_centre").set_active(osm.get_property("auto-center"))
        
    def on_menu_item_auto_centre_toggled(self, widget):
        self._map.props.auto_center = widget.get_active()

    def on_map_show_trip_history_property_change(self, osm, param):
        self._builder.get_object("menu_item_show_path").set_active(osm.get_property("show-trip-history"))

    def on_menu_item_show_path_toggled(self, widget):
        self._map.props.show_trip_history = widget.get_active()

    def map_click_callback(self, widget, event):
        mouse_x = event.x
        mouse_y = event.y
        lat,lon = self._map.get_co_ordinates(mouse_x, mouse_y)
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            self._map.draw_gps(lat,lon,0)

    def main(self):
        self._window.show_all()
        gtk.main()

if __name__ == "__main__":
    gs = Groundstation()
    gs.main()
import logging
import gtk

import gs.ui
import gs.config as config
import wasp.ui.treeview as treeview

LOG = logging.getLogger("settings")

def num_digits(num):
    digits = 0
    while num < 1 and (1.0 - num) > 1e-10:
        digits += 1
        num /= .1
    return digits

class _EditSetting(gtk.Frame):
    def __init__(self, setting, source, **msgs):
        gtk.Frame.__init__(self, label=setting.name)
        self.set_border_width(5)
        self._setting = setting
        self._source = source

        alignment = gtk.Alignment(xscale=1.0)
        alignment.set_padding(0,5,0,5)
        self.add(alignment)

        self._box = gtk.HBox(spacing=10)
        alignment.add(self._box)

        #create a slider and a spin entry
        min_, default, max_, step = setting.get_value_adjustment()
        self._adj = gtk.Adjustment(
                    value=float(default),
                    lower=float(min_),
                    upper=float(max_),
                    step_incr=float(step),
                    page_incr=10.0*step)

        slider = gtk.HScale(self._adj)
        spin = gtk.SpinButton(self._adj)

        if type(default) == float:
            digits = num_digits(step)
            slider.set_digits(digits)
            spin.set_digits(digits)
        else:
            slider.set_digits(0)
            spin.set_digits(0)

        self._getmsg = msgs["get"]
        self._msgs = msgs[setting.type]
        self._spin = spin
        self._box.pack_start(slider,True)
        self._box.pack_start(spin,False)

        #get button
        getbtn = gtk.Button("Get")
        getbtn.connect("clicked", self._on_get_button_clicked)
        self._box.pack_start(getbtn, False)

        #set button
        setbtn = gtk.Button("Set")
        setbtn.connect("clicked", self._on_set_button_clicked)
        self._box.pack_start(setbtn, False)

        if not setting.get:
            getbtn.set_sensitive(False)

        if not setting.set:
            slider.set_sensitive(False)
            spin.set_sensitive(False)
            setbtn.set_sensitive(False)

    def _on_set_button_clicked(self, btn):
        v = self._setting.format_value(self._adj.value)
        LOG.debug("Set setting: %s = %s" % (self._setting.name, v))
        self._source.send_message(
                        self._msgs,
                        (self._setting.id, self._setting.type_enum_value, v))

    def _on_get_button_clicked(self, btn):
        LOG.debug("Get setting: %s" % self._setting.name)
        self._source.send_message(
                        self._getmsg,
                        (self._setting.id,))

    def set_size(self, sizegroup):
        sizegroup.add_widget(self._spin)

    def set_value(self, value):
        self._adj.value = value

class _EditSettingsManager(gtk.VBox):
    def __init__(self, source, **msgs):
        gtk.VBox.__init__(self, spacing=10)
        self._sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._settings = {}
        self._source = source
        self._msgs = msgs

    def add_setting(self, setting):
        if setting.id not in self._settings:
            es = _EditSetting(setting, self._source, **self._msgs)
            es.set_size(self._sg)
            es.show_all()
            self.pack_start(es, False, True)
            self._settings[setting.id] = es

    def update_setting_value(self, settingid, value):
        try:
            setting = self._settings[settingid]
            setting.set_value(value)
        except KeyError:
            LOG.warn("Could not find setting, id: %d" % settingid)

class SettingsController(gs.ui.GtkBuilderWidget):

    MSGS = {0:"No",1:"Yes"}

    DEFAULT_SHOW_ONLY_DYNAMIC = True

    def __init__(self, source, settingsfile, messagesfile):
        gs.ui.GtkBuilderWidget.__init__(self, "settings.ui")

        self._source = source
        self._settingsfile = settingsfile
        self.widget = self.get_resource("hbox")

        #the settings manager controls sending new settings to the craft
        self._sm = _EditSettingsManager(source,
                        get=messagesfile.get_message_by_name("GET_SETTING"),
                        uint8=messagesfile.get_message_by_name("SETTING_UINT8"),
                        int32=messagesfile.get_message_by_name("SETTING_INT32"),
                        float=messagesfile.get_message_by_name("SETTING_FLOAT")
        )
        self.get_resource("setting_right_vbox").pack_start(self._sm, False, True)

        ts = treeview.SettingsTreeStore()
        for section in self._settingsfile.all_sections:
            iter_ = ts.add_section(section)
            for s in section.settings:
                ts.add_setting(s, section=iter_)

        tv = treeview.SettingsTreeView(ts, show_all_colums=False)
        tv.get_selection().connect(
                "changed",
                self._on_selection_changed,
                tv)
        self.get_resource("settings_sw").add(tv)

        btn = self.get_resource("setting_edit_button")
        btn.connect(
                "clicked",
                self._on_es_clicked,
                tv)
        btn.set_sensitive(False)

        #connect to checkbutton toggled signal
        self.get_resource("show_editable_only_cb").connect(
                    "toggled",
                    lambda btn, tv_: tv_.show_only_dynamic(btn.get_active()),
                    tv)

        #listen for settings messages
        source.register_interest(self._on_setting, 0, "SETTING_UINT8")
        source.register_interest(self._on_setting, 0, "SETTING_FLOAT")
        source.register_interest(self._on_setting, 0, "SETTING_INT32")

    def _on_setting(self, msg, header, payload):
        id_, type_, val = msg.unpack_values(payload)
        LOG.debug("Got setting: %d %s" % (id_, val))
        self._sm.update_setting_value(id_, val)

    def _on_es_clicked(self, btn, _tv):
        setting = _tv.get_selected_setting()
        if setting:
            self._sm.add_setting(setting)

    def _on_selection_changed(self, _ts, _tv):
        self.get_resource("setting_info_hbox").set_sensitive(True)
        edit_btn = self.get_resource("setting_edit_button")

        setting = _tv.get_selected_setting()
        if setting:
            self.get_resource("name_value").set_text(setting.name)
            self.get_resource("value_value").set_text(setting.default_value_string)
            self.get_resource("can_set_value").set_text(self.MSGS[setting.set])
            self.get_resource("can_get_value").set_text(self.MSGS[setting.get])
            self.get_resource("doc_value").set_text(setting.doc)

            if setting.set or setting.get:
                edit_btn.set_sensitive(True)
            else:
                edit_btn.set_sensitive(False)

        else:
            self.get_resource("name_value").set_text("")
            self.get_resource("value_value").set_text("")
            self.get_resource("can_set_value").set_text("")
            self.get_resource("can_get_value").set_text("")
            self.get_resource("doc_value").set_text("")
            self.get_resource("setting_info_hbox").set_sensitive(False)
            edit_btn.set_sensitive(False)


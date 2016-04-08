#!/usr/bin/python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, GObject
from gi.repository import GtkSource

# App Menu
MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label" translatable="yes">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label" translatable="yes">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""

class TabLabel(Gtk.Box):
    __gsignals__ = {
        "close-clicked": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
    }
    def __init__(self, label_text):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(5) # spacing: [icon|5px|label|5px|close]  

        # icon
        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, False, False, 0)
        self.spinner.set_visible(False)
        
        # label
        label = Gtk.Label(label_text)
        self.text = label_text
        self.pack_start(label, True, True, 0)
       
        # close button
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        button.add(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU))
        button.connect("clicked", self.button_clicked)
        data =  ".button {\n" \
                "-GtkButton-default-border : 0px;\n" \
                "-GtkButton-default-outside-border : 0px;\n" \
                "-GtkButton-inner-border: 0px;\n" \
                "-GtkWidget-focus-line-width : 0px;\n" \
                "-GtkWidget-focus-padding : 0px;\n" \
                "padding: 0px;\n" \
                "}"
        provider = Gtk.CssProvider()
        provider.load_from_data(bytes(data, "ascii"))
        # 600 = GTK_STYLE_PROVIDER_PRIORITY_APPLICATION
        button.get_style_context().add_provider(provider, 600)
        self.pack_start(button, False, False, 0)
       
        self.show_all()
        self.spinner.set_visible(False)
   
    def button_clicked(self, button, data=None):
        self.emit("close-clicked")

    def get_text(self):
        return self.text

    def start_working(self):
        self.spinner.start()
        self.spinner.set_visible(True)

    def stop_working(self):
        self.spinner.stop()
        self.spinner.set_visible(False)

class BitWin(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title("Untitled")
        self.header.set_subtitle("Bit")

        btn_open  = Gtk.Button('Open')
        btn_save  = Gtk.Button('Save')
        btn_new   = Gtk.Button.new_from_icon_name('tab-new-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        btn_flash = Gtk.Button.new_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.SMALL_TOOLBAR)

        self.header.pack_start(btn_open)
        self.header.pack_start(btn_new)
        self.header.pack_end(btn_save)
        self.header.pack_end(btn_flash)
        
        btn_new.connect("clicked", self.on_new_clicked, self)
        btn_open.connect("clicked", self.on_open_clicked, self)
        btn_save.connect("clicked", self.on_save_clicked, self)
        btn_flash.connect("clicked", self.on_flash_clicked, self)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        #toolbutton = Gtk.ToolButton(stock_id=Gtk.STOCK_NEW)
        #toolbutton.set_is_important(True)
        #toolbutton.connect("clicked", self.on_new_clicked, self)

        toolbar = Gtk.Toolbar()
        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        #toolbar.insert(toolbutton, 0)

        self.box.add(toolbar)

        self.notebook = Gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_scrollable (True)
        Gtk.Notebook.popup_enable (self.notebook)
        self.notebook.connect("switch-page", self.on_page_changed, None)

        self.files = []
        self.create_sourceview()
        self.box.pack_start(self.notebook, True, True, 0)
        
        self.add(self.box)
        self.set_default_size(800,600)
        self.set_titlebar(self.header)
        self.set_icon_name("applications-development")
        self.show_all()

    def on_page_changed(self, happy, page, page_num, data):
        self.header.set_title(self.notebook.get_tab_label(page).get_text())
        print(page.bit_buffer.get_text(page.bit_buffer.get_start_iter(), page.bit_buffer.get_end_iter(), True))

    def create_sourceview(self, file = "/home/pi/projects/Untitled Folder/template.py"):

        filename = file.split('/')
        filename = filename[len(filename)-1]

        lm = GtkSource.LanguageManager.new()
        language = lm.guess_language(file, None)

        buffer = GtkSource.Buffer()

        if language:
            buffer.set_highlight_syntax(True)
            buffer.set_language(language)
            print(language)
        else:
            print('No language found for file "%s"' % file)
            buffer.set_highlight_syntax(False)

        source_file = GtkSource.File()
        source_file.set_location(Gio.File.new_for_path(file))
        source_file_loader = GtkSource.FileLoader.new(buffer, source_file)
        source_file_loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

        # style list /usr/share/gtksourceview-3.0/
        sourceview = GtkSource.View.new_with_buffer(buffer)
        sourceview.set_auto_indent(True)
        sourceview.set_indent_on_tab(True)
        sourceview.set_show_line_numbers(True)
        sourceview.set_highlight_current_line(True)
        sourceview.set_smart_home_end(True)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.add(sourceview)

        tab_label = TabLabel(filename)
        tab_label.connect("close-clicked", self.on_close_clicked, self.notebook, scrolledwindow)
        
        self.notebook.append_page(scrolledwindow, tab_label)
        self.notebook.set_tab_reorderable(scrolledwindow, True)
        scrolledwindow.bit_file = source_file
        scrolledwindow.bit_buffer = buffer
        scrolledwindow.show_all()
        tab_label.show_all()
        self.notebook.set_current_page(self.notebook.page_num(scrolledwindow))

    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()

    def on_close_clicked(self, widget2, sender, widget):
        #get the page number of the tab we wanted to close
        pagenum = self.notebook.page_num(widget)
        #and close it
        self.notebook.remove_page(pagenum)

    def on_new_clicked(self, widget, data):
        self.create_sourceview()
        self.show_all()

    def on_save_clicked(self, widget, data):
        source_file_saver = GtkSource.FileSaver.new(self.notebook.get_nth_page(self.notebook.get_current_page()).bit_buffer, self.notebook.get_nth_page(self.notebook.get_current_page()).bit_file)
        self.notebook.get_tab_label(self.notebook.get_nth_page(self.notebook.get_current_page())).start_working()
        source_file_saver.save_async(GLib.PRIORITY_DEFAULT, None, None, None, self.done_io, self.notebook.get_nth_page(self.notebook.get_current_page()))
        print("Save")
        
    def done_io(self, task, result, data):
        self.notebook.get_tab_label(data).stop_working()
        
    def on_open_clicked(self, widget, data):
        print("Open")
        filechooserdialog = Gtk.FileChooserDialog("Open", self, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_py = Gtk.FileFilter()
        filter_py.set_name("Python files")
        filter_py.add_mime_type("text/x-python")
        filechooserdialog.add_filter(filter_py)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        filechooserdialog.add_filter(filter_any)
        
        response = filechooserdialog.run()
        if response == Gtk.ResponseType.OK:
            file = filechooserdialog.get_filename()
            self.create_sourceview(file)
        filechooserdialog.destroy()
        
    def on_flash_clicked(self, widget, data):
        print("Flash")
        

class BitApp(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="org.zanderbrown.bit",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                         **kwargs)
        self.window = None

        self.add_main_option("test", ord("t"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Command line test", None)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = BitWin(application=self, title="Bit")
            self.window.connect("delete-event", Gtk.main_quit)

        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains("test"):
            # This is printed on the main instance
            print("Test argument recieved")

        self.activate()
        return 0

    def on_about(self, action, param):
        aboutdialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        aboutdialog.set_name("Bit")
        aboutdialog.set_version("1.0")
        aboutdialog.set_comments("Python Editor for Micro::Bit")
        aboutdialog.set_authors(["Alexander Brown"])
        aboutdialog.set_copyright("Copyright © 2016 Alexander Brown")
        aboutdialog.set_logo_icon_name("applications-development")
        aboutdialog.run()
        aboutdialog.destroy()

    def on_quit(self, action, param):
        self.quit()



def run():
    app = BitApp()
    app.run(sys.argv)

if __name__ == "__main__":
    run()

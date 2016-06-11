#!/usr/bin/python3

import sys, gi, logging, os
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import GLib, Gio, Gtk, GObject, Pango
from gi.repository import GtkSource

#from mu.logic import Editor, LOG_FILE, LOG_DIR
from bit.logic import *

logger = logging.getLogger(__name__)

def setup_logging():
    """
    Configure logging.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_format = '%(name)s(%(funcName)s) %(levelname)s: %(message)s'
    #logging.basicConfig(filename=LOG_FILE, filemode='w', format=log_format,
    #                    level=logging.DEBUG)
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    print('Logging to {}'.format(LOG_FILE))



# App Menu
MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">app.zoom-in</attribute>
        <attribute name="label" translatable="yes">_Increase Text</attribute>
      </item>
      <item>
        <attribute name="action">app.zoom-out</attribute>
        <attribute name="label" translatable="yes">_Decrease Text</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
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
        logger.info("Make TabLabel")
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(5) # spacing: [icon|5px|label|5px|close]  

        # icon
        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, False, False, 0)
        
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

class BitFile(Gtk.Box):
    def __init__(self, file):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        logger.debug("Make Tab")

        self.scroll = Gtk.ScrolledWindow()

        lm = GtkSource.LanguageManager.new()
        language = lm.guess_language(file, None)

        logger.debug("Make Buffer")
        buffer = GtkSource.Buffer()

        if language:
            buffer.set_highlight_syntax(True)
            buffer.set_language(language)
        else:
            logger.warning('No language found for file "%s"' % file)
            buffer.set_highlight_syntax(False)

        logger.debug("Make File")
        source_file = GtkSource.File()
        source_file.set_location(Gio.File.new_for_path(file))
        source_file_loader = GtkSource.FileLoader.new(buffer, source_file)
        source_file_loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

        logger.debug("Make View")
        self.sourceview = GtkSource.View.new_with_buffer(buffer)
        self.sourceview.set_auto_indent(True)
        self.sourceview.set_indent_on_tab(True)
        self.sourceview.set_show_line_numbers(True)
        self.sourceview.set_highlight_current_line(True)
        self.sourceview.set_smart_home_end(True)

        #self.sourceview.undo()
        self.scroll.add(self.sourceview)
        self.pack_start(self.scroll, True, True, 0)

        self.actions = Gtk.ActionBar()

        btn_undo = Gtk.Button('Undo')
        btn_undo.connect("clicked", self.undo, self)

        btn_redo = Gtk.Button('Redo')
        btn_redo.connect("clicked", self.redo, self)

        self.actions.pack_start(btn_undo)
        self.actions.pack_start(btn_redo)
        self.pack_end(self.actions, False, False, 0)

        self.bit_file = source_file
        self.bit_buffer = buffer
        self.show_all()
        print(self.get_file())

    def get_file(self):
        return self.bit_file.get_location().get_path()

    def undo(self, widget, data):
        if self.bit_buffer.can_undo():
            self.bit_buffer.undo()

    def redo(self, widget, data):
        if self.bit_buffer.can_redo():
            self.bit_buffer.redo()

    def zoom(self, level):
        print("monospace " + str(level))
        self.sourceview.modify_font(Pango.FontDescription("monospace " + str(level)))

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

        btn_open.set_tooltip_text("Open File")
        btn_save.set_tooltip_text("Save File")
        btn_new.set_tooltip_text("New File")
        btn_flash.set_tooltip_text("Flash Micro:Bit")

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

        #toolbar = Gtk.Toolbar()
        #toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        #toolbar.insert(toolbutton, 0)

        #self.box.add(toolbar)

        self.notebook = Gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_scrollable (True)
        Gtk.Notebook.popup_enable (self.notebook)
        self.notebook.connect("switch-page", self.on_page_changed, None)

        self.zoom = 12

        self.create_sourceview()
        self.box.pack_start(self.notebook, True, True, 0)
        
        self.add(self.box)
        self.set_default_size(800,600)
        self.set_titlebar(self.header)
        self.set_icon_name("applications-development")
        self.show_all()

    def on_page_changed(self, happy, page, page_num, data):
        self.header.set_title(self.notebook.get_tab_label(page).get_text())
        logger.debug("Switched to tab with contents: " + page.bit_buffer.get_text(page.bit_buffer.get_start_iter(), page.bit_buffer.get_end_iter(), True))

    def create_sourceview(self, file = "template.py"):
        scrolledwindow = BitFile(file)
        scrolledwindow.zoom(self.zoom)
        filename = file.split('/')
        filename = filename[len(filename)-1]
        tab_label = TabLabel(filename)
        logger.debug("TabLable Made")
        self.notebook.append_page(scrolledwindow, tab_label)
        self.notebook.set_tab_reorderable(scrolledwindow, True)
        tab_label.connect("close-clicked", self.on_close_clicked, self.notebook, scrolledwindow)
        self.notebook.set_current_page(self.notebook.page_num(scrolledwindow))

    def on_close_clicked(self, widget2, sender, widget):
        logger.debug("Close Tab Requested")
        pagenum = self.notebook.page_num(widget)
        # Should check if saved
        self.notebook.remove_page(pagenum)

    def on_new_clicked(self, widget, data):
        logger.debug("New Tab Requested")
        self.create_sourceview()
        self.show_all()

    def on_save_clicked(self, widget, data):
        logger.debug("Save Requested")
        source_file_saver = GtkSource.FileSaver.new(self.notebook.get_nth_page(self.notebook.get_current_page()).bit_buffer, self.notebook.get_nth_page(self.notebook.get_current_page()).bit_file)
        self.notebook.get_tab_label(self.notebook.get_nth_page(self.notebook.get_current_page())).start_working()
        self.notebook.get_nth_page(self.notebook.get_current_page()).bit_buffer.set_modified(False)
        source_file_saver.save_async(GLib.PRIORITY_DEFAULT, None, None, None, self.done_io, self.notebook.get_nth_page(self.notebook.get_current_page()))
        
    def done_io(self, task, result, data):
        logger.debug("File IO Complete")
        self.notebook.get_tab_label(data).stop_working()
        
    def on_open_clicked(self, widget, data):
        logger.debug("Open Requested")
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
        logger.debug("Flash Requested")
        logger.debug(flash(self.notebook.get_nth_page(self.notebook.get_current_page()).get_file()))
        
    def on_close_widow(self):
        logger.debug("Window closing")
        print(self.notebook.get_n_pages())
        for x in range(0, self.notebook.get_n_pages()):
            if (self.notebook.get_nth_page(x).bit_buffer.get_modified()):
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, "Unsaved Changes")
                dialog.format_secondary_text(self.notebook.get_tab_label(self.notebook.get_nth_page(x)).text + " has unsaved changs. Save them now?")
                response = dialog.run()
                if response == Gtk.ResponseType.YES:
                    print("QUESTION dialog closed by clicking YES button")
                elif response == Gtk.ResponseType.NO:
                    print("QUESTION dialog closed by clicking NO button")
                dialog.destroy()

    def zoom_text(self, level):
        self.zoom = level
        for x in range(0, self.notebook.get_n_pages()):
            self.notebook.get_nth_page(x).zoom(level)

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
        self.zoom = 12

        action = Gio.SimpleAction.new("zoom-in", None)
        action.connect("activate", self.on_zoom_in)
        self.add_action(action)

        action = Gio.SimpleAction.new("zoom-out", None)
        action.connect("activate", self.on_zoom_out)
        self.add_action(action)

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
            self.window.zoom_text(self.zoom)
            self.window.connect("delete-event", self.on_quit)

        self.window.present()
        self.window.show()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains("test"):
            # This is printed on the main instance
            print("Test argument recieved")

        self.activate()
        return 0

    def on_zoom_in(self, action, param):
        self.zoom = self.zoom + 3
        self.window.zoom_text(self.zoom)

    def on_zoom_out(self, action, param):
        self.zoom = self.zoom - 3
        self.window.zoom_text(self.zoom)

    def on_about(self, action, param):
        aboutdialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        aboutdialog.set_program_name("Bit")
        aboutdialog.set_name("Bit")
        aboutdialog.set_version("1.2")
        aboutdialog.set_comments("Python Editor for Micro::Bit")
        aboutdialog.set_authors(["Alexander Brown"])
        aboutdialog.set_website("https://github.com/zanderbrown/bit")
        aboutdialog.set_website_label("GitHub Repository")
        aboutdialog.set_copyright("Copyright © 2016 Alexander Brown Takes inspiration from Mu")
        aboutdialog.set_logo_icon_name("applications-development")
        aboutdialog.run()
        aboutdialog.destroy()

    def on_quit(self, action, param):
        self.window.on_close_widow()
        self.quit()

def flash(file, path = None):
    import os
    from bit.contrib import uflash
    logger.debug("Flash" + file)
    # Make a hex
    try:
        # Load File contents
        f = open(file, "r")
        script = f.read()
        # Actually hex it
        python_hex = uflash.hexlify(script.encode('utf-8'))
    except:
        # Opps that didnt work...
        return 3;

    # Add it to MicroPython
    micropython_hex = uflash.embed_hex(uflash._RUNTIME, python_hex)

    # Did they manually specify path?
    if path is None:
        path = uflash.find_microbit()
        if path is None:
            # Cant find it!
            return 2

    # So does it really ecist?
    if path and os.path.exists(path):
        hex_file = os.path.join(path, 'micropython.hex')
        # Save to microbit
        uflash.save_hex(micropython_hex, hex_file)
        # Yay it worked!
        return 1;
    else:
        # Still doesnt exist
        return 2

def run():
    setup_logging()
    print("Started")
    app = BitApp()
    app.run(sys.argv)

if __name__ == "__main__":
    run()

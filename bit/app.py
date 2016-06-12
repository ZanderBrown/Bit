#!/usr/bin/python3

import sys, gi, logging, os
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import GLib, Gio, Gtk, GObject, Pango
from gi.repository import GtkSource
from pkg_resources import resource_string
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
    #print('Logging to {}'.format(LOG_FILE))

class TabLabel(Gtk.Box):
    __gsignals__ = {
        "close-clicked": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
    }
    def __init__(self, label_text):
        logger.info("Make TabLabel")
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(5)

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
        self.get_style_context().add_class("background")

        logger.debug("Make Tab")

        self.scroll = Gtk.ScrolledWindow()

        lm = GtkSource.LanguageManager.new()
        language = lm.guess_language(file, None)

        buffer = GtkSource.Buffer()

        if language:
            buffer.set_highlight_syntax(True)
            buffer.set_language(language)
        else:
            logger.warning('No language found for file "%s"' % file)
            buffer.set_highlight_syntax(False)

        source_file = GtkSource.File()
        source_file.set_location(Gio.File.new_for_path(file))
        source_file_loader = GtkSource.FileLoader.new(buffer, source_file)
        source_file_loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

        self.sourceview = GtkSource.View.new_with_buffer(buffer)
        self.sourceview.set_auto_indent(True)
        self.sourceview.set_indent_on_tab(True)
        self.sourceview.set_show_line_numbers(True)
        self.sourceview.set_highlight_current_line(True)
        self.sourceview.set_smart_home_end(True)

        self.scroll.add(self.sourceview)
        data =  "GtkSourceView {\n" \
        "   font-family: monospace;\n" \
        "}"
        provider = Gtk.CssProvider()
        provider.load_from_data(bytes(data, "ascii"))
        # 600 = GTK_STYLE_PROVIDER_PRIORITY_APPLICATION
        self.sourceview.get_style_context().add_provider(provider, 600)
        self.pack_start(self.scroll, True, True, 0)

        self.actions = Gtk.ActionBar()

        box_unredo = Gtk.Box()
        box_unredo.get_style_context().add_class('linked')

        btn_undo = Gtk.Button('Undo')
        btn_undo.set_tooltip_text('Undo the last edit')
        btn_undo.connect('clicked', self.undo, self)

        btn_redo = Gtk.Button.new_from_icon_name('edit-redo-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        btn_redo.set_tooltip_text('Redo the undone edit')
        btn_redo.connect("clicked", self.redo, self)

        box_unredo.add(btn_undo)
        box_unredo.add(btn_redo)

        self.actions.pack_start(box_unredo)

        btn_info = Gtk.Button.new_from_icon_name('document-properties-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        btn_info.set_tooltip_text('File Information')
        btn_info.connect("clicked", self.info, self)

        self.actions.pack_end(btn_info)

        self.pack_end(self.actions, False, False, 0)

        self.bit_file = source_file
        self.bit_buffer = buffer
        self.show_all()

    def get_file(self):
        return self.bit_file.get_location().get_path()

    def undo(self, widget, data):
        if self.bit_buffer.can_undo():
            self.bit_buffer.undo()

    def redo(self, widget, data):
        if self.bit_buffer.can_redo():
            self.bit_buffer.redo()
            
    def info(self, widget, data):
        win = BitFileInfo(self.bit_file.get_location().query_info("*",0,None), parent=self.get_toplevel())
        win.run()
        win.destroy()

    def start_flashing(self):
        info = Gtk.Box()
        spin = Gtk.Spinner()
        spin.start()
        info.pack_start(spin, False, False, 0)
        info.pack_end(Gtk.Label('Flashing'), False, False, 0)
        info.show_all()
        self.actions.set_center_widget(info)
        self.get_toplevel().btn_flash.set_sensitive(False)

    def done_flashing(self):
        info = Gtk.Box()
        info.add(Gtk.Label('Done'))
        info.show_all()
        self.actions.set_center_widget(info)
        self.get_toplevel().btn_flash.set_sensitive(True)

    def zoom(self, level):
        self.sourceview.modify_font(Pango.FontDescription("monospace " + str(level)))

class BitFileInfo(Gtk.Dialog):
    def __init__(self, file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("File Info")
        header = Gtk.HeaderBar()
        header.show()
        self.set_titlebar(header)
        header.set_title(file.get_name())
        header.set_subtitle('File Info')
        header.set_show_close_button(True)
        builder = Gtk.Builder.new_from_string(resource_string('bit.resources', 'fileinfo.glade').decode('UTF-8', 'replace'), -1)
        self.get_content_area().add(builder.get_object('info'))
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        def humansize(nbytes):
            if nbytes == 0: return '0 B'
            i = 0
            while nbytes >= 1024 and i < len(suffixes)-1:
                nbytes /= 1024.
                i += 1
            f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
            return '%s %s' % (f, suffixes[i])
        
        builder.get_object('size').set_label(str(humansize(file.get_size())))
        builder.get_object('file').set_label(str(file.get_name()))
        builder.get_object('icon').set_from_gicon(file.get_icon(), Gtk.IconSize.DIALOG)

class BitWin(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.set_title("Untitled")
        self.header.set_subtitle("Bit")

        self.btn_open  = Gtk.Button('Open')
        self.btn_save  = Gtk.Button('Save')
        self.btn_new   = Gtk.Button.new_from_icon_name('tab-new-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
        self.btn_flash = Gtk.Button.new_from_icon_name('media-playback-start-symbolic', Gtk.IconSize.SMALL_TOOLBAR)

        self.btn_open.set_tooltip_text("Open File")
        self.btn_save.set_tooltip_text("Save File")
        self.btn_new.set_tooltip_text("New File")
        self.btn_flash.set_tooltip_text("Flash Micro:Bit")

        self.header.pack_start(self.btn_open)
        self.header.pack_start(self.btn_new)
        self.header.pack_end(self.btn_save)
        self.header.pack_end(self.btn_flash)
        
        self.btn_new.connect("clicked", self.on_new_clicked, self)
        self.btn_open.connect("clicked", self.on_open_clicked, self)
        self.btn_save.connect("clicked", self.on_save_clicked, self)
        self.btn_flash.connect("clicked", self.on_flash_clicked, self)

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

    def create_sourceview(self, file = "template.py"):
        scrolledwindow = BitFile(file)
        scrolledwindow.zoom(self.zoom)
        tab_label = TabLabel(scrolledwindow.bit_file.get_location().query_info("*",0,None).get_name())
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
        filechooserdialog = Gtk.FileChooserDialog("Open", self, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.APPLY))

        filter_py = Gtk.FileFilter()
        filter_py.set_name("Python files")
        filter_py.add_mime_type("text/x-python")
        filter_py.add_pattern("*.py")
        filechooserdialog.add_filter(filter_py)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        filechooserdialog.add_filter(filter_any)
        
        response = filechooserdialog.run()
        if response == Gtk.ResponseType.APPLY:
            file = filechooserdialog.get_filename()
            self.create_sourceview(file)
        filechooserdialog.destroy()
        
    def on_flash_clicked(self, widget, data):
        logger.debug("Flash Requested")
        import threading
        t = threading.Thread(target=self.do_flash)        
        t.start()
        
    def do_flash(self):
        self.notebook.get_nth_page(self.notebook.get_current_page()).start_flashing()
        logger.debug(flash(self.notebook.get_nth_page(self.notebook.get_current_page()).get_file()))
        self.notebook.get_nth_page(self.notebook.get_current_page()).done_flashing()
        #messagedialog = Gtk.MessageDialog(message_format="MessageDialog", parent=self)
        #messagedialog.set_property("message-type", Gtk.MessageType.INFO)
        #messagedialog.run()
        #messagedialog.destroy()

    def on_close_widow(self):
        logger.debug("Window closing")
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
        self.dark = False

        action = Gio.SimpleAction.new("zoom-in", None)
        action.connect("activate", self.on_zoom_in)
        self.add_action(action)

        action = Gio.SimpleAction.new("zoom-out", None)
        action.connect("activate", self.on_zoom_out)
        self.add_action(action)

        action = Gio.SimpleAction.new("dark", None)
        action.connect("activate", self.on_dark)
        self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_string(resource_string('bit.resources', 'appmenu.glade').decode('UTF-8', 'replace'), -1)
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

    def on_dark(self, action, param):
        if self.dark:
            Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", False);
            self.dark = False
        else:
            Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True);
            self.dark = True


    def on_about(self, action, param):
        aboutdialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        aboutdialog.set_program_name("Bit")
        aboutdialog.set_name("Bit")
        aboutdialog.set_version("1.2")
        aboutdialog.set_comments("Python Editor for Micro:Bit")
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
    app = BitApp()
    app.run(sys.argv)

if __name__ == "__main__":
    run()

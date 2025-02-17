from gi.repository import Adw, Gtk, GLib


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/gtk/app_row.ui")
class AppRow(Adw.ActionRow):
	__gtype_name__ = "AppRow"
	gtc = Gtk.Template.Child
	image = gtc()
	eol_package_package_status_icon = gtc()
	eol_runtime_status_icon = gtc()
	pinned_status_icon = gtc()
	masked_status_icon = gtc()
	check_button = gtc()

	def idle_stuff(self):
		if self.package.icon_path:
			self.image.add_css_class("icon-dropshadow")
			self.image.set_from_file(self.package.icon_path)

	def gesture_handler(self, *args):
		if self.on_long_press:
			self.on_long_press(self)

	def __init__(self, package, on_long_press=None, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creation
		self.package = package
		self.on_long_press = on_long_press
		self.rclick_gesture = Gtk.GestureClick(button=3)
		self.long_press_gesture = Gtk.GestureLongPress()

		# Apply
		GLib.idle_add(lambda *_: self.set_title(GLib.markup_escape_text(package.info["name"])))
		GLib.idle_add(lambda *_: self.set_subtitle(GLib.markup_escape_text(package.info["id"])))
		GLib.idle_add(lambda *_: self.idle_stuff())
		self.add_controller(self.rclick_gesture)
		self.add_controller(self.long_press_gesture)
		if package.info["id"] == "io.github.flattool.Warehouse":
			self.check_button.set_active = lambda *_: None
			self.check_button.set_sensitive(False)

		# Connections
		self.rclick_gesture.connect("released", self.gesture_handler)
		self.long_press_gesture.connect("pressed", self.gesture_handler)

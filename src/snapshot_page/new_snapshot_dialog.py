from gi.repository import Adw, Gtk, GLib
from src.host_info import HostInfo
from src.gtk.loading_status import LoadingStatus
from src.gtk.app_row import AppRow
from src.snapshot_page.tar_worker import TarWorker
import os, time


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/new_snapshot_dialog.ui")
class NewSnapshotDialog(Adw.Dialog):
	__gtype_name__ = "NewSnapshotDialog"
	gtc = Gtk.Template.Child

	toast_overlay = gtc()
	nav_page = gtc()
	list_cancel_button = gtc()
	search_button = gtc()
	create_button = gtc()
	search_entry = gtc()
	name_entry = gtc()
	listbox = gtc()
	select_all_button = gtc()
	total_selected_label = gtc()
	scrolled_window = gtc()
	no_results = gtc()
	stack = gtc()
	is_open = False

	def row_gesture_handler(self, row):
		row.check_button.set_active(not row.check_button.get_active())

	def row_select_handler(self, row):
		if row.check_button.get_active():
			self.selected_rows.append(row)
		else:
			self.selected_rows.remove(row)

		total = len(self.selected_rows)
		self.total_selected_label.set_label(_("{} Selected").format(total))
		self.total_selected_label.set_visible(total > 0)
		self.valid_checker()

	def generate_list(self, *args):
		for package in HostInfo.flatpaks:
			if "io.github.flattool.Warehouse" in package.info["id"]:
				continue

			if package.is_runtime or not os.path.exists(package.data_path):
				continue

			row = AppRow(package, self.row_gesture_handler)
			row.check_button.set_visible(True)
			row.check_button.connect("toggled", lambda *_, row=row: self.row_select_handler(row))
			row.set_activatable(True)
			row.set_activatable_widget(row.check_button)
			self.listbox.append(row)

	def sort_func(self, row1, row2):
		return row1.package.info["name"].lower() > row2.package.info["name"].lower()

	def filter_func(self, row):
		title = row.get_title().lower()
		subtitle = row.get_subtitle().lower()
		search = self.search_entry.get_text().lower()
		if search in title or search in subtitle:
			self.is_result = True
			return True
		else:
			return False

	def on_close(self, *args):
		self.__class__.is_open = False
		self.search_button.set_active(False)
		for row in self.selected_rows.copy():
			GLib.idle_add(lambda *_, row=row: row.check_button.set_active(False))

	def valid_checker(self):
		text = self.name_entry.get_text().strip()
		something_selected = len(self.selected_rows) > 0
		text_good = len(text) > 0 and not ("/" in text or "\0" in text)
		self.create_button.set_sensitive(something_selected and text_good)
		if text_good:
			self.name_entry.remove_css_class("error")
		else:
			self.name_entry.add_css_class("error")

		return something_selected and text_good

	def get_total_fraction(self):
		total = 0
		stopped_workers_amount = 0
		for worker in self.workers:
			total += worker.fraction
			if worker.stop:
				stopped_workers_amount += 1

			if stopped_workers_amount == len(self.workers):
				self.loading_status.progress_bar.set_fraction(1)
				self.loading_status.progress_label.set_label(f"{len(self.workers)} / {len(self.workers)}")
				self.workers.clear()
				if self.on_done:
					self.on_done()

				return False

		self.loading_status.progress_label.set_label(f"{stopped_workers_amount + 1} / {len(self.workers)}")
		self.loading_status.progress_bar.set_fraction(total / len(self.workers))
		return True

	def on_create(self, button):
		self.loading_status.title_label.set_label(_("Creating Snapshot"))
		self.loading_status.progress_bar.set_fraction(0.0)
		self.snapshot_page.status_stack.set_visible_child(self.snapshot_page.snapshotting_view)
		self.workers.clear()
		for row in self.selected_rows:
			if "io.github.flattool.Warehouse" in row.package.info["id"]:
				continue

			package = row.package
			worker = TarWorker(
				existing_path=package.data_path,
				new_path=f"{HostInfo.snapshots_path}{package.info['id']}",
				file_name=f"{int(time.time())}_{package.info["version"]}",
				name=self.name_entry.get_text(),
				toast_overlay=self.snapshot_page.toast_overlay,
			)
			self.workers.append(worker)
			worker.compress()

		self.loading_status.progress_label.set_visible(len(self.workers) > 1)
		GLib.timeout_add(200, self.get_total_fraction)
		self.close()

	def on_invalidate(self, search_entry):
		self.is_result = False
		self.listbox.invalidate_filter()
		if self.is_result:
			self.stack.set_visible_child(self.scrolled_window)
		else:
			self.stack.set_visible_child(self.no_results)

	def on_select_all(self, button):
		i = 0
		while row := self.listbox.get_row_at_index(i):
			i += 1
			row.check_button.set_active(True)

	def set_packages(self):
		for package in self.packages:
			row = AppRow(package)
			row.set_activatable(False)
			self.selected_rows.append(row)
			self.listbox.append(row)

	def enter_handler(self, *args):
		if self.create_button.get_sensitive():
			self.create_button.activate()

	def present(self, *args, **kwargs):
		if self.__class__.is_open:
			return

		super().present(*args, **kwargs)
		self.__class__.is_open = True
		if not self.search_button.get_visible():
			self.name_entry.grab_focus()

	def __init__(self, snapshot_page, loading_status, on_done=None, packages=None, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creations
		self.snapshot_page = snapshot_page
		self.loading_status = loading_status
		self.on_done = on_done
		self.is_result = False
		self.rows = []
		self.selected_rows = []
		self.workers = []
		self.packages = packages

		# Connections
		self.connect("closed", self.on_close)
		self.create_button.connect("clicked", self.on_create)
		self.search_entry.connect("search-changed", self.on_invalidate)
		self.list_cancel_button.connect("clicked", lambda *_: self.close())
		self.name_entry.connect("changed", lambda *_: self.valid_checker())
		self.name_entry.connect("entry-activated", self.enter_handler)
		self.select_all_button.connect("clicked", self.on_select_all)

		# Apply
		self.listbox.set_sort_func(self.sort_func)
		self.listbox.set_filter_func(self.filter_func)
		self.name_entry.set_title(_("Name these Snapshots"))
		if not packages is None:
			self.search_entry.set_editable(False)
			self.search_button.set_visible(False)
			self.nav_page.set_title(_("New Snapshot"))
			self.set_packages()
			self.no_results.set_visible(False)
			if len(packages) == 1:
				self.name_entry.set_title(_("Name this Snapshot"))
		else:
			self.nav_page.set_title(_("New Snapshots"))
			self.generate_list()

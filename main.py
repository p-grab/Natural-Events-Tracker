import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QCheckBox,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from natural_events_tracker import EventTracker


"""
Const variables:
limits for days user can get data
"""
MIN_DAYS = 1
MAX_DAYS = 200


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Natural events")
        self.setGeometry(400, 200, 400, 200)

        """
        Adds title and description under it labels
        """
        title_label = QLabel("Natural events", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 20px;")

        description_label = QLabel(
            "Choose from how many days data should be found:", self
        )

        """
        Adds slider with limits, features, and changing action
        Also adds labels for min and max days
        """
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(MIN_DAYS)
        self.slider.setMaximum(MAX_DAYS)
        self.slider.setValue(int((MAX_DAYS - MIN_DAYS) / 2))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.update_value)

        min_label = QLabel("Min: " + str(MIN_DAYS), self)
        max_label = QLabel("Max: " + str(MAX_DAYS), self)
        max_label.setAlignment(Qt.AlignRight)

        """
        Adds button for request data for specific number of days
        """
        self.events_button = QPushButton(
            ("Find for " + str(self.slider.value()) + " days"), self
        )
        self.events_button.clicked.connect(self.run_events_button)

        """
        Adds parameter Checkboxes for each category of Event
         and label with text before it
        """
        self.choose_params = QLabel("Choose which events are presented:", self)
        self.choose_params.setVisible(False)

        self.params = [
            QCheckBox("1", self),
            QCheckBox("2", self),
            QCheckBox("3", self),
            QCheckBox("4", self),
            QCheckBox("5", self),
            QCheckBox("6", self),
            QCheckBox("7", self),
            QCheckBox("8", self),
        ]
        for param in self.params:
            param.setVisible(False)

        """
        Adds buttons to create image
        """
        self.button_see_plot = QPushButton("See plot", self)
        self.button_see_plot.clicked.connect(self.run_function_plot)
        self.button_see_plot.setDisabled(True)

        self.button_see_png = QPushButton("See png", self)
        self.button_see_png.clicked.connect(self.run_function_png)
        self.button_see_png.setDisabled(True)

        self.save_png_box = QCheckBox("Save output to .png", self)
        self.intensity_box = QCheckBox("Intensify close points", self)

        """
        Adds 2 horizontal layouts for parameter checkboxes
        """
        hbox_params1 = QHBoxLayout()
        hbox_params2 = QHBoxLayout()
        for i in range(len(self.params)):
            if i < int(len(self.params) / 2):
                hbox_params1.addWidget(self.params[i])
            else:
                hbox_params2.addWidget(self.params[i])

        """
        Adds horizontal layout for text labels
        """
        hbox2 = QHBoxLayout()
        hbox2.addWidget(min_label)
        hbox2.addWidget(max_label)
        """
        Adds horizontals layout for creating image and its' options
        """
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.button_see_plot)
        hbox_buttons.addWidget(self.button_see_png)

        hbox_run_options = QHBoxLayout()
        hbox_run_options.addWidget(self.save_png_box)
        hbox_run_options.addWidget(self.intensity_box)

        """
        Set all Widgets in one vertical layout
        """
        vbox = QVBoxLayout()
        vbox.addWidget(title_label)
        vbox.addWidget(description_label)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.events_button)
        vbox.addWidget(self.choose_params)
        vbox.addLayout(hbox_params1)
        vbox.addLayout(hbox_params2)
        vbox.addLayout(hbox_buttons)
        vbox.addLayout(hbox_run_options)

        self.setLayout(vbox)

        self.show()

    def run_function_plot(self):
        """
        Method which calls creating map for specific chechboxes
        after pushing plot button If file was save it also shows
        information about it
        """
        checked_params = [param.isChecked() for param in self.params]
        coords = self.tracker.get_coords(checked_params, self.intensity_box.isChecked())
        self.tracker.create_map(coords, False, self.save_png_box.isChecked())
        if self.save_png_box.isChecked():
            QMessageBox.about(None, "Saved!", "Saved file in current folder ")

    def run_function_png(self):
        """
        Method which calls creating map for specific chechboxes after pushing
        png button. If file was save it also shows information about it
        """
        checked_params = [param.isChecked() for param in self.params]
        coords = self.tracker.get_coords(checked_params, self.intensity_box.isChecked())
        self.tracker.create_map(coords, True, self.save_png_box.isChecked())
        if self.save_png_box.isChecked():
            QMessageBox.about(None, "Saved!", "Saved file in current folder ")

    def run_events_button(self):
        """
        Method which update text in the button when push.
        Then creates EventTracker object and create get list of event categories
        Then mark specific checkboxes and makes them visible
        Also activates creating Image button if at least one category is available
        """

        prev_text = self.events_button.text()
        new_text = prev_text.replace("Find", "Found")
        self.events_button.setText(new_text)
        self.tracker = EventTracker((self.slider.value()))
        events_list = list(self.tracker.classified_events.keys())
        for i in range(len(self.params)):
            if i < len(events_list):
                self.params[i].setText(events_list[i])
                self.params[i].setVisible(True)
                self.params[i].setChecked(True)

            else:
                self.params[i].setVisible(False)
                self.params[i].setChecked(False)

        if len(events_list) == 0:
            self.choose_params.setText("No events happened in those days")
            self.button_see_plot.setDisabled(True)
            self.button_see_png.setDisabled(True)
        else:
            self.choose_params.setText("Choose which events are presented:")
            self.choose_params.setVisible(True)
            self.button_see_plot.setDisabled(False)
            self.button_see_png.setDisabled(False)

    def update_value(self):
        """
        Method which update text in the button when changing slider value
        """
        value = self.slider.value()
        self.events_button.setText("Find for " + str(value) + " days")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
